from typing import Tuple, List, Sequence, Self

from pygame import Surface, SurfaceType

from trees.interface import (
    IDrawable, IContainer, ILayout,
    ISelectable, ISelectionManager,
)


class Drawable(IDrawable):
    changed: bool

    def __init__(self, size: Tuple[int, int]):
        self.size = size
        self.pos = (0, 0)
        self.hovered = False
        self.changed = True
        self.parent = None
        self.surface = Surface(self.size)
    
    def draw(self, surface: SurfaceType):
        print(f"Drawing {self}")
        if self.changed or True: # TODO figure out how this should work
            self.render()
        surface.blit(self.surface, self.pos)
    
    def _render(self):
        pass
    
    def render(self):
        self._render()
        self.changed = False

    @property
    def global_pos(self) -> Tuple[int, int]:
        if self.parent:
            return (
                self.pos[0] + self.parent.pos[0],
                self.pos[1] + self.parent.pos[1],
            )
        return self.pos

    def on_mouseover(self, mouse_pos: Tuple[int, int]):
        self.hovered = True

    def on_mouseleave(self, mouse_pos: Tuple[int, int]):
        self.hovered = False


class Container(IContainer, Drawable):
    repositioned: bool

    def __init__(self, layout: ILayout, children: List[IDrawable]):
        self.children = children
        self.layout = layout.link(self)
        self.repositioned = False

        Drawable.__init__(self, self.layout.bounding_box)
    
    def resurface(self):
        self.size = self.layout.bounding_box
        self.surface = Surface(self.size)
    
    @property
    def offset(self) -> Tuple[int, int]:
        return (0, 0)

    def position_children(self):
        self.resurface()
        for i, child in enumerate(self.children):
            child.index = i
            pos = self.layout.get_pos(child)
            child.pos = (
                pos[0] + self.offset[0],
                pos[1] + self.offset[1],
            )
        self.repositioned = False
    
    def add_child(self, child: IDrawable) -> Self:
        child.index = len(self.children)
        child.parent = self
        self.children.append(child)

        self.repositioned = True
        self.changed = True
        return self
 
    def _render_children(self):
        for child in self.children:
            child.draw(self.surface)
    
    def render(self):
        self._render()
        if self.repositioned or True:
            self._render_children()
            self.repositioned = False
        self.changed = False


class SelectionContainer(Container, ISelectionManager):
    def __init__(self, layout: ILayout, children: List[IDrawable]):
        Container.__init__(self, layout, children)

        self.current_selected = None
        self.managed = {}

        for child in self.children:
            if isinstance(child, ISelectable):
                self.managed[child.index] = child
    
    def add_child(self, child: IDrawable) -> Self:
        Container.add_child(self, child)
        if isinstance(child, ISelectable):
            self.managed[child.index] = child
        return self
    
    def on_select(self, index):
        self.on_clearselect()
        self.managed[index].on_select()
    
    def on_clearselect(self):
        if self.current_selected:
            self.current_selected.on_deselect()