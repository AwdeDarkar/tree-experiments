from typing import Tuple, List, Dict, Type, Optional, Self

from pygame import SurfaceType

from trees.utils import BoxBoundary


class IDrawable:
    surface: SurfaceType
    parent: Optional["IContainer"]
    index: Optional[int]

    pos: Tuple[int, int]
    size: Tuple[int, int]

    hovered: bool

    def draw(self, surface: SurfaceType):
        raise NotImplementedError

    @property
    def global_pos(self) -> Tuple[int, int]:
        raise NotImplementedError

    def on_mouseover(self, mouse_pos: Tuple[int, int]):
        pass

    def on_mouseleave(self, mouse_pos: Tuple[int, int]):
        pass


class ILayout:
    container: Optional["IContainer"] = None

    def link(self, container: "IContainer") -> Self:
        raise NotImplementedError

    def get_pos(self, drawable: IDrawable) -> Tuple[int, int]:
        raise NotImplementedError

    @property
    def bounding_box(self) -> Tuple[int, int]:
        raise NotImplementedError


class IContainer(IDrawable):
    children: List[IDrawable]
    layout: ILayout

    def position_children(self):
        raise NotImplementedError
    
    def add_child(self, child: IDrawable) -> Self:
        raise NotImplementedError


class IResizable(IDrawable):
    resizing: bool
    resize_edge: BoxBoundary

    def resize(self, delta: Tuple[float, float]):
        raise NotImplementedError
    
    def on_resize_delta(self, mouse_move: Tuple[float, float]):
        raise NotImplementedError

    def on_resize_start(self, mouse_pos: Tuple[int, int]):
        raise NotImplementedError

    def on_resize_stop(self, mouse_pos: Tuple[int, int]):
        raise NotImplementedError


class ISelectable(IDrawable):
    manager: "ISelectionManager"
    index: int
    selected: bool

    def on_select(self):
        raise NotImplementedError

    def on_deselect(self):
        raise NotImplementedError


class ISelectionManager:
    current_selected: Optional[ISelectable]
    managed: Dict[int, ISelectable]

    def on_select(self, index: int):
        raise NotImplementedError
    
    def on_clearselect(self):
        raise NotImplementedError


class IDraggable(IDrawable):
    dragging: bool

    def on_drag_delta(self, mouse_move: Tuple[float, float]):
        raise NotImplementedError

    def on_drag_start(self, mouse_pos: Tuple[int, int]):
        raise NotImplementedError

    def on_drag_stop(self, mouse_pos: Tuple[int, int]):
        raise NotImplementedError