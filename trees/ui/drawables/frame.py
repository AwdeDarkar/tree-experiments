from dataclasses import dataclass

from typing import Optional, Self, Tuple, List, Dict

from pygame import Surface, draw, Rect

from trees.interface import ILayout, IContainer, IDrawable
from trees.ui.drawables.base import SelectionContainer
from trees.utils import FrameSpacing, FrameStyling, LayoutStructure


class FrameLayout(ILayout):
    container: Optional["Frame"] = None
    lookup_paths: Dict[int, List[int]]
    tree: Optional["LayoutTree"] = None

    def __init__(self, **kwargs):
        self.lookup_paths = {}

    @property
    def spacing(self) -> FrameSpacing:
        if self.container is None:
            raise Exception("FrameLayout must be linked to use")
        return self.container.style.spacing

    @property
    def bounding_box(self) -> Tuple[int, int]:
        if self.tree is None:
            return (0, 0)
        return self.tree.bounding_box

    def link(self, container: IContainer) -> Self:
        if not isinstance(container, Frame):
            raise Exception(f"FrameLayout must be linked to a Frame, not '{type(container)}'")
        self.container = container
        return self
    
    def get_pos(self, drawable: IDrawable) -> Tuple[int, int]:
        if self.tree is None:
            raise Exception("Layout has no construction")
        if drawable.index is None:
            raise Exception("Drawables must have an index to be positioned")
        path = self.lookup_paths[drawable.index]

        return self.tree.get_pos(path)
    
    def _set_tree(self, structure: LayoutStructure, **kwargs):
        if self.tree:
            raise Exception("Root tree already set")
        self.tree = LayoutTree(
            self,
            structure,
            0,
            kwargs,
            []
        )
    
    def row(self, **kwargs) -> "LayoutTree":
        self._set_tree(LayoutStructure.ROW, **kwargs)
        assert self.tree
        return self.tree
    
    def col(self, **kwargs) -> "LayoutTree":
        self._set_tree(LayoutStructure.COL, **kwargs)
        assert self.tree
        return self.tree


@dataclass
class LayoutTree:
    parent: "FrameLayout | LayoutTree"
    structure: LayoutStructure
    index: int
    args: dict
    children: Optional[List["IDrawable | LayoutTree"]] = None

    @property
    def root_layout(self) -> FrameLayout:
        if isinstance(self.parent, FrameLayout):
            return self.parent
        return self.parent.root_layout

    @property
    def address(self) -> List[int]:
        if isinstance(self.parent, FrameLayout):
            return []
        return self.parent.address + [self.index]
    
    @property
    def step(self) -> int:
        return self.args.get("spacing", 0)

    @property
    def bounding_box(self) -> Tuple[int, int]:
        if self.children is None:
            return (0, 0)
        match self.structure:
            case LayoutStructure.ROW:
                maxx = 0
                ttly = 0
                for child in self.children:
                    if isinstance(child, IDrawable):
                        size = child.size
                    else:
                        size = child.bounding_box
                    maxx = max(maxx, size[0])
                    ttly += size[1]
                return (maxx, ttly)
            case LayoutStructure.COL:
                maxy = 0
                ttlx = 0
                for child in self.children:
                    if isinstance(child, IDrawable):
                        size = child.size
                    else:
                        size = child.bounding_box
                    ttlx += size[0]
                    maxy = max(maxy, size[1])
                return (ttlx, maxy)
            case LayoutStructure.GRID:
                ttlx = 0
                ttly = 0
                for child in self.children:
                    if isinstance(child, IDrawable):
                        size = child.size
                    else:
                        size = child.bounding_box
                    ttlx += size[0]
                    ttly += size[1]
                return (ttlx, ttly)

    def _get_pos(self, index: int) -> Tuple[int, int]:
        match self.structure:
            case LayoutStructure.ROW:
                return (
                    0,
                    self.step * index,
                )
            case LayoutStructure.COL:
                return (
                    self.step * index,
                    0,
                )
            case LayoutStructure.GRID:
                raise NotImplementedError
    
    def get_pos(self, path: List[int]) -> Tuple[int, int]:
        if self.children is None:
            raise Exception("No children!")

        match len(path):
            case 0:
                raise Exception("Could not find path")
            case 1:
                return self._get_pos(path[0])
            case _:
                child = self.children[path[0]]
                assert isinstance(child, LayoutTree)
                pos = child.get_pos(path[1:])
                off = self._get_pos(path[0])
                return (
                    pos[0] + off[0],
                    pos[1] + off[1],
                )

    def add_child(self, child: IDrawable) -> Self:
        if self.children is None:
            self.children = []

        assert self.root_layout.container
        self.root_layout.container.add_child(child)
        assert child.index is not None
        self.root_layout.lookup_paths[child.index] = self.address + [len(self.children)]
        self.children.append(child)
        return self
    
    def up(self) -> "LayoutTree":
        assert isinstance(self.parent, LayoutTree)
        return self.parent
    
    def row(self, spacing: int) -> "LayoutTree":
        if self.children is None:
            self.children = []

        subtree = LayoutTree(
            self,
            LayoutStructure.ROW,
            len(self.children),
            {
                "spacing": spacing,
            },
            []
        )
        self.children.append(subtree)
        return subtree
    
    def col(self, spacing: int) -> "LayoutTree":
        if self.children is None:
            self.children = []

        subtree = LayoutTree(
            self,
            LayoutStructure.COL,
            len(self.children),
            {
                "spacing": spacing,
            },
            []
        )
        self.children.append(subtree)
        return subtree


class Frame(SelectionContainer):
    style: FrameStyling
    layout: FrameLayout

    def __init__(self, style: FrameStyling, layout_args: dict):
        SelectionContainer.__init__(self, FrameLayout(**layout_args), [])
        self.style = style
    
    def resurface(self):
        size = self.layout.bounding_box
        self.size = (
            size[0] + (self.style.spacing.margin*2),
            size[1] + (self.style.spacing.margin*2),
        )
        self.surface = Surface(self.size)
    
    @property
    def offset(self) -> Tuple[int, int]:
        return (self.style.spacing.margin, self.style.spacing.margin)

    def _render(self):
        self.surface.fill(self.style.colors.background_color)
        draw.rect(
            self.surface,
            self.style.colors.border_color,
            rect=Rect(self.pos[0], self.pos[1], self.size[0] - 1, self.size[1] - 1),
            width=self.style.spacing.border_thickness,
        )
        self.position_children()