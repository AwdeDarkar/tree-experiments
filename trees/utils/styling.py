from functools import cached_property
from dataclasses import dataclass

from typing import Callable, Optional

from pygame import Color

from trees.utils.enums import LayoutForm


def _noop(c: Color):
    return c


@dataclass
class FrameColoring:
    background_color: Color
    foreground_color: Color
    frame_color: Color
    border_color: Color
    text_bg_color: Color
    text_fg_color: Color
    key_color: Color

    hover_transform: Callable[[Color], Color] = _noop
    select_transform: Callable[[Color], Color] = _noop
    flash_up_transform: Callable[[Color], Color] = _noop
    flash_down_transform: Callable[[Color], Color] = _noop
    key_transform: Callable[[Color, float], Color] = lambda c, _: c

    @cached_property
    def hovered(self) -> "FrameColoring":
        t = self.hover_transform
        return FrameColoring(
            background_color=t(self.background_color),
            foreground_color=t(self.foreground_color),
            frame_color=t(self.frame_color),
            border_color=t(self.border_color),
            text_bg_color=t(self.text_bg_color),
            text_fg_color=t(self.text_fg_color),
            key_color=t(self.key_color),
            select_transform=self.select_transform,
            flash_up_transform=self.flash_up_transform,
            flash_down_transform=self.flash_down_transform,
            key_transform=self.key_transform,
        )

    @cached_property
    def selected(self) -> "FrameColoring":
        t = self.select_transform
        return FrameColoring(
            background_color=t(self.background_color),
            foreground_color=t(self.foreground_color),
            frame_color=t(self.frame_color),
            border_color=t(self.border_color),
            text_bg_color=t(self.text_bg_color),
            text_fg_color=t(self.text_fg_color),
            key_color=t(self.key_color),
            hover_transform=self.hover_transform,
            flash_up_transform=self.flash_up_transform,
            flash_down_transform=self.flash_down_transform,
            key_transform=self.key_transform,
        )

    @cached_property
    def flashed_up(self) -> "FrameColoring":
        t = self.flash_up_transform
        return FrameColoring(
            background_color=t(self.background_color),
            foreground_color=t(self.foreground_color),
            frame_color=t(self.frame_color),
            border_color=t(self.border_color),
            text_bg_color=t(self.text_bg_color),
            text_fg_color=t(self.text_fg_color),
            key_color=t(self.key_color),
            hover_transform=self.hover_transform,
            select_transform=self.select_transform,
            flash_down_transform=self.flash_down_transform,
            key_transform=self.key_transform,
        )

    @cached_property
    def flashed_down(self) -> "FrameColoring":
        t = self.flash_down_transform
        return FrameColoring(
            background_color=t(self.background_color),
            foreground_color=t(self.foreground_color),
            frame_color=t(self.frame_color),
            border_color=t(self.border_color),
            text_bg_color=t(self.text_bg_color),
            text_fg_color=t(self.text_fg_color),
            key_color=t(self.key_color),
            hover_transform=self.hover_transform,
            select_transform=self.select_transform,
            flash_up_transform=self.flash_up_transform,
            key_transform=self.key_transform,
        )

    def keyed(self, amount: float) -> "FrameColoring":
        def t(c: Color):
            return self.key_transform(c, amount)
        return FrameColoring(
            background_color=t(self.background_color),
            foreground_color=t(self.foreground_color),
            frame_color=t(self.frame_color),
            border_color=t(self.border_color),
            text_bg_color=t(self.text_bg_color),
            text_fg_color=t(self.text_fg_color),
            key_color=t(self.key_color),
            hover_transform=self.hover_transform,
            select_transform=self.select_transform,
            flash_up_transform=self.flash_up_transform,
            flash_down_transform=self.flash_down_transform,
            key_transform=self.key_transform,
        )


@dataclass
class FrameSpacing:
    margin: int
    padding: int

    border_thickness: int
    frame_thickness: int

    font_size_lg: int
    font_size_md: int
    font_size_sm: int


@dataclass
class FrameStyling:
    base_colors: FrameColoring
    spacing_standard: FrameSpacing

    layout_form: Optional[LayoutForm] = LayoutForm.STD
    current_colors: Optional[FrameColoring] = None
    spacing_wide: Optional[FrameSpacing] = None
    spacing_tight: Optional[FrameSpacing] = None

    @property
    def colors(self) -> FrameColoring:
        if self.current_colors is None:
            return self.base_colors
        return self.current_colors
    
    @colors.setter
    def colors(self, new_colors: FrameColoring):
        self.current_colors = new_colors
    
    def reset_color(self):
        self.current_colors = None

    @property
    def spacing(self) -> FrameSpacing:
        match self.layout_form:
            case LayoutForm.STD:
                return self.spacing_standard
            case LayoutForm.WID:
                return self.spacing_wide or self.spacing_standard
            case LayoutForm.TGT:
                return self.spacing_tight or self.spacing_standard
            case _:
                raise Exception(f"Unknown layout form '{self.layout_form}'")