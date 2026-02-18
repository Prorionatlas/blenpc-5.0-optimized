"""
Test suite for composed wall system (wall + door + window integration).

This test file verifies:
1. Wall + door integration
2. Wall + window integration
3. Wall + multiple openings
4. Scene grid placement
5. JSON command format
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from blenpc.atoms.wall_modular import build_wall_composed, composed_wall_to_json
from blenpc import config


class TestComposedWallBasics:
    """Test basic composed wall creation."""
    
    def test_wall_only(self):
        """Test composed wall with no openings."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=None,
            name="simple_wall"
        )
        
        assert result["wall_data"] is not None
        assert len(result["door_objects"]) == 0
        assert len(result["window_objects"]) == 0
        assert result["meta"]["opening_count"] == 0
    
    def test_wall_with_single_door(self):
        """Test composed wall with one door."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {
                    "type": "door",
                    "position": {"x_ratio": 0.5},
                    "style": "single"
                }
            ],
            name="wall_with_door"
        )
        
        assert len(result["door_objects"]) == 1
        assert len(result["window_objects"]) == 0
        assert result["meta"]["opening_count"] == 1
        
        # Check door was created
        door = result["door_objects"][0]
        assert door.style == "single"
    
    def test_wall_with_single_window(self):
        """Test composed wall with one window."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {
                    "type": "window",
                    "position": {"x_ratio": 0.5},
                    "style": "standard"
                }
            ],
            name="wall_with_window"
        )
        
        assert len(result["door_objects"]) == 0
        assert len(result["window_objects"]) == 1
        assert result["meta"]["opening_count"] == 1
        
        # Check window was created
        window = result["window_objects"][0]
        assert window.style == "standard"


class TestMultipleOpenings:
    """Test walls with multiple openings."""
    
    def test_door_and_window(self):
        """Test wall with both door and window."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {
                    "type": "door",
                    "position": {"x_ratio": 0.3},
                    "style": "single"
                },
                {
                    "type": "window",
                    "position": {"x_ratio": 0.7},
                    "style": "standard"
                }
            ],
            name="wall_door_window"
        )
        
        assert len(result["door_objects"]) == 1
        assert len(result["window_objects"]) == 1
        assert result["meta"]["opening_count"] == 2
    
    def test_multiple_windows(self):
        """Test wall with multiple windows."""
        result = build_wall_composed(
            wall_spec={"length": 10.0, "height": 3.0},
            opening_specs=[
                {"type": "window", "position": {"x_ratio": 0.25}, "style": "standard"},
                {"type": "window", "position": {"x_ratio": 0.5}, "style": "standard"},
                {"type": "window", "position": {"x_ratio": 0.75}, "style": "standard"}
            ],
            name="wall_three_windows"
        )
        
        assert len(result["window_objects"]) == 3
        assert result["meta"]["opening_count"] == 3
    
    def test_multiple_doors(self):
        """Test wall with multiple doors."""
        result = build_wall_composed(
            wall_spec={"length": 8.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.3}, "style": "single"},
                {"type": "door", "position": {"x_ratio": 0.7}, "style": "single"}
            ],
            name="wall_two_doors"
        )
        
        assert len(result["door_objects"]) == 2
        assert result["meta"]["opening_count"] == 2


class TestPositioning:
    """Test opening positioning."""
    
    def test_position_by_ratio(self):
        """Test positioning by x_ratio."""
        result = build_wall_composed(
            wall_spec={"length": 10.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.5}, "style": "single"}
            ]
        )
        
        # Door should be centered (approximately)
        door = result["door_objects"][0]
        door_center_x = door.grid_pos.to_meters()[0] + door.meta["width_m"] / 2
        assert door_center_x == pytest.approx(5.0, abs=0.5)
    
    def test_position_by_meters(self):
        """Test positioning by x_meters."""
        result = build_wall_composed(
            wall_spec={"length": 10.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_meters": 3.0}, "style": "single"}
            ]
        )
        
        # Door should be at 3.0m (approximately)
        door = result["door_objects"][0]
        door_center_x = door.grid_pos.to_meters()[0] + door.meta["width_m"] / 2
        assert door_center_x == pytest.approx(3.0, abs=0.5)
    
    def test_invalid_position(self):
        """Test that missing position raises error."""
        with pytest.raises(ValueError):
            build_wall_composed(
                wall_spec={"length": 5.0, "height": 3.0},
                opening_specs=[
                    {"type": "door", "position": {}, "style": "single"}
                ]
            )


class TestDoorStyles:
    """Test different door styles in composed walls."""
    
    def test_single_door(self):
        """Test single door style."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.5}, "style": "single"}
            ]
        )
        
        door = result["door_objects"][0]
        assert door.style == "single"
        assert door.meta["width_m"] == config.DOOR_STANDARDS["single"]["w"]
    
    def test_double_door(self):
        """Test double door style."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.5}, "style": "double"}
            ]
        )
        
        door = result["door_objects"][0]
        assert door.style == "double"
        assert door.meta["width_m"] == config.DOOR_STANDARDS["double"]["w"]
    
    def test_door_materials(self):
        """Test door material specification."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {
                    "type": "door",
                    "position": {"x_ratio": 0.5},
                    "style": "single",
                    "material": "glass"
                }
            ]
        )
        
        door = result["door_objects"][0]
        assert door.material == "glass"


