from blenpc.mf_v5.datamodel import Rect, RoofType
from blenpc.mf_v5.roof import build_roof

def test_hip_roof_geometry():
    rect = Rect(0, 0, 10, 10)
    roof = build_roof(rect, 0, RoofType.HIP)
    assert len(roof.faces) == 5 # 4 slopes + 1 bottom
    assert roof.roof_type == RoofType.HIP

def test_flat_roof_geometry():
    rect = Rect(0, 0, 10, 10)
    roof = build_roof(rect, 0, RoofType.FLAT)
    assert len(roof.faces) == 2 # Top + Bottom
    assert roof.roof_type == RoofType.FLAT

def test_gabled_roof_geometry():
    rect = Rect(0, 0, 10, 10)
    roof = build_roof(rect, 0, RoofType.GABLED)
    assert len(roof.faces) == 5 # 2 slopes + 2 gable ends + 1 bottom
    assert roof.roof_type == RoofType.GABLED

def test_shed_roof_geometry():
    rect = Rect(0, 0, 10, 10)
    roof = build_roof(rect, 0, RoofType.SHED)
    assert len(roof.faces) == 6 # 1 slope + 4 sides + 1 bottom
    assert roof.roof_type == RoofType.SHED
