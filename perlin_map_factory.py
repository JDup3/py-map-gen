""" An expanded perlin noise factory object which tiles in
a uniform way.
This code is essentially a fork of
https://gist.github.com/eevee/26f547457522755cb1fb8739d0ea89a1
"""
from itertools import product
import math
import random


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def lerp(t, a, b):
    return a + t * (b - a)


class WrappingPerlinMapFactory(object):
    def __init__(self, dimension=2, octaves=1, tile=(), unbias=False, seed=None):
        # we likely want reproducible maps, so lets support seeding within this class
        # The caller will likely do this at the top level, so we default to None
        if seed is not None:
            random.seed(seed)

        # A dimension of 1 will not do a whole lot using this method
        self.dimension = dimension
        self.octaves = octaves
        self.raw_tile = tile
        self.tile = tile + (0,) * dimension
        self.unbias = unbias
        self.gradient = {}
        self.scale_factor = 2 * dimension ** -0.5

        # created preloaded child maps to use for octave values instead of this particalur
        # perlin map object
        self.map_octaves = [
            WrappingPerlinMapFactory(
                dimension, octaves=1, tile=tuple((x*2**(i+1) for x in tile)), unbias=unbias)
            for i in range(octaves-1)]

        # preload with outer gradients
        self.generate_wrapping_gradients()

    def _generate_gradient(self):
        if self.dimension == 1:
            return (random.uniform(-1, 1),)

        random_point = [random.gauss(0, 1) for _ in range(self.dimension)]
        scale = sum(n * n for n in random_point) ** -0.5
        return tuple(coord * scale for coord in random_point)

    def generate_wrapping_gradients(self):
        """ Pre-Configure the outermost points to have matching gradients in order to give a
        spherical-like generation similar to a equirectangular projection.
        The purpose here is to:
        - generate the same gradients for all points along the x axis (see X)
        - generate the same gradients for all points containing a dimension's maximum value (see Y)
        - generate the same gradient for matching coordinates between the x = 0 and
          x = X_MAX planes (see A,B,C)

        For example, in a (4,4) solution, we would expect there to be 5 unique gradients along the
        outer edge of the perlin map (X,A,B,C,Y):

        X  X  X  X  X
        A           A
        B           B
        C           C
        Y  Y  Y  Y  Y
        """
        # initialize the gradient at the origin to reference later
        origin = tuple(0 for _ in range(self.dimension))
        self.gradient[origin] = self._generate_gradient()

        # initialize the gradient at each dimensions' maximum relative to the origin
        origin_max = []
        for i in range(1, self.dimension):
            origin_max.append(origin[:i]+(self.raw_tile[i],)+origin[i+1:])
            self.gradient[origin_max[i-1]] = self._generate_gradient()

        # Now lets assign all gradients along the outer edge of the map...
        # this approach is naive; we are iterating across all possible points.
        # However, computing a set of points to iterate over will likely not change
        # the runtime past O(n**d) for d dimensions
        all_points = product(*(range(self.raw_tile[i]+1) for i in range(self.dimension)))
        for coord in all_points:
            if coord[0] == sum(coord):
                # along the x axis, make the gradients the same
                # only the x axis will attribute to the sum when we are along the x axis
                self.gradient[coord] = self.gradient[origin]
            elif coord[0] == 0:
                coord_copy = (self.raw_tile[0],) + coord[1:]
                # at any point with x = 0, make this the same as the gradient at x = max_dim with
                # the same coords for the other dimensions
                self.gradient[coord] = self._generate_gradient()
                self.gradient[coord_copy] = self.gradient[coord]
            else:
                for i in range(1, self.dimension):
                    if coord[i] == self.raw_tile[i]:
                        # at the dimension's maximum, make the gradient the same as all others
                        # along the same plane
                        self.gradient[coord] = self.gradient[origin_max[i-1]]
                        break
            # in order to keep the maps reproducible and consistent, avoid generating the gradient
            # at the time of calculating the actual noise value
            if coord not in self.gradient:
                self.gradient[coord] = self._generate_gradient()

    def get_plain_noise(self, *point):
        if len(point) != self.dimension:
            raise ValueError("Expected {} values, got {}".format(
                self.dimension, len(point)))

        grid_coords = []
        for coord in point:
            min_coord = math.floor(coord)
            max_coord = min_coord + 1
            grid_coords.append((min_coord, max_coord))

        dots = []
        for grid_point in product(*grid_coords):
            gradient = self.gradient[grid_point]

            dot = 0
            for i in range(self.dimension):
                dot += gradient[i] * (point[i] - grid_point[i])
            dots.append(dot)

        dim = self.dimension
        while len(dots) > 1:
            dim -= 1
            s = smoothstep(point[dim] - grid_coords[dim][0])

            next_dots = []
            while dots:
                next_dots.append(lerp(s, dots.pop(0), dots.pop(0)))

            dots = next_dots

        return dots[0] * self.scale_factor

    def __call__(self, *point):
        # if tiling is provided (which it should, since this is the purpose),
        # we will need to bind the point to 0 and the specified tile maximums
        bound_point = []
        for i, coord in enumerate(point):
            if self.tile[i]:
                coord %= self.tile[i]
            bound_point.append(coord)

        # generate the main noise value for this factory object
        ret = self.get_plain_noise(*bound_point)

        # instead of using a superset of this objects noise, we use
        # child factories whos gradients also wrap
        for i, o_map in enumerate(self.map_octaves):
            # scale the point according to the octave map's index
            # this produces 'fuzzier' noise to add to the value
            new_point = tuple((x*2**(i+1) for x in bound_point))
            # add the weighted noise value according to the index
            ret += o_map.get_plain_noise(*new_point) / 2**(i+1)

        ret /= 2 - 2 ** (1 - self.octaves)

        if self.unbias:
            r = (ret + 1) / 2
            for _ in range(int(self.octaves / 2 + 0.5)):
                r = smoothstep(r)
            ret = r * 2 - 1

        return ret
