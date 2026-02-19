import pytest
from blenpc.mf_v5.geometry_authority import to_int_grid, from_int_grid, robust_union
from blenpc.mf_v5.collision_engine import CollisionEngine
from blenpc.mf_v5.datamodel import Room, Rect

def test_integer_grid_conversions():
    # 0.025m is 1 unit
    assert to_int_grid(0.025) == 1
    assert to_int_grid(0.050) == 2
    assert to_int_grid(0.100) == 4
    assert to_int_grid(0.250) == 10
    
    assert from_int_grid(10) == 0.250
    assert from_int_grid(1) == 0.025

def test_collision_engine_detection():
    # Two overlapping rooms
    rooms = [
        Room(Rect(0, 0, 2, 2), 0, 1),
        Room(Rect(1.5, 0, 3.5, 2), 0, 2) # 0.5m overlap
    ]
    valid, msg = CollisionEngine.validate_layout(rooms)
    assert valid is False
    assert "LAYOUT_CONFLICT" in msg
    assert "IDs [1, 2]" in msg

def test_collision_engine_clean():
    # Two touching but not overlapping rooms
    rooms = [
        Room(Rect(0, 0, 2, 2), 0, 1),
        Room(Rect(2, 0, 4, 2), 0, 2)
    ]
    valid, msg = CollisionEngine.validate_layout(rooms)
    assert valid is True
    assert msg == "LAYOUT_VALID"

def test_robust_union_integer_precision():
    # Touching rooms should merge perfectly in v5.2
    rooms = [
        Room(Rect(0, 0, 2.0001, 2), 0, 1),
        Room(Rect(1.9999, 0, 4, 2), 0, 2)
    ]
    footprint = robust_union(rooms)
    assert footprint.area == 8.0
    assert footprint.geom_type == 'Polygon'

def test_robust_union_empty_list_handling():
    with pytest.raises(ValueError, match="Cannot perform union on empty room list"):
        robust_union([])
