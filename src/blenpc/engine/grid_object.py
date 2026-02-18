"""
IGridObject - Interface for grid-aware objects in BlenPC v5.2.0

This module defines the contract that all grid-aware objects (atoms)
must implement to participate in the scene grid system.

Key Concepts:
- Protocol-based interface (structural typing)
- Footprint calculation (which cells does the object occupy?)
- Placement validation (can this object be placed here?)
- Slot system integration
"""

from typing import Protocol, Set, Tuple, List, Dict, Optional
from .grid_pos import GridPos


class IGridObject(Protocol):
    """
    Protocol for objects that can be placed on the scene grid.
    
    All atoms (wall, door, window, furniture, etc.) should implement
    this interface to enable grid-based placement and collision detection.
    
    Attributes:
        name: Unique identifier for this object instance
        grid_pos: Position in grid space (integer coordinates)
        grid_size: Size in grid units (width, depth, height)
        snap_mode: Snap mode used for this object ("micro"|"meso"|"macro")
        slots: List of connection/attachment points
        tags: List of classification tags (e.g., "arch_wall", "mat_brick")
    """
    
    name: str
    grid_pos: GridPos
    grid_size: Tuple[int, int, int]  # (width, depth, height) in units
    snap_mode: str
    slots: List[Dict]
    tags: List[str]
    
    def get_footprint(self) -> Set[Tuple[int, int, int]]:
        """
        Calculate which grid cells this object occupies.
        
        Returns:
            Set of (x, y, z) tuples representing occupied cells
        
        Example:
            A 2x1x3 object at (10, 0, 0) occupies:
            {(10,0,0), (11,0,0), (10,0,1), (11,0,1), (10,0,2), (11,0,2)}
        """
        ...
    
    def validate_placement(self, scene: "SceneGrid") -> bool:
        """
        Check if this object can be placed at its current position.
        
        Args:
            scene: The scene grid to check against
        
        Returns:
            True if placement is valid (no collisions), False otherwise
        """
        ...


class GridObjectMixin:
    """
    Mixin class providing default implementations of IGridObject methods.
    
    Usage:
        class Wall(GridObjectMixin):
            def __init__(self, ...):
                self.name = "wall_01"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (200, 8, 120)  # 5m x 0.2m x 3m
                self.snap_mode = "macro"
                self.slots = []
                self.tags = ["arch_wall"]
    """
    
    def get_footprint(self) -> Set[Tuple[int, int, int]]:
        """Default footprint implementation - full AABB."""
        px, py, pz = self.grid_pos.x, self.grid_pos.y, self.grid_pos.z
        sx, sy, sz = self.grid_size
        
        footprint = set()
        for dx in range(sx):
            for dy in range(sy):
                for dz in range(sz):
                    footprint.add((px + dx, py + dy, pz + dz))
        
        return footprint
    
    def validate_placement(self, scene: "SceneGrid") -> bool:
        """Default placement validation - check if all cells are free."""
        from .grid_manager import SceneGrid
        if not isinstance(scene, SceneGrid):
            raise TypeError("scene must be a SceneGrid instance")
        
        return scene.is_free(self.grid_pos, self.grid_size)
    
    def get_aabb(self) -> Dict:
        """
        Get axis-aligned bounding box in meters.
        
        Returns:
            Dict with "min" and "max" keys, each containing [x, y, z] in meters
        """
        min_x, min_y, min_z = self.grid_pos.to_meters()
        
        max_pos = self.grid_pos + GridPos(*self.grid_size)
        max_x, max_y, max_z = max_pos.to_meters()
        
        return {
            "min": [min_x, min_y, min_z],
            "max": [max_x, max_y, max_z]
        }
    
    def get_center(self) -> GridPos:
        """Get the center position of this object in grid space."""
        half_size = GridPos(
            self.grid_size[0] // 2,
            self.grid_size[1] // 2,
            self.grid_size[2] // 2
        )
        return self.grid_pos + half_size


# Helper function for creating grid objects
def create_grid_object(
    name: str,
    pos_meters: Tuple[float, float, float],
    size_meters: Tuple[float, float, float],
    snap_mode: str = "meso",
    slots: Optional[List[Dict]] = None,
    tags: Optional[List[str]] = None
) -> Dict:
    """
    Factory function for creating grid object data structures.
    
    Args:
        name: Object name
        pos_meters: Position in meters (x, y, z)
        size_meters: Size in meters (width, depth, height)
        snap_mode: Snap mode for position
        slots: List of slot definitions
        tags: List of classification tags
    
    Returns:
        Dict containing grid object data
    """
    from .grid_pos import meters_to_units
    
    grid_pos = GridPos.from_meters(*pos_meters, snap=snap_mode)
    grid_size = tuple(meters_to_units(s) for s in size_meters)
    
    return {
        "name": name,
        "grid_pos": grid_pos,
        "grid_size": grid_size,
        "snap_mode": snap_mode,
        "slots": slots or [],
        "tags": tags or []
    }
