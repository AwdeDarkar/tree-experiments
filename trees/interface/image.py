from typing import Tuple, Callable, TypeVar
from numpy import ndarray

T = TypeVar("T")

RenderFunc = Callable[[T], Tuple[float, float, float]]
DataLayer = Tuple[ndarray, RenderFunc]
DataLayerAlpha = Tuple[ndarray, RenderFunc, float]
