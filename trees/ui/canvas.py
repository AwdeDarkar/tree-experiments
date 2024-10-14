from typing import ClassVar, Tuple

from pygame import Surface, SurfaceType, Color

from numpy import ndarray

from trees.ui.image import Image
from trees.ui.drawables import Frame, FrameStyling, FrameColoring, FrameSpacing

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

    image: Image
    scale: float

    def __init__(self, image: Image):
        Frame.__init__(self, self.CANVAS_STYLE, {})

        self.image = image
        self.scale = 1.0

        self.layout.row()\
          .add_child(self.image)

    @property
    def img_pixels(self) -> ndarray:
        return self.image.pixels

    @property
    def img_surface(self) -> SurfaceType:
        surface = self.image.surface
        if surface is None:
            raise Exception("Image has no surface")
        return surface