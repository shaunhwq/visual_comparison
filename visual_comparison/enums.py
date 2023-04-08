import enum


class VCModes(enum.Enum):
    Compare = enum.auto()
    Concat = enum.auto()
    Specific = enum.auto()


class VCState(enum.Enum):
    UPDATE_MODE = enum.auto()
    UPDATE_FILE = enum.auto()
    UPDATE_METHOD = enum.auto()
    UPDATED = enum.auto()
