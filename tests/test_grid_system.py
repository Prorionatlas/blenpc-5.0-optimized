"""
Test suite for integer grid system (GridPos, SceneGrid, IGridObject)

This test file verifies:
1. GridPos coordinate conversion and snapping
2. SceneGrid collision detection and placement
3. IGridObject interface implementation
4. Backward compatibility with legacy snap() function
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from blenpc.engine.grid_pos import GridPos, snap, meters_to_units, units_to_meters
from blenpc.engine.grid_manager import SceneGrid
from blenpc.engine.grid_object import GridObjectMixin, create_grid_object
from blenpc import config


class TestGridPos:
    """Test GridPos integer coordinate system."""
    
    def test_basic_creation(self):
        """Test basic GridPos creation."""
        pos = GridPos(40, 0, 120)
        assert pos.x == 40
        assert pos.y == 0
        assert pos.z == 120
    
    def test_to_meters(self):
        """Test conversion to meters."""
        pos = GridPos(40, 0, 120)  # (1.0m, 0m, 3.0m)
        mx, my, mz = pos.to_meters()
        assert mx == pytest.approx(1.0)
        assert my == pytest.approx(0.0)
        assert mz == pytest.approx(3.0)
    
    def test_from_meters_meso(self):
        """Test conversion from meters with meso snap."""
        pos = GridPos.from_meters(1.23, 0, 2.87, snap="meso")
        mx, my, mz = pos.to_meters()
        assert mx == pytest.approx(1.25)  # snapped to 0.25m
        assert my == pytest.approx(0.0)
        assert mz == pytest.approx(2.75)  # snapped to 0.25m (2.87 rounds down)
    
    def test_from_meters_macro(self):
        """Test conversion from meters with macro snap."""
        pos = GridPos.from_meters(1.23, 0, 2.87, snap="macro")
        mx, my, mz = pos.to_meters()
        assert mx == pytest.approx(1.0)  # snapped to 1.0m
        assert my == pytest.approx(0.0)
        assert mz == pytest.approx(3.0)  # snapped to 1.0m
    
    def test_from_meters_micro(self):
        """Test conversion from meters with micro snap."""
        pos = GridPos.from_meters(0.123, 0, 0, snap="micro")
        mx, _, _ = pos.to_meters()
        assert mx == pytest.approx(0.125)  # snapped to 0.025m
    
    def test_invalid_snap_mode(self):
        """Test invalid snap mode raises error."""
        with pytest.raises(ValueError):
            GridPos.from_meters(1.0, 0, 0, snap="invalid")
    
    def test_vector_addition(self):
        """Test GridPos addition."""
        pos1 = GridPos(10, 20, 30)
        pos2 = GridPos(5, 10, 15)
        result = pos1 + pos2
        assert result.x == 15
        assert result.y == 30
        assert result.z == 45
    
    def test_vector_subtraction(self):
        """Test GridPos subtraction."""
        pos1 = GridPos(10, 20, 30)
        pos2 = GridPos(5, 10, 15)
        result = pos1 - pos2
        assert result.x == 5
        assert result.y == 10
        assert result.z == 15
    
    def test_scalar_multiplication(self):
        """Test GridPos scalar multiplication."""
        pos = GridPos(10, 20, 30)
        result = pos * 2
        assert result.x == 20
        assert result.y == 40
        assert result.z == 60
    
    def test_distance_calculation(self):
        """Test distance calculation between two positions."""
        pos1 = GridPos(0, 0, 0)
        pos2 = GridPos(40, 0, 0)  # 1.0m away
        distance = pos1.distance_to(pos2)
        assert distance == pytest.approx(1.0)
    
    def test_to_tuple(self):
        """Test conversion to tuple (for dict keys)."""
        pos = GridPos(10, 20, 30)
        assert pos.to_tuple() == (10, 20, 30)


class TestLegacySnap:
    """Test backward compatibility with legacy snap() function."""
    
    def test_snap_meso(self):
        """Test legacy snap with meso mode."""
        result = snap(1.23, "meso")
        assert result == pytest.approx(1.25)
    
    def test_snap_macro(self):
        """Test legacy snap with macro mode."""
        result = snap(1.23, "macro")
        assert result == pytest.approx(1.0)
    
    def test_snap_default(self):
        """Test legacy snap with default mode (meso)."""
        result = snap(1.23)
        assert result == pytest.approx(1.25)


class TestSceneGrid:
    """Test SceneGrid sparse hashmap implementation."""
    
    def test_empty_scene(self):
        """Test empty scene creation."""
        scene = SceneGrid()
        assert len(scene.get_all_objects()) == 0
        assert scene.get_bounds() is None
    
    def test_place_object(self):
        """Test placing an object on the grid."""
        scene = SceneGrid()
        
        # Create a simple object
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test_obj"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = ["test"]
        
        obj = SimpleObject()
        result = scene.place(obj)
        assert result is True
        assert len(scene.get_all_objects()) == 1
    
    def test_collision_detection(self):
        """Test collision detection."""
        scene = SceneGrid()
        
        class SimpleObject(GridObjectMixin):
            def __init__(self, name, pos):
                self.name = name
                self.grid_pos = pos
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = []
        
        obj1 = SimpleObject("obj1", GridPos(0, 0, 0))
        obj2 = SimpleObject("obj2", GridPos(5, 5, 5))  # overlaps with obj1
        
        assert scene.place(obj1) is True
        assert scene.place(obj2) is False  # collision
    
    def test_remove_object(self):
        """Test removing an object."""
        scene = SceneGrid()
        
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test_obj"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        scene.place(obj)
        assert scene.remove("test_obj") is True
        assert len(scene.get_all_objects()) == 0
    
    def test_is_free(self):
        """Test is_free region check."""
        scene = SceneGrid()
        
        # Empty scene - should be free
        assert scene.is_free(GridPos(0, 0, 0), (10, 10, 10)) is True
        
        # Place object
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test_obj"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        scene.place(obj)
        
        # Now should not be free
        assert scene.is_free(GridPos(0, 0, 0), (10, 10, 10)) is False
        
        # Adjacent region should be free
        assert scene.is_free(GridPos(10, 0, 0), (10, 10, 10)) is True
    
    def test_get_at(self):
        """Test get_at position query."""
        scene = SceneGrid()
        
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test_obj"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        scene.place(obj)
        
        assert scene.get_at(GridPos(0, 0, 0)) == "test_obj"
        assert scene.get_at(GridPos(5, 5, 5)) == "test_obj"
        assert scene.get_at(GridPos(100, 100, 100)) is None
    
    def test_get_objects_by_tag(self):
        """Test tag-based object search."""
        scene = SceneGrid()
        
        class SimpleObject(GridObjectMixin):
            def __init__(self, name, tags):
                self.name = name
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = tags
        
        obj1 = SimpleObject("wall", ["arch_wall", "mat_brick"])
        obj2 = SimpleObject("door", ["arch_door", "mat_wood"])
        
        # Place at different positions to avoid collision
        obj1.grid_pos = GridPos(0, 0, 0)
        obj2.grid_pos = GridPos(100, 0, 0)
        
        scene.place(obj1)
        scene.place(obj2)
        
        walls = scene.get_objects_by_tag("arch_wall")
        assert len(walls) == 1
        assert walls[0].name == "wall"
    
    def test_scene_stats(self):
        """Test scene statistics."""
        scene = SceneGrid()
        
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test_obj"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (10, 10, 10)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        scene.place(obj)
        
        stats = scene.get_stats()
        assert stats["object_count"] == 1
        assert stats["occupied_cells"] == 1000  # 10x10x10


class TestGridObjectMixin:
    """Test GridObjectMixin default implementations."""
    
    def test_get_footprint(self):
        """Test footprint calculation."""
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (2, 2, 2)
                self.snap_mode = "meso"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        footprint = obj.get_footprint()
        assert len(footprint) == 8  # 2x2x2
        assert (0, 0, 0) in footprint
        assert (1, 1, 1) in footprint
    
    def test_get_aabb(self):
        """Test AABB calculation."""
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (40, 8, 120)  # 1m x 0.2m x 3m
                self.snap_mode = "macro"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        aabb = obj.get_aabb()
        
        assert aabb["min"] == pytest.approx([0.0, 0.0, 0.0])
        assert aabb["max"] == pytest.approx([1.0, 0.2, 3.0])
    
    def test_get_center(self):
        """Test center position calculation."""
        class SimpleObject(GridObjectMixin):
            def __init__(self):
                self.name = "test"
                self.grid_pos = GridPos(0, 0, 0)
                self.grid_size = (40, 40, 40)  # 1m cube
                self.snap_mode = "macro"
                self.slots = []
                self.tags = []
        
        obj = SimpleObject()
        center = obj.get_center()
        cx, cy, cz = center.to_meters()
        
        assert cx == pytest.approx(0.5)
        assert cy == pytest.approx(0.5)
        assert cz == pytest.approx(0.5)


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_meters_to_units(self):
        """Test meters to units conversion."""
        assert meters_to_units(1.0) == 40
        assert meters_to_units(0.25) == 10
        assert meters_to_units(0.025) == 1
    
    def test_units_to_meters(self):
        """Test units to meters conversion."""
        assert units_to_meters(40) == pytest.approx(1.0)
        assert units_to_meters(10) == pytest.approx(0.25)
        assert units_to_meters(1) == pytest.approx(0.025)
    
    def test_create_grid_object(self):
        """Test grid object factory function."""
        obj_data = create_grid_object(
            name="test_wall",
            pos_meters=(0.0, 0.0, 0.0),
            size_meters=(5.0, 0.2, 3.0),
            snap_mode="macro",
            tags=["arch_wall"]
        )
        
        assert obj_data["name"] == "test_wall"
        assert obj_data["grid_pos"].to_meters() == pytest.approx((0.0, 0.0, 0.0))
        assert "arch_wall" in obj_data["tags"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
