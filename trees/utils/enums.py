from enum import auto, IntEnum


class BoxBoundary(IntEnum):
    TOP_L = auto()
    TOP_C = auto()
    TOP_R = auto()
    SID_L = auto()
    SID_R = auto()
    BOT_L = auto()
    BOT_C = auto()
    BOT_R = auto()


class LayoutForm(IntEnum):
    STD = auto()
    TGT = auto()
    WID = auto()


class LayoutStructure(IntEnum):
    ROW = auto()
    COL = auto()
    GRID = auto()