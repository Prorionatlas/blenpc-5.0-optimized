"""Core datatypes for deterministic procedural generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Axis(str, Enum):
    X = "X"
    Y = "Y"


class RoofType(str, Enum):
    FLAT = "flat"
    GABLED = "gabled"
    SHED = "shed"
    HIP = "hip"


@dataclass(frozen=True)
class Rect:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def width(self) -> float:
        return self.max_x - self.min_x

    def height(self) -> float:
        return self.max_y - self.min_y


@dataclass(frozen=True)
class Room:
    rect: Rect
    floor_index: int
    id: int


@dataclass(frozen=True)
class Corridor:
    rect: Rect
    floor_index: int
    orientation: Axis = Axis.Y


@dataclass(frozen=True)
class BuildingSpec:
    width: float
    depth: float
    floors: int
    seed: int
    roof_type: RoofType = RoofType.HIP


import warnings

@dataclass(frozen=True)
class WallSegment:
    """DEPRECATED: Use ClassifiedEdge and build_wall_strip in v5.0."""
    room_id: int
    side: str
    x1: float
    y1: float
    x2: float
    y2: float
    height: float
    thickness: float
    
    def __post_init__(self):
        warnings.warn("WallSegment is deprecated in v5.0", DeprecationWarning, stacklevel=2)


@dataclass(frozen=True)
class DoorOpening:
    room_id: int
    side: str
    center: Tuple[float, float]
    width: float
    height: float


AdjacencyMap = Dict[int, Dict[str, Optional[int]]]
