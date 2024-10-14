from typing import ClassVar, Tuple

import pygame
from pygame import SurfaceType, Color
from pygame.time import Clock
from pygame.event import EventType

from trees.image import Image
from trees.app.canvas import Canvas

def dbg_render(x: float) -> Tuple[float, float, float, float]:
    return (1 - x, x, 1 - x, 1)

class TreesApp:
    WINDOW_SIZE: ClassVar[Tuple[int, int]] = \
        (720, 720)
    BACKGROUND_COLOR: ClassVar[Color] = \
        Color(255, 250, 250)
    FPS_LIMIT: ClassVar[int] = \
        60

    screen: SurfaceType
    clock: Clock
    running: bool
    dbg_canvas: Canvas

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode()
        self.clock = Clock()
        self.running = False

        self.dbg_canvas = Canvas(
            Image.blank_image(dbg_render, (300, 300)),
            (30, 30),
        )

    def run(self):
        self.running = True
        while self.running:
            # Process event queue
            for event in pygame.event.get():
                self.process_event(event)
            
            # Draw frame
            self.draw_current_frame()

            # Update clock
            self.clock.tick(self.FPS_LIMIT)
        self.exit()

    def process_event(self, event: EventType):
        match event.type:
            case pygame.QUIT:
                self.quit()
            case _:
                pass
    
    def draw_current_frame(self):
        self.screen.fill(self.BACKGROUND_COLOR)
        self.dbg_canvas.draw(self.screen)
        pygame.display.flip()
    
    def quit(self):
        self.running = False
    
    def exit(self):
        pygame.quit()
