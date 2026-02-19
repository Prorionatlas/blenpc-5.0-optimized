import pytest
from blenpc.mf_v5.geometry_authority import quantize, robust_union
from blenpc.mf_v5.datamodel import Room, Rect

def test_quantization():
    # v5.2.0 uses MICRO_UNIT (0.025)
    # 0.24 snaps to 0.25 (10 units)
    assert quantize(0.24) == 0.25
    # 0.12 snaps to 0.125 (5 units)
    assert quantize(0.12) == 0.125
    # 0.38 snaps to 0.375 (15 units)
    assert quantize(0.38) == 0.375

def test_robust_union_basic():
    rooms = [
        Room(Rect(0, 0, 2, 2), 0, 1),
        Room(Rect(2, 0, 4, 2), 0, 2)
    ]
    footprint = robust_union(rooms)
    assert footprint.area == 8.0
    assert footprint.geom_type == 'Polygon'

def test_robust_union_touching_with_drift():
    # Slightly overlapping or gapped rooms that should be snapped by MICRO_UNIT
    rooms = [
        Room(Rect(0, 0, 2.001, 2), 0, 1),
        Room(Rect(1.999, 0, 4, 2), 0, 2)
    ]
    footprint = robust_union(rooms)
    assert footprint.area == 8.0
