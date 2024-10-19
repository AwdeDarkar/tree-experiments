import os
from dataclasses import dataclass

from typing import ClassVar, Tuple

import pygame
from pygame import SurfaceType, Color
from pygame.time import Clock
from pygame.event import EventType

from trees.ui.drawables import Frame, FrameStyling, FrameColoring, FrameSpacing
from trees.ui import Canvas, Image

def dbg_render(x: float) -> Tuple[float, float, float, float]:
    return (1 - x, x, 1 - x, 1)


@dataclass
class RootElements:
    canvas: Canvas


class RootFrame(Frame):
    CANVAS_SIZE: ClassVar[int] = 800

    ROOT_STYLE: ClassVar[FrameStyling] = FrameStyling(
        base_colors=FrameColoring(
            background_color=Color(0, 0, 0),
            foreground_color=Color(190, 190, 187),
            frame_color=Color(0, 0, 0),
            border_color=Color(100, 0, 0),
            text_bg_color=Color(0, 0, 0),
            text_fg_color=Color(0, 0, 0),
            key_color=Color(0, 180, 0),
        ),
        spacing_standard=FrameSpacing(
            margin=4,
            padding=11,
            border_thickness=1,
            frame_thickness=3,
            font_size_lg=18,
            font_size_md=13,
            font_size_sm=9,
        )
    )

    @classmethod
    def make_canvas(cls) -> Canvas:
        return Canvas.perlin_noise_canvas(
            shape=(3, 3),
            size=cls.CANVAS_SIZE,
            render_size=12,
            seed=1337,
            octaves=2,
            magnitude=1.0,
            density=2,
        )

    app: "TreesApp"
    elements: RootElements

    def __init__(self, app: "TreesApp"):
        Frame.__init__(self, self.ROOT_STYLE, {})
        self.app = app
        self.elements = RootElements(
            canvas=self.make_canvas(),
        )
        self.build()
    
    def build(self):
        self.layout.row()\
            .add_child(self.elements.canvas)


class TreesApp:
    WINDOW_SIZE: ClassVar[Tuple[int, int]] = \
        (1000, 1000)
    WINDOW_POS: ClassVar[Tuple[int, int]] = \
        (int((2560 - 1000) / 2), int((1440 / 4)))
    BACKGROUND_COLOR: ClassVar[Color] = \
        Color(255, 250, 250)
    FPS_LIMIT: ClassVar[int] = \
        6

    screen: SurfaceType
    clock: Clock
    running: bool
    root: RootFrame

    def __init__(self):
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{self.WINDOW_POS[0]},{self.WINDOW_POS[1]}"
        pygame.init()

        self.screen = pygame.display.set_mode(
            self.WINDOW_SIZE,
        )
        self.clock = Clock()
        self.running = False
        self.root = RootFrame(self)

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
        self.root.draw(self.screen)
        pygame.display.flip()
    
    def quit(self):
        self.running = False
    
    def exit(self):
        pygame.quit()