class TestWindowStyles:
    """Test different window styles in composed walls."""
    
    def test_standard_window(self):
        """Test standard window style."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "window", "position": {"x_ratio": 0.5}, "style": "standard"}
            ]
        )
        
        window = result["window_objects"][0]
        assert window.style == "standard"
        assert window.meta["width_m"] == config.WINDOW_STANDARDS["standard"]["w"]
    
    def test_large_window(self):
        """Test large window style."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "window", "position": {"x_ratio": 0.5}, "style": "large"}
            ]
        )
        
        window = result["window_objects"][0]
        assert window.style == "large"
    
    def test_window_glass_materials(self):
        """Test window glass material specification."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {
                    "type": "window",
                    "position": {"x_ratio": 0.5},
                    "style": "standard",
                    "glass_inner": "transparent",
                    "glass_outer": "mirror"
                }
            ]
        )
        
        window = result["window_objects"][0]
        assert window.glass_inner == "transparent"
        assert window.glass_outer == "mirror"


class TestSceneGrid:
    """Test scene grid integration."""
    
    def test_all_objects_placed(self):
        """Test that all objects are placed in scene grid."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.3}, "style": "single"},
                {"type": "window", "position": {"x_ratio": 0.7}, "style": "standard"}
            ]
        )
        
        scene = result["scene_grid"]
        
        # Should have 1 object (wall) in grid, others are children
        assert len(scene.get_all_objects()) == 1
        assert "children" in result["wall_data"].meta
        assert len(result["wall_data"].meta["children"]["doors"]) == 1
        assert len(result["wall_data"].meta["children"]["windows"]) == 1
    
    def test_no_collisions(self):
        """Test that objects don't collide."""
        result = build_wall_composed(
            wall_spec={"length": 10.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.2}, "style": "single"},
                {"type": "window", "position": {"x_ratio": 0.8}, "style": "standard"}
            ]
        )
        
        # Only wall is in grid
        assert result["meta"]["total_objects"] == 1
        assert result["meta"]["child_count"] == 2
    
    def test_scene_stats(self):
        """Test scene statistics."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.5}, "style": "single"}
            ]
        )
        
        scene = result["scene_grid"]
        stats = scene.get_stats()
        
        assert stats["object_count"] == 1  # only wall
        assert stats["occupied_cells"] > 0


class TestWallOpeningAlignment:
    """Test that wall openings align with door/window slots."""
    
    def test_door_slot_alignment(self):
        """Test that door slot aligns with wall opening."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.5}, "style": "single"}
            ]
        )
        
        wall = result["wall_data"]
        door = result["door_objects"][0]
        
        # Wall should have door opening slot
        door_slots = [s for s in wall.slots if s["type"] == "door_opening"]
        assert len(door_slots) == 1
        
        # Door should have wall interface slot
        wall_slots = [s for s in door.slots if s["id"] == "wall_interface"]
        assert len(wall_slots) == 1
    
    def test_window_slot_alignment(self):
        """Test that window slot aligns with wall opening."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "window", "position": {"x_ratio": 0.5}, "style": "standard"}
            ]
        )
        
        wall = result["wall_data"]
        window = result["window_objects"][0]
        
        # Wall should have window opening slot
        window_slots = [s for s in wall.slots if s["type"] == "window_opening"]
        assert len(window_slots) == 1
        
        # Window should have wall interface slot
        wall_slots = [s for s in window.slots if s["id"] == "wall_interface"]
        assert len(wall_slots) == 1


class TestSerialization:
    """Test JSON serialization."""
    
    def test_composed_wall_to_json(self):
        """Test serialization of composed wall."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.5}, "style": "single"}
            ],
            name="test_composed"
        )
        
        json_str = composed_wall_to_json(result)
        
        assert "wall" in json_str
        assert "doors" in json_str
        assert "windows" in json_str
        assert "test_composed" in json_str
    
    def test_json_structure(self):
        """Test JSON structure is correct."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0},
            opening_specs=[
                {"type": "door", "position": {"x_ratio": 0.3}, "style": "single"},
                {"type": "window", "position": {"x_ratio": 0.7}, "style": "standard"}
            ]
        )
        
        json_str = composed_wall_to_json(result)
        
        import json
        data = json.loads(json_str)
        
        assert "wall" in data
        assert "doors" in data
        assert "windows" in data
        assert "scene_stats" in data
        assert "meta" in data
        
        assert len(data["doors"]) == 1
        assert len(data["windows"]) == 1


class TestEdgeCases:
    """Test edge cases."""
    
    def test_very_long_wall(self):
        """Test wall with many openings."""
        result = build_wall_composed(
            wall_spec={"length": 20.0, "height": 3.0},
            opening_specs=[
                {"type": "window", "position": {"x_ratio": 0.1}, "style": "standard"},
                {"type": "door", "position": {"x_ratio": 0.3}, "style": "single"},
                {"type": "window", "position": {"x_ratio": 0.5}, "style": "standard"},
                {"type": "window", "position": {"x_ratio": 0.7}, "style": "standard"},
                {"type": "door", "position": {"x_ratio": 0.9}, "style": "single"}
            ]
        )
        
        assert result["meta"]["opening_count"] == 5
        assert len(result["door_objects"]) == 2
        assert len(result["window_objects"]) == 3
    
    def test_custom_wall_thickness(self):
        """Test wall with custom thickness."""
        result = build_wall_composed(
            wall_spec={"length": 5.0, "height": 3.0, "thickness": 0.3},
            opening_specs=None
        )
        
        assert result["wall_data"].meta["thickness_m"] == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
