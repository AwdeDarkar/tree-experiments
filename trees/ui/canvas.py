from types import SimpleNamespace
from functools import cached_property

from typing import ClassVar, Tuple, Callable, List, Optional

from pygame import Surface, SurfaceType, Color, mouse
from pygame import draw as pgdraw
from pygame.font import FontType, SysFont

import numpy as np
from numpy import ndarray

from trees.tree_things import PerlinNoiseScreen

from trees.ui.drawables import Frame, FrameStyling, FrameColoring, FrameSpacing
from trees.ui.image import Image

OverlayLayer = Callable[["Canvas", SurfaceType], SurfaceType]

class Canvas(Frame):
    CANVAS_STYLE: ClassVar[FrameStyling] = FrameStyling(
        base_colors=FrameColoring(
            background_color=Color(53, 56, 57),
            foreground_color=Color(190, 190, 187),
            frame_color=Color(0, 0, 0),
            border_color=Color(0, 100, 0),
            text_bg_color=Color(0, 0, 0),
            text_fg_color=Color(0, 0, 0),
            key_color=Color(0, 180, 0),
        ),
        spacing_standard=FrameSpacing(
            margin=14,
            padding=11,
            border_thickness=3,
            frame_thickness=3,
            font_size_lg=18,
            font_size_md=13,
            font_size_sm=9,
        )
    )

    @classmethod
    def perlin_noise_canvas(
        cls,
        shape: Tuple[int, int],
        size: int,
        render_size: int,
        seed: int,
        octaves: int,
        magnitude: float,
        density: int,
    ) -> "Canvas":
        screen = PerlinNoiseScreen(
            shape,
            seed,
            octaves,
            magnitude,
            density,
        )
        image = Image(
            (size, size),
            [(
                screen.render_noise(render_size, normalize=True),
                PerlinNoiseScreen.NOISE_RENDER_FUNC,
                1.0,
            )],
        )
        canvas = Canvas(
            image,
            [
                GridOverlay(Color(155+100, 50, 50), 3)
            ]
        )
        canvas.misc.screen = screen
        canvas.misc.render_size = render_size
        return canvas

    image: Image
    overlays: List[OverlayLayer]
    misc: SimpleNamespace

    def __init__(self, image: Image, overlays: Optional[List[OverlayLayer]] = None):
        Frame.__init__(self, self.CANVAS_STYLE, {})

        self.image = image
        self.misc = SimpleNamespace()
        self.overlays = overlays or []

        self.layout.row()\
          .add_child(self.image)
    
    def _post_render(self):
        for layer in self.overlays:
            self.image.surface = layer(self, self.image.surface)
        self.surface = self.draw_text(
            self.surface,
            self.current_text,
            (0, 0),
            Color(255, 255, 255)
        )
        self.surface.blit(self.image.surface, self.image.pos)

    @cached_property
    def font(self) -> FontType:
        return SysFont("Cascasia Mono", 14)
    
    def draw_text(self, surface: SurfaceType, text: str, pos: Tuple[int, int], color: Color) -> SurfaceType:
        tsurf = self.font.render(text, True, color)
        surface.blit(tsurf, pos)
        return surface

    @property
    def mouse_pos(self) -> ndarray:
        return np.array(mouse.get_pos())

    @property
    def img_mouse_pos(self) -> ndarray:
        return self.mouse_pos - np.array(self.image.pos)

    @property
    def img_mouse_pixel(self) -> ndarray:
        return (self.img_mouse_pos / self.image.scale).astype(np.int32)

    @cached_property
    def pixel_full(self) -> int:
        return self.image.scale

    @cached_property
    def pixel_half(self) -> int:
        return int(self.image.scale / 2)

    @property
    def current_text(self) -> str:
        pos = self.img_mouse_pixel
        gpos = self.overlays[0].grid_pos #type: ignore
        return f"({pos[0]}, {pos[1]}) [{gpos[0]}, {gpos[1]}]"

    @property
    def img_pixels(self) -> ndarray:
        return self.image.pixels

    @property
    def img_surface(self) -> SurfaceType:
        surface = self.image.surface
        if surface is None:
            raise Exception("Image has no surface")
        return surface


class CanvasOverlay:
    _canvas: Optional[Canvas] = None

    def __call__(self, canvas: Canvas, surface: SurfaceType) -> SurfaceType:
        self._init_with_canvas(canvas)
        return self._render_overlay(surface)
    
    def _init_with_canvas(self, canvas: Canvas):
        self._canvas = canvas
    
    @property
    def canvas(self) -> Canvas:
        if self._canvas is None:
            raise Exception("Canvas not set")
        return self._canvas

    def _render_overlay(self, surface: SurfaceType) -> SurfaceType:
        raise NotImplementedError
    

class GridOverlay(CanvasOverlay):
    color: Color
    thickness: int

    _screen: Optional[PerlinNoiseScreen]

    def __init__(self, color: Color, thickness: int):
        self.color = color
        self.thickness = thickness

        self._screen = None
    
    @property
    def screen(self) -> PerlinNoiseScreen:
        if self._screen is None:
            raise Exception("Screen not set")
        return self._screen

    @property
    def grid_pos(self) -> Tuple[int, int]:
        size = self.grid_shape[0] * 2
        pos = self.canvas.img_mouse_pixel / size
        return (int(pos[0]), int(pos[1]))

    def grid_rect(self, length: int) -> Tuple[int, int, int, int]:
        gx, gy = self.grid_pos
        size = int(length / (self.grid_shape[0] - 1))
        return (
            gx * size + 2, gy * size + 2,
            size - 2, size - 2
        )

    @property
    def grid_shape(self) -> Tuple[int, int]:
        return self.screen.gradient.shape[:-1] #type: ignore
    
    def lines(self, length: int, axis: int, endpoint: bool = False) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        dim = self.grid_shape[axis] - 1
        points = zip(
            np.linspace((0, 0), (0, length), num=(dim + endpoint), endpoint=endpoint),
            np.linspace((length, 0), (length, length), num=(dim + endpoint), endpoint=endpoint),
        )
        x = 0 if axis else 1
        y = 1 if axis else 0
        return [
            (
                (int(start[x]), int(start[y])),
                (int(stop[x]), int(stop[y]))
            )
            for start, stop in points
        ]

    def _init_with_canvas(self, canvas: Canvas):
        CanvasOverlay._init_with_canvas(self, canvas)
        self._screen = self.canvas.misc.screen

    def _render_overlay(self, surface: SurfaceType) -> SurfaceType:
        size = surface.get_size()
        for axis in [0, 1]:
            for i, (start, stop) in enumerate(self.lines(size[axis], axis, True)):
                pgdraw.line(
                    surface,
                    self.color,
                    start,
                    stop,
                    self.thickness
                )
        if self.grid_pos[0] >=0 and self.grid_pos[1] >= 0:
            color = Color(255, 200, 200)
            pgdraw.rect(
                surface,
                color,
                self.grid_rect(size[0]),
                1,
            )
        return surface