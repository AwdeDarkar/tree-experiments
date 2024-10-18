from itertools import product
from functools import cached_property, cache
from dataclasses import dataclass

from typing import Literal, TypeVar, Tuple, Generator, List

import numpy as np
from numpy import ndarray, random
from numpy.random import Generator as RandomGenerator
from numpy.typing import NDArray

from scipy.interpolate import RegularGridInterpolator

@dataclass
class NoiseOctave:
    octave: int
    dimensions: int
    top_shape: Tuple[int, ...]
    density: int
    magnitude: float
    generator: RandomGenerator

    @cached_property
    def density_scale_factor(self) -> int:
        return self.density ** self.octave

    @cached_property
    def shape(self) -> Tuple[int, ...]:
        return tuple([
            d * self.density_scale_factor
            for d in self.top_shape
        ])

    def gen_vector(self) -> ndarray:
        vec = self.generator.uniform(
            low=-1.0,
            high=1.0,
            size=self.dimensions,
        )
        return self.magnitude * (vec / np.linalg.norm(vec))

    @cached_property
    def gradient_grid(self) -> ndarray:
        gradient = np.zeros([*self.shape, self.dimensions], dtype=np.float32)
        for idx in product(*[range(d) for d in self.shape]):
            gradient[idx] = self.gen_vector()
        return gradient
    
    @cached_property
    def mesh(self) -> List[ndarray]:
        return np.meshgrid(
            *(
                np.linspace(0, 1, num=self.shape[d])
                for d in range(self.dimensions)
            )
        )

    @cached_property
    def points(self) -> ndarray:
        return np.array(list(product(*(
            np.linspace(0, 1, num=d)
            for d in self.shape
        )))).reshape([*self.shape, self.dimensions])

    def interpolated_gradient(self, points: ndarray) -> ndarray:
        interpolator = RegularGridInterpolator(
            [np.linspace(0, 1, num=d) for d in self.shape],
            self.gradient_grid,
            method="linear",
            bounds_error=True,
        )
        grid = interpolator(points)
        assert isinstance(grid, ndarray)
        return grid


@dataclass
class PerlinNoiseScreen:
    shape: Tuple[int, ...]
    seed: int
    octaves: int
    magnitude: float
    density: int

    def __hash__(self) -> int:
        return hash((
            self.shape,
            self.seed,
            self.octaves,
            self.magnitude,
            self.density,
        ))

    @cached_property
    def dimensions(self) -> int:
        return len(self.shape)

    @cached_property
    def real_density(self) -> int:
        return self.density ** len(self.shape)

    @cached_property
    def generator(self) -> RandomGenerator:
        return random.default_rng(seed=self.seed)

    @cached_property
    def octave_layers(self) -> List[NoiseOctave]:
        return [
            NoiseOctave(
                octave=octave,
                dimensions=self.dimensions,
                top_shape=self.shape,
                density=self.density,
                magnitude=self.magnitude,
                generator=self.generator,
            )
            for octave in range(self.octaves)
        ]
    
    @cached_property
    def gradient(self) -> ndarray:
        highest_octave = self.octave_layers[-1]
        gradients = np.array([
            layer.interpolated_gradient(highest_octave.points)
            for layer in self.octave_layers[:-1]
        ] + [highest_octave.gradient_grid])
        return gradients.sum(axis=0)
    
    @cache
    def stencil(self, k: int) -> List[Tuple[Tuple[int, ...], ndarray]]:
        """
        Stencil of displacement vectors from all corners of the unit n-hypercube with side-length `k`
        """
        base_cube = np.array(list(product(
            *(np.linspace(0, 1, num=k) for _ in range(self.dimensions))
        ))).reshape([k for _ in range(self.dimensions)] + [self.dimensions])
        stencil: List[Tuple[Tuple[int, ...], ndarray]] = []

        for idx in product([1, -1], repeat=self.dimensions):
            cube = base_cube[tuple([
                slice(None, None, unit)
                for unit in idx
            ] + [slice(None, None, None)])].copy()
            for i, unit in enumerate(idx):
                cube[..., i] *= unit

            stencil.append((
                tuple([1 if unit < 0 else 0 for unit in idx]),
                cube,
            ))

        return stencil

    def render_noise(self, shape: Tuple[int, ...]) -> ndarray:
        assert len(shape) == self.dimensions
        raise NotImplementedError