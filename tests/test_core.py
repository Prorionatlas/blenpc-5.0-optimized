import pytest
from pathlib import Path
from blenpc.mf_v5 import BuildingSpec, RoofType, generate
from blenpc.mf_v5.exceptions import ConfigurationError, GenerationError
from blenpc.mf_v5.config import snap

def test_snap_to_grid():
    assert snap(0.24) == 0.25
    assert snap(0.12) == 0.0
    assert snap(0.51) == 0.50

def test_building_spec_validation():
    # Small dimensions should raise error
    spec = BuildingSpec(width=2.0, depth=2.0, floors=1, seed=42)
    with pytest.raises(ConfigurationError):
        generate(spec, Path("./test_output"))

def test_floorplan_generation_consistency():
    # Same seed should produce same floorplan
    from blenpc.mf_v5.floorplan import generate_floorplan
    rooms1, _ = generate_floorplan(20, 20, 42, 0)
    rooms2, _ = generate_floorplan(20, 20, 42, 0)
    
    assert len(rooms1) == len(rooms2)
    for r1, r2 in zip(rooms1, rooms2):
        assert r1.rect == r2.rect
        assert r1.id == r2.id

def test_adjacency_map_logic():
    from blenpc.mf_v5.adjacency import build_adjacency
    from blenpc.mf_v5.datamodel import Rect, Room
    
    # Create two rooms next to each other
    r1 = Room(Rect(0, 0, 5, 5), 0, 0)
    r2 = Room(Rect(5, 0, 10, 5), 0, 1)
    
    adj = build_adjacency([r1, r2])
    assert adj[0]["east"] == 1
    assert adj[1]["west"] == 0

def test_roof_generation_flat():
    from blenpc.mf_v5.roof import build_roof
    from blenpc.mf_v5.datamodel import Rect, RoofType
    
    rect = Rect(0, 0, 10, 10)
    roof = build_roof(rect, 3.0, RoofType.FLAT)
    assert len(roof.faces) == 2 # Top + Bottom
    assert roof.roof_type == RoofType.FLAT
