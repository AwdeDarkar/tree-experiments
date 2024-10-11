from typing import ClassVar, Tuple

import pygame
from pygame import SurfaceType, Color
from pygame.time import Clock
from pygame.event import EventType


class TreesApp:
    WINDOW_SIZE: ClassVar[Tuple[int, int]] = \
        (1280, 720)
    BACKGROUND_COLOR: ClassVar[Color] = \
        Color(255, 255, 255)
    FPS_LIMIT: ClassVar[int] = \
        60

    screen: SurfaceType
    clock: Clock
    running: bool

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode()
        self.clock = Clock()
        self.running = False

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
        pygame.display.flip()
    
    def quit(self):
        self.running = False
    
    def exit(self):
        pygame.quit()
