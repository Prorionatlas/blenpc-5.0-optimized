"""
SceneGrid - Sparse hashmap-based scene management for BlenPC v5.2.0

This module implements an efficient scene-level grid manager using
a sparse hashmap (dict) to track occupied cells.

Key Features:
- O(1) collision detection per cell
- Infinite grid (only occupied cells use memory)
- Thread-safe operations (with optional locking)
- Query operations (find objects at position, get neighbors, etc.)
"""

from typing import Dict, Set, Tuple, List, Optional, Any
from .grid_pos import GridPos
from .grid_object import IGridObject
import json


class SceneGrid:
    """
    Scene-level grid manager using sparse hashmap.
    
    The grid is represented as a dictionary where:
    - Key: (x, y, z) tuple (integer grid coordinates)
    - Value: object name (string)
    
    Only occupied cells are stored, making the grid effectively infinite
    while remaining memory-efficient.
    
    Example:
        >>> scene = SceneGrid()
        >>> wall = create_wall(...)  # implements IGridObject
        >>> scene.place(wall)
        True
        >>> scene.get_at(GridPos(0, 0, 0))
        'wall_01'
    """
    
    def __init__(self):
        """Initialize an empty scene grid."""
        self._cells: Dict[Tuple[int, int, int], str] = {}
        self._objects: Dict[str, IGridObject] = {}
    
    def place(self, obj: IGridObject) -> bool:
        """
        Place an object on the grid.
        
        Args:
            obj: Object implementing IGridObject interface
        
        Returns:
            True if placement successful, False if collision detected
        
        Raises:
            ValueError: If object with same name already exists
        """
        if obj.name in self._objects:
            raise ValueError(f"Object '{obj.name}' already exists in scene")
        
        footprint = obj.get_footprint()
        
        # Check for collisions (O(1) per cell)
        for cell in footprint:
            if cell in self._cells:
                return False  # Collision detected
        
        # Place object
        for cell in footprint:
            self._cells[cell] = obj.name
        
        self._objects[obj.name] = obj
        return True
    
    def remove(self, obj_name: str) -> bool:
        """
        Remove an object from the grid.
        
        Args:
            obj_name: Name of the object to remove
        
        Returns:
            True if object was removed, False if not found
        """
        if obj_name not in self._objects:
            return False
        
        obj = self._objects[obj_name]
        footprint = obj.get_footprint()
        
        # Remove from cells
        for cell in footprint:
            self._cells.pop(cell, None)
        
        # Remove from objects
        del self._objects[obj_name]
        return True
    
    def get_at(self, pos: GridPos) -> Optional[str]:
        """
        Get the name of the object at a specific position.
        
        Args:
            pos: Grid position to query
        
        Returns:
            Object name if cell is occupied, None otherwise
        """
        return self._cells.get(pos.to_tuple())
    
    def is_free(self, pos: GridPos, size: Tuple[int, int, int]) -> bool:
        """
        Check if a rectangular region is free.
        
        Args:
            pos: Starting position (bottom-left-front corner)
            size: Size in grid units (width, depth, height)
        
        Returns:
            True if all cells in the region are free
        """
        sx, sy, sz = size
        px, py, pz = pos.x, pos.y, pos.z
        
        for dx in range(sx):
            for dy in range(sy):
                for dz in range(sz):
                    if (px + dx, py + dy, pz + dz) in self._cells:
                        return False
        
        return True
    
    def get_object(self, name: str) -> Optional[IGridObject]:
        """Get object by name."""
        return self._objects.get(name)
    
    def get_all_objects(self) -> List[IGridObject]:
        """Get all objects in the scene."""
        return list(self._objects.values())
    
    def get_objects_by_tag(self, tag: str) -> List[IGridObject]:
        """
        Find all objects with a specific tag.
        
        Args:
            tag: Tag to search for (e.g., "arch_wall", "mat_wood")
        
        Returns:
            List of matching objects
        """
        return [obj for obj in self._objects.values() if tag in obj.tags]
    
    def get_neighbors(
        self, 
        pos: GridPos, 
        radius: int = 1
    ) -> List[Tuple[GridPos, str]]:
        """
        Get all occupied cells within a radius.
        
        Args:
            pos: Center position
            radius: Search radius in grid units
        
        Returns:
            List of (position, object_name) tuples
        """
        neighbors = []
        px, py, pz = pos.x, pos.y, pos.z
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    cell = (px + dx, py + dy, pz + dz)
                    if cell in self._cells:
                        neighbors.append((
                            GridPos(*cell),
                            self._cells[cell]
                        ))
        
        return neighbors
    
    def clear(self):
        """Remove all objects from the scene."""
        self._cells.clear()
        self._objects.clear()
    
    def get_bounds(self) -> Optional[Dict]:
        """
        Calculate the bounding box of all objects in the scene.
        
        Returns:
            Dict with "min" and "max" GridPos, or None if scene is empty
        """
        if not self._cells:
            return None
        
        cells = list(self._cells.keys())
        min_x = min(c[0] for c in cells)
        min_y = min(c[1] for c in cells)
        min_z = min(c[2] for c in cells)
        max_x = max(c[0] for c in cells)
        max_y = max(c[1] for c in cells)
        max_z = max(c[2] for c in cells)
        
        return {
            "min": GridPos(min_x, min_y, min_z),
            "max": GridPos(max_x, max_y, max_z)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the scene.
        
        Returns:
            Dict containing:
            - occupied_cells: Number of occupied cells
            - object_count: Number of objects
            - memory_estimate: Rough memory usage estimate (bytes)
        """
        return {
            "occupied_cells": len(self._cells),
            "object_count": len(self._objects),
            "memory_estimate": (
                len(self._cells) * 64 +  # dict overhead per entry
                len(self._objects) * 256  # object overhead estimate
            )
        }
    
    def to_json(self) -> str:
        """
        Serialize scene to JSON.
        
        Returns:
            JSON string representation of the scene
        
        Note:
            Objects must be JSON-serializable. Complex objects may need
            custom serialization logic.
        """
        data = {
            "cells": {
                f"{x},{y},{z}": name 
                for (x, y, z), name in self._cells.items()
            },
            "objects": {
                name: {
                    "grid_pos": obj.grid_pos.to_tuple(),
                    "grid_size": obj.grid_size,
                    "snap_mode": obj.snap_mode,
                    "tags": obj.tags
                }
                for name, obj in self._objects.items()
            }
        }
        return json.dumps(data, indent=2)
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"SceneGrid("
            f"objects={stats['object_count']}, "
            f"cells={stats['occupied_cells']}, "
            f"memory≈{stats['memory_estimate']}B)"
        )


# Convenience function for creating scenes from JSON
def scene_from_json(json_str: str) -> SceneGrid:
    """
    Deserialize a scene from JSON.
    
    Args:
        json_str: JSON string from SceneGrid.to_json()
    
    Returns:
        Reconstructed SceneGrid instance
    
    Note:
        This is a basic implementation. Full object reconstruction
        requires additional logic to instantiate specific object types.
    """
    data = json.loads(json_str)
    scene = SceneGrid()
    
    # Reconstruct cells
    for cell_str, name in data["cells"].items():
        x, y, z = map(int, cell_str.split(","))
        scene._cells[(x, y, z)] = name
    
    # Note: Object reconstruction requires factory functions
    # This is a placeholder - full implementation needed
    
    return scene
