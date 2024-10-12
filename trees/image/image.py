from dataclasses import dataclass
from itertools import product
from functools import cached_property
from contextlib import contextmanager
from collections.abc import Generator
from typing import Tuple, List, Optional, Self, Callable, Any

from pygame import SurfaceType, Color
import pygame.surfarray as surfarray

import numpy as np
from numpy import ndarray
from numpy.typing import ArrayLike

@dataclass
class Image:
    size: Tuple[int, int]
    data_layers: List[ndarray]
    data_render_func: Callable[[Any], Tuple[float, float, float, float]]
    surface: Optional[SurfaceType]

    _cached: Optional[ndarray] = None

    @classmethod
    def blank_image(
        cls,
        render:  Callable[[Any], Tuple[float, float, float, float]],
        size: Tuple[int, int]
    ) -> "Image":
        return cls(
            size=size,
            data_layers=[
                np.zeros(size)
            ],
            data_render_func=render,
            surface=None,
        )

    def link(self, surface: SurfaceType) -> Self:
        self.surface = surface
        return self

    @cached_property
    def positions(self) -> List[Tuple[int, int]]:
        return list(product(range(self.size[0]), range(self.size[1])))

    @property
    def pixels(self) -> ndarray:
        if self._cached is None:
            return self.render()
        else:
            return self._cached
    
    def _render_layers(self) -> ndarray:
        array = np.zeros(
            (*self.size, len(self.data_layers), 4)
        )

        for i, layer in enumerate(self.data_layers):
            for x, y in self.positions:
                array[x, y, i, :] = self.data_render_func(layer[x, y])

        final_array = np.zeros((*self.size, 3), dtype=np.float32)
        for x, y in self.positions:
            pixel_column = array[x, y, :, :3]
            alphas = array[x, y, :, 3]
            float_pixel: ndarray = np.dot(alphas, pixel_column)
            pixel = 255 * float_pixel
            final_array[x, y, :] = pixel.astype(np.int32)

        return final_array
    
    def render(self) -> ndarray:
        rendered_pixels = self._render_layers()

        if self.surface is None:
            self.surface = surfarray.make_surface(rendered_pixels)
        else:
            surfarray.blit_array(self.surface, rendered_pixels)
        
        self._cached = rendered_pixels
        return rendered_pixels

    def _layer_setter(self, idx: int):
        def set(array: ndarray):
            self.data_layers[idx] = array
            self._cached = None
        return set

    @contextmanager
    def edit_layers(self, *layer_indexes) -> Generator[
        List[Tuple[ndarray, Callable[[ndarray], None]]],
        None, None
    ]:
        editing_layers: List[Tuple[ndarray, Callable[[ndarray], None]]] = [
            (self.data_layers[i], self._layer_setter(i))
            for i in layer_indexes
        ]
        try:
            yield editing_layers
        finally:
            self._cached = None

    @staticmethod
    def pixel_to_int(pixel: Tuple[int, int, int]) -> int:
        r, g, b = pixel
        a = 255
        return int(Color(r, g, b, a))