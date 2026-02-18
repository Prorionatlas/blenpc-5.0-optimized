"""
GridPos - Integer-based coordinate system for BlenPC v5.2.0

This module implements a deterministic, integer-based coordinate system
that eliminates floating-point precision errors and enables efficient
spatial queries.

Key Concepts:
- All coordinates stored as integers (units)
- 1 unit = MICRO_UNIT = 0.025m (2.5cm)
- Snap modes: micro (2.5cm), meso (25cm), macro (1m)
- Conversion to meters only when interfacing with Blender API
"""

from typing import Tuple, Optional
from dataclasses import dataclass
from .. import config


@dataclass(frozen=True)
class GridPos:
    """
    Integer-based 3D coordinate in grid space.
    
    Attributes:
        x, y, z: Integer coordinates in grid units (1 unit = 0.025m)
    
    Examples:
        >>> pos = GridPos(40, 0, 120)  # (1.0m, 0m, 3.0m)
        >>> pos.to_meters()
        (1.0, 0.0, 3.0)
        
        >>> pos2 = GridPos.from_meters(2.5, 0, 1.5, snap="meso")
        >>> pos2.x, pos2.y, pos2.z
        (100, 0, 60)  # snapped to 0.25m grid
    """
    x: int
    y: int
    z: int
    
    def to_meters(self) -> Tuple[float, float, float]:
        """
        Convert grid coordinates to metric coordinates.
        
        Returns:
            Tuple of (x, y, z) in meters
        """
        m = config.MICRO_UNIT
        return (self.x * m, self.y * m, self.z * m)
    
    @staticmethod
    def from_meters(
        mx: float, 
        my: float, 
        mz: float, 
        snap: str = "meso"
    ) -> "GridPos":
        """
        Convert metric coordinates to grid coordinates with snapping.
        
        Args:
            mx, my, mz: Coordinates in meters
            snap: Snap mode ("micro", "meso", "macro")
        
        Returns:
            GridPos with snapped integer coordinates
        
        Raises:
            ValueError: If snap mode is invalid
        """
        if snap not in config.SNAP_MODES:
            raise ValueError(
                f"Invalid snap mode '{snap}'. "
                f"Valid modes: {list(config.SNAP_MODES.keys())}"
            )
        
        snap_unit = config.SNAP_MODES[snap] * config.MICRO_UNIT
        
        # Snap to grid and convert to integer units
        def snap_coord(value: float) -> int:
            snapped = round(value / snap_unit) * snap_unit
            return round(snapped / config.MICRO_UNIT)
        
        return GridPos(
            x=snap_coord(mx),
            y=snap_coord(my),
            z=snap_coord(mz)
        )
    
    def __add__(self, other: "GridPos") -> "GridPos":
        """Vector addition."""
        return GridPos(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: "GridPos") -> "GridPos":
        """Vector subtraction."""
        return GridPos(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: int) -> "GridPos":
        """Scalar multiplication."""
        return GridPos(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __repr__(self) -> str:
        mx, my, mz = self.to_meters()
        return f"GridPos({self.x}, {self.y}, {self.z}) = ({mx:.3f}m, {my:.3f}m, {mz:.3f}m)"
    
    def distance_to(self, other: "GridPos") -> float:
        """
        Calculate Euclidean distance to another GridPos.
        
        Returns:
            Distance in meters
        """
        dx = (self.x - other.x) * config.MICRO_UNIT
        dy = (self.y - other.y) * config.MICRO_UNIT
        dz = (self.z - other.z) * config.MICRO_UNIT
        return (dx**2 + dy**2 + dz**2) ** 0.5
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to tuple (for dict keys)."""
        return (self.x, self.y, self.z)


def snap(value: float, mode: str = "meso") -> float:
    """
    Legacy snap function - kept for backward compatibility.
    
    Internally uses GridPos for consistent snapping behavior.
    
    Args:
        value: Value in meters
        mode: Snap mode ("micro", "meso", "macro")
    
    Returns:
        Snapped value in meters
    
    Examples:
        >>> snap(1.23, "meso")
        1.25
        >>> snap(1.23, "macro")
        1.0
    """
    pos = GridPos.from_meters(value, 0, 0, snap=mode)
    return pos.to_meters()[0]


# Convenience functions
def meters_to_units(meters: float) -> int:
    """Convert meters to grid units."""
    return round(meters / config.MICRO_UNIT)


def units_to_meters(units: int) -> float:
    """Convert grid units to meters."""
    return units * config.MICRO_UNIT
