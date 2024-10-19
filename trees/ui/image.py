from dataclasses import dataclass
from itertools import product
from functools import cached_property
from contextlib import contextmanager
from collections.abc import Generator
from typing import Tuple, List, Optional, Self, Callable, Any, TypeAlias

from pygame import Surface, SurfaceType, Color
import pygame.surfarray as surfarray
import pygame.transform as transform

import numpy as np
from numpy import ndarray

from trees.ui.drawables import Drawable
from trees.interface import DataLayer, DataLayerAlpha


def nn_resample(img, shape):
    def per_axis(in_sz, out_sz):
        ratio = 0.5 * in_sz / out_sz
        return np.round(np.linspace(ratio - 0.5, in_sz - ratio - 0.5, num=out_sz)).astype(int)

    return img[per_axis(img.shape[0], shape[0])[:, None],
               per_axis(img.shape[1], shape[1])]


class Image(Drawable):
    data_layers: List[DataLayerAlpha]

    _cached: Optional[ndarray] = None

    def __init__(
            self,
            size: Tuple[int, int],
            layers: List[DataLayer] | List[DataLayerAlpha],
        ):
        Drawable.__init__(self, size)
        self.surface = Surface(self.size)
        if not layers:
            raise Exception("Must provide at least one layer to an image")
        elif len(layers[0]) == 2:
            layers_: List[DataLayer] = layers #type: ignore
            self.data_layers = [
                (data, render, 1/len(layers))
                for data, render in layers_
            ]
        elif len(layers[0]) == 3:
            layers__: List[DataLayerAlpha] = layers #type: ignore
            self.data_layers = layers__

    def link(self, surface: SurfaceType) -> Self:
        self.surface = surface
        return self

    @cached_property
    def internal_size(self) -> Tuple[int, int]:
        shape = self.data_layers[0][0].shape
        return (shape[0], shape[1])

    @cached_property
    def positions(self) -> List[Tuple[int, int]]:
        return [idx for idx in np.ndindex(self.internal_size)] #type: ignore

    @property
    def pixels(self) -> ndarray:
        if self._cached is None:
            return self.render()
        else:
            return self._cached
    
    def _scale_array(self, array: ndarray) -> ndarray:
        return nn_resample(array, self.size)
    
    def _render_layers(self) -> ndarray:
        array = np.zeros(
            (*self.internal_size, len(self.data_layers), 4)
        )

        for i, (data, render, alpha) in enumerate(self.data_layers):
            for x, y in self.positions:
                array[x, y, i, :3] = render(data[x, y])
                array[x, y, i, 3] = alpha

        final_array = np.zeros((*self.internal_size, 3), dtype=np.int8)
        for x, y in self.positions:
            pixel_column = array[x, y, :, :3]
            alphas = array[x, y, :, 3]
            float_pixel: ndarray = np.dot(alphas, pixel_column)
            pixel = 255 * float_pixel
            final_array[x, y, :] = pixel.astype(np.int8)

        return final_array
    
    def render(self) -> ndarray:
        if self._cached is None:
            print("re-rendering")
            rendered_pixels = self._scale_array(
                self._render_layers()
            )
            self._cached = rendered_pixels

        surfarray.blit_array(self.surface, self._cached)

        return self._cached

    def _layer_setter(self, idx: int):
        def set(array: ndarray):
            _, render, alpha = self.data_layers[idx]
            self.data_layers[idx] = (array, render, alpha)
            self._invalidate()
        return set
    
    def _invalidate(self):
        self._cached = None
        self.changed = True
    
    @property
    def alphas(self) -> Tuple[float, ...]:
        return tuple(
            alpha
            for _, __, alpha in self.data_layers
        )
    
    @alphas.setter
    def alphas(self, alphas: Tuple[float, ...]):
        self.data_layers = [
            (data, render, alphas[i])
            for i, (data, render, _) in enumerate(self.data_layers)
        ]
        self._invalidate()

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
            self._invalidate()

    @staticmethod
    def pixel_to_int(pixel: Tuple[int, int, int]) -> int:
        r, g, b = pixel
        a = 255
        return int(Color(r, g, b, a))