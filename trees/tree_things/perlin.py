import math
from itertools import product
from functools import cached_property, cache
from dataclasses import dataclass

from typing import Literal, Callable, Tuple, ClassVar, List

import numpy as np
from numpy import ndarray, random
from numpy.random import Generator as RandomGenerator
from numpy.typing import NDArray

from scipy.interpolate import RegularGridInterpolator
from scipy.integrate import simpson

from trees.interface import RenderFunc

def integrate_kernel(grad_window: ndarray, value: float):
    wsize = grad_window.shape[0]
    grid = np.zeros([
        wsize for _ in range(len(grad_window.shape) - 1)
    ])
    grid[tuple([0 for _ in range(len(grid.shape))])] = value

    for _index in np.ndindex(grid.shape):
        assert isinstance(_index, tuple)
        index: Tuple[int, ...] = _index # type: ignore

        for i, b in enumerate(index):
            if b > 0:
                #import pdb; pdb.set_trace()
                grid[index] += grid[tuple([
                    0 if i == j else d
                    for j, d in enumerate(index)
                ])] + simpson(grad_window[tuple([
                    slice(None, d) if i == j else slice(d, d+1)
                    for j, d in enumerate(index)
                ] + [i])])[0]

    return grid


def kernel_method(gradient: ndarray, wsize=3):
    grid = np.zeros(gradient.shape[:-1])

    ex_grid = np.tile(grid, [2 for _ in grid.shape])
    ex_grad = np.tile(gradient, [2 for _ in grid.shape] + [1])
    #print(grid.shape)

    for _index in np.ndindex(grid.shape):
        assert isinstance(_index, tuple)
        index: Tuple[int, ...] = _index # type: ignore

        window = [
            slice(d, d + wsize, None)
            for d in index
        ]
        ex_grid[tuple(window)] += integrate_kernel(
            ex_grad[tuple(window + [slice(None, None, None)])],
            grid[index],
        ) / (wsize ** len(grid.shape))
    
    grid = ex_grid[tuple([
        slice(None, d, None)
        for d in grid.shape
    ])]

    for i, b in enumerate(grid.shape):
        #import pdb; pdb.set_trace()
        grid[tuple([
            slice(None, wsize, None) if i == j else slice(None, None, None)
            for j, d in enumerate(grid.shape)
        ])] += ex_grid[tuple([
            slice(d, d + wsize, None) if i == j else slice(None, d, None)
            for j, d in enumerate(grid.shape)
        ])]
    
    return grid


@dataclass
class NoiseOctave:
    octave: int
    dimensions: int
    top_shape: Tuple[int, ...]
    density: int
    magnitude: float
    variance: float
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
        vec = self.generator.normal(
            loc=0.0,
            scale=self.variance,
            size=self.dimensions,
        )
        return (self.magnitude / (np.sum(vec ** 2))) * vec

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


def _noise_render_function(x: float) -> Tuple[float, float, float]:
    return (x, x, x)

@dataclass
class PerlinNoiseScreen:
    NOISE_RENDER_FUNC: ClassVar[RenderFunc[float]] = _noise_render_function

    shape: Tuple[int, ...]
    seed: int
    octaves: int
    density: int

    variance_func: Callable[[int], float]
    magnitude_func: Callable[[int], float]

    @staticmethod
    def constant(_: int) -> float:
        return 1.0

    @staticmethod
    def linear(n: int) -> float:
        return n / 2.0 + 1.0

    @staticmethod
    def quadratic(n: int) -> float:
        return n**2 / 2.0 + 1.0

    @staticmethod
    def falloff(n: int) -> float:
        return 1.0 / (n ** 2 + 0.5)

    def __hash__(self) -> int:
        return hash((
            self.shape,
            self.seed,
            self.octaves,
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
                magnitude=self.magnitude_func(octave),
                variance=self.variance_func(octave),
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
        stencil: List[Tuple[Tuple[int, ...], ndarray]] = []

        base_cube = np.array(list(product(
            *(np.linspace(0, 1, num=k) for _ in range(self.dimensions))
        ))).reshape([k for _ in range(self.dimensions)] + [self.dimensions])

        for idx in product([1, -1], repeat=self.dimensions):
            cube = base_cube[tuple([
                slice(None, None, unit)
                for unit in idx
            ] + [slice(None, None, None)])].copy()
            for i, unit in enumerate(idx):
                cube[..., i] *= unit

            pos = tuple([1 if unit < 0 else 0 for unit in idx]) 
            cube[pos] /=  ((np.linalg.norm(cube[pos]) + 0.05) ** 2)
            stencil.append((
                pos,
                cube,
            ))

        return stencil
    
    @cached_property
    def scalar_field(self) -> ndarray:
        field = kernel_method(self.gradient, wsize=3)
        delta = field.max() - field.min()
        return (field - field.min()) / delta
    
    @cached_property
    def fft(self) -> ndarray:
        return np.fft.fft2(self.scalar_field)
    
    @cached_property
    def freqs(self) -> Tuple[ndarray, ndarray]:
        normed = np.abs(self.fft)
        return (
            np.mean(normed, axis=0),
            np.mean(normed, axis=1)
        )
    
    @cache
    def render_noise(self, size: int, normalize: bool = True) -> ndarray:
        final = np.zeros([(d-1)*size for d in self.gradient.shape[:-1]])
        for idx in np.ndindex(*[i-1 for i in self.gradient.shape[:-1]]):
            g = self.gradient[
                tuple([
                    slice(i, i+2, None)
                    for i in idx
                ] + [slice(None, None, None)])
            ]
            val = np.sum([
                np.dot(
                    cube,
                    g[idx]
                )
                for idx, cube in self.stencil(size)
            ], axis=0)
            final[
                tuple([
                    slice((size*i), (size*i)+size, None)
                    for i in idx
                ])
            ] = val[::-1, ::-1]
        if normalize:
            r = final.max() - final.min()
            return (final - final.min()) / r
        return final
