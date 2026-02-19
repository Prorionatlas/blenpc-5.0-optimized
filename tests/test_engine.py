from pathlib import Path

from blenpc.mf_v5 import BuildingSpec, RoofType, generate
from blenpc.mf_v5.floorplan import generate_floorplan


def test_floorplan_deterministic():
    rooms_a, corridor_a = generate_floorplan(20, 16, seed=42, floor_index=0)
    rooms_b, corridor_b = generate_floorplan(20, 16, seed=42, floor_index=0)
    assert [r.rect for r in rooms_a] == [r.rect for r in rooms_b]
    assert corridor_a.rect == corridor_b.rect


def test_engine_generates_manifest(tmp_path: Path):
    spec = BuildingSpec(width=20, depth=16, floors=2, seed=42, roof_type=RoofType.HIP)
    out = generate(spec, tmp_path)
    assert len(out.floors) == 2
    assert Path(out.export_manifest).exists()
