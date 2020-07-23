import pygame
from perlin_map_factory import WrappingPerlinMapFactory
import random

BLACK   = (  0,   0,   0)
GREY    = (100, 100, 100)
WHITE   = (255, 255, 255)
BLUE    = (  0,   0, 255)
L_BLUE  = (  0, 221, 255)
GREEN   = (  0, 220,   0)
D_GREEN = (  0, 125,   0)
RED     = (255,   0,   0)
YELLOW  = (200, 200,   0)

COLOUR_MAP = [
    (0.8,BLACK),(0.5,GREY),
    (0.3,D_GREEN),(0.25,GREEN),(0.15,D_GREEN),(0.08,GREEN),(0.05,YELLOW),
    (0.01,L_BLUE),(-1,BLUE)]

COLOUR_MAP_UNBIAS = [
    (1,BLACK),(0.95,GREY),
    (0.8,D_GREEN),(0.6,GREEN),(0.3,D_GREEN),(0.2,GREEN),(0.1,YELLOW),
    (0.05,L_BLUE),(-1,BLUE)]

SEED = "seed"
PIXEL_WIDTH = 1
MAP_TILES = 5
TILE_WIDTH = 100
TILE_HEIGHT = 100

def get_color(value):
    #print(value)
    for val, color in COLOUR_MAP_UNBIAS:
        if value >= val:
            return color
    return COLOUR_MAP[-1][1]


def main():
    pygame.init()
    pygame.display.set_caption("PyWorldGen")

    # Make this 3x wide to showcase the tessellation of map, to give an
    # illusion of a realistic equirectangular projection
    screen = pygame.display.set_mode((
        PIXEL_WIDTH*MAP_TILES*(TILE_WIDTH)*3, PIXEL_WIDTH*MAP_TILES*(TILE_HEIGHT)))
    pygame.display.set_caption("Map Test")
    screen.fill(BLACK)

    # initialize our factory object
    map_value = WrappingPerlinMapFactory(
        unbias=True, tile=(MAP_TILES,MAP_TILES), octaves=6, seed=SEED)

    # generate and draw each 'pixel' of our map
    for x in range(TILE_WIDTH*MAP_TILES):
        for y in range(TILE_HEIGHT*MAP_TILES):
            # the factory is expecting x,y values in the range [0,1] for
            # each perlin grid square. So we need to scale this
            color = get_color(map_value(x/TILE_WIDTH, y/TILE_HEIGHT))
            pygame.draw.rect(
                screen,
                color,
                (x*PIXEL_WIDTH, y*PIXEL_WIDTH, PIXEL_WIDTH, PIXEL_WIDTH))
            pygame.draw.rect(
                screen,
                color,
                (
                    x*PIXEL_WIDTH+(TILE_WIDTH*MAP_TILES*PIXEL_WIDTH),
                    y*PIXEL_WIDTH,
                    PIXEL_WIDTH,
                    PIXEL_WIDTH))
            pygame.draw.rect(
                screen,
                color,
                (
                    x*PIXEL_WIDTH+2*(TILE_WIDTH*MAP_TILES*PIXEL_WIDTH),
                    y*PIXEL_WIDTH,
                    PIXEL_WIDTH,
                    PIXEL_WIDTH))

    # This will produce white gridlines to show the actual limits of the map
    for x in range(MAP_TILES):
        for y in range(MAP_TILES):
            pygame.draw.rect(
                screen,
                WHITE,
                (
                    x*TILE_WIDTH*PIXEL_WIDTH,
                    y*TILE_HEIGHT*PIXEL_WIDTH,
                    TILE_WIDTH*PIXEL_WIDTH,
                    TILE_HEIGHT*PIXEL_WIDTH),
                1)

    pygame.display.update()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

if __name__=="__main__":
    main()
