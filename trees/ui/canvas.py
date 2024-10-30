import math
from types import SimpleNamespace
from itertools import product
from functools import cached_property

from typing import ClassVar, Tuple, Callable, List, Optional, Dict

from pygame import Surface, SurfaceType, Color, mouse, transform
from pygame import draw as pgdraw
from pygame import math as pgmath
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
                screen.render_noise(render_size, normalize=True).T,
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
        self.surface.blit(
            self.image.surface,
            self.image.pos
        )

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
    
    @property
    def grid_pixel(self) -> Tuple[int, int]:
        size = self.grid_shape[0] * 2
        pos = self.canvas.img_mouse_pixel
        return (int(pos[0]) % size, int(pos[1]) % size)
    
    def scale_grid(self, length: int, gval: int) -> int:
        return int(length / (self.grid_shape[0] - 1)) * gval

    def grid_rect(self, length: int) -> Tuple[int, int, int, int]:
        gx, gy = self.grid_pos
        size = self.scale_grid(length, 1)
        return (
            gx * size + 2, gy * size + 2,
            size - 2, size - 2
        )

    @property
    def grid_shape(self) -> Tuple[int, int]:
        return self.screen.gradient.shape[:-1] #type: ignore
    
    def draw_arrow(
            self,
            surface: SurfaceType,
            pos: Tuple[int, int],
            term: Tuple[int, int],
            color: Color,
            project: Optional[Tuple[int, int]] = None,
        ):
        vec = pgmath.Vector2(term[0] - pos[0], term[1] - pos[1])
        if project:
            avec = pgmath.Vector2(pos[0] - project[0], pos[1] - project[1])
            pvec = avec.project(vec)
            pgdraw.line(
                surface,
                Color(255, 0, 190),
                pos,
                (pvec[0] + pos[0], pvec[1] + pos[1]),
                width=5
            )

        pgdraw.line(
            surface,
            color,
            pos,
            term,
            width=3
        )

        alength = self.canvas.pixel_full
        rt0 = vec.rotate(45)
        rt0.scale_to_length(alength)
        rt1 = vec.rotate(-45)
        rt1.scale_to_length(alength)
        vec.scale_to_length(alength * 1.3)

        p0 = (
            int(term[0] + rt0[0] - vec[0]),
            int(term[1] + rt0[1] - vec[1]),
        )
        p1 = (
            int(term[0] + rt1[0] - vec[0]),
            int(term[1] + rt1[1] - vec[1]),
        )

        pgdraw.line(
            surface,
            color,
            term,
            p0,
            width=2,
        )
        pgdraw.line(
            surface,
            color,
            term,
            p1,
            width=2,
        )
    
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
            for start, stop in self.lines(size[axis], axis, True):
                pgdraw.line(
                    surface,
                    self.color,
                    start,
                    stop,
                    self.thickness
                )

        corners: Dict[Tuple[int, int], Tuple[int, int]] = {}
        gleft, gtop = self.grid_pos
        for pos in np.ndindex(self.screen.gradient.shape[:-1]):
            vec = self.screen.gradient[pos] * self.canvas.pixel_half * self.canvas.misc.render_size
            gpos = (
                self.scale_grid(size[0], pos[0]),
                self.scale_grid(size[1], pos[1])
            )
            gtar = (
                int(gpos[0] + vec[1]),
                int(gpos[1] + vec[0]),
            )

            proj = None
            proj_x = None
            proj_y = None

            cx = pos[0] - gleft
            cy = pos[1] - gtop

            if cx == 0 or cx == 1:
                proj_y = self.grid_pixel[1] * self.canvas.pixel_full
            if cy == 0 or cy == 1:
                proj_x = self.grid_pixel[0] * self.canvas.pixel_full

            if proj_x and proj_y:
                proj = (proj_y, proj_x)
                corners[(cx, cy)] = vec
                color = Color(100*cx, 100*cy, 255 - (80*cx + 80*cy))
            else:
                color = Color(170, 170, 190)

            self.draw_arrow(
                surface,
                gpos, gtar,
                color,
                project=proj,
            )

        if gleft >= 0 and gtop >= 0:
            color = Color(255, 200, 200)
            rect = self.grid_rect(size[0])
            pgdraw.rect(
                surface,
                color,
                rect,
                1,
            )

            col = Color(0, 255, 140)
            pgdraw.line(
                surface,
                col,
                (rect[0], rect[1]),
                (rect[0], rect[1] + self.canvas.pixel_full * self.grid_pixel[1]),
                1,
            )
            pgdraw.line(
                surface,
                col,
                (rect[0], rect[1]),
                (rect[0] + self.canvas.pixel_full * self.grid_pixel[0], rect[1]),
                1,
            )
            self.canvas.draw_text(
                surface,
                str(self.grid_pixel[1]),
                (
                    rect[0] - self.canvas.pixel_half * 3,
                    rect[1] + self.canvas.pixel_full * self.grid_pixel[1],
                ),
                col,
            )
            self.canvas.draw_text(
                surface,
                str(self.grid_pixel[0]),
                (
                    rect[0] + self.canvas.pixel_full * self.grid_pixel[0],
                    rect[1] - self.canvas.pixel_half * 3,
                ),
                col,
            )

            dotsum = 0
            for (x, y), grid in self.screen.stencil(self.canvas.misc.render_size):
                offv = (
                    grid[self.grid_pixel] * self.canvas.pixel_full * self.canvas.misc.render_size
                ).astype(np.int16)
                """
                offv = (
                    grid[self.grid_pixel] * self.canvas.pixel_full * self.canvas.misc.render_size /
                    ((np.linalg.norm(grid[self.grid_pixel]) + 0.05) ** 2)
                ).astype(np.int16)
                """
                """
                offv = (
                    grid[self.grid_pixel] * self.canvas.pixel_full * self.canvas.misc.render_size *
                    (math.sqrt(2) - np.linalg.norm(grid[self.grid_pixel]))
                ).astype(np.int16)
                """

                rx = rect[0] + x * rect[2]
                ry = rect[1] + y * rect[3]
                try:
                    dot = np.dot(offv, corners[(x, y)])
                    dotsum += dot
                    self.draw_arrow(
                        surface,
                        (
                            rx,
                            ry,
                        ),
                        (
                            rx + offv[0],
                            ry + offv[1]
                        ),
                        col,
                    )
                    self.draw_arrow(
                        surface,
                        (
                            rx + offv[0],
                            ry + offv[1]
                        ),
                        (
                            rx + offv[0] + corners[(x, y)][1],
                            ry + offv[1] + corners[(x, y)][0]
                        ),
                        Color(130, 190, 140),
                    )
                    self.canvas.draw_text(
                        surface,
                        str(int(dot)),
                        (
                            rx + offv[0] + corners[(x, y)][1],
                            ry + offv[1] + corners[(x, y)][0]
                        ),
                        Color(50, 100, 70),
                    )
                except (ValueError, KeyError):
                    pass

        try:
            nval = self.canvas.image.data_layers[0][0][
                self.canvas.img_mouse_pixel[0],
                self.canvas.img_mouse_pixel[1]
            ]
            self.canvas.draw_text(
                surface,
                f"{int(dotsum)}; {nval:0.3f}",
                (
                    self.canvas.img_mouse_pixel[0] * self.canvas.pixel_full,
                    (self.canvas.img_mouse_pixel[1] + 3) * self.canvas.pixel_full,
                ),
                Color(0, 0, 0),
            )
        except IndexError:
            pass
        
        return surface