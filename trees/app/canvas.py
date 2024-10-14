from typing import ClassVar, Tuple

from pygame import Surface, SurfaceType, Color

from numpy import ndarray

from trees.image import Image

class Canvas:
    FRAME_COLOR: ClassVar[Color] = \
        Color(53, 56, 57)
    MARGIN: ClassVar[int] = 14

    image: Image
    root_surface: SurfaceType

    pos: Tuple[int, int]
    scale: float

    def __init__(self, image: Image, pos: Tuple[int, int]):
        self.image = image
        self.pos = pos

        self.scale = 1.0
        self.root_surface = Surface(self.size)

    @property
    def size(self) -> Tuple[int, int]:
        return (
            self.image.size[0] + (self.MARGIN * 2),
            self.image.size[1] + (self.MARGIN * 2),
        )

    @property
    def img_pixels(self) -> ndarray:
        return self.image.pixels

    @property
    def img_surface(self) -> SurfaceType:
        surface = self.image.surface
        if surface is None:
            raise Exception("Image has no surface")
        return surface
    
    def draw(self, surface: SurfaceType):
        self.root_surface.fill(self.FRAME_COLOR)
        _ = self.img_pixels
        self.root_surface.blit(self.img_surface, (self.MARGIN, self.MARGIN))
        surface.blit(self.root_surface, self.pos)