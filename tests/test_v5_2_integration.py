import pytest
from pathlib import Path
from blenpc.mf_v5.engine import generate
from blenpc.mf_v5.datamodel import BuildingSpec, RoofType

def test_generate_building_minimal(tmp_path):
    """Test full pipeline generation with a simple 1-floor spec."""
    spec = BuildingSpec(
        width=10.0,
        depth=8.0,
        floors=1,
        seed=42,
        roof_type=RoofType.FLAT
    )
    
    # We test the engine's data output without Blender dependency (mocking bpy in engine.py)
    # The engine handles the bpy import error gracefully by returning glb_path=None
    output = generate(spec, tmp_path)
    
    assert len(output.floors) == 1
    assert output.roof_type == "flat"
    assert Path(output.export_manifest).exists()
    assert output.floors[0].room_count > 0

def test_generate_multi_floor(tmp_path):
    """Test full pipeline generation with multiple floors."""
    spec = BuildingSpec(
        width=15.0,
        depth=12.0,
        floors=3,
        seed=123,
        roof_type=RoofType.HIP
    )
    
    output = generate(spec, tmp_path)
    
    assert len(output.floors) == 3
    assert output.roof_type == "hip"
    for floor in output.floors:
        assert floor.wall_segment_count > 0
