import pytest
from blenpc.mf_v5.geometry_authority import quantize, robust_union
from blenpc.mf_v5.datamodel import Room, Rect

def test_quantization():
    assert quantize(0.24) == 0.25
    assert quantize(0.12) == 0.0
    assert quantize(0.38) == 0.5

def test_robust_union_basic():
    rooms = [
        Room(Rect(0, 0, 2, 2), 0, 1),
        Room(Rect(2, 0, 4, 2), 0, 2)
    ]
    footprint = robust_union(rooms)
    assert footprint.area == 8.0
    assert footprint.geom_type == 'Polygon'

def test_robust_union_touching_with_drift():
    # Slightly overlapping or gapped rooms that should be snapped by GRID
    rooms = [
        Room(Rect(0, 0, 2.001, 2), 0, 1),
        Room(Rect(1.999, 0, 4, 2), 0, 2)
    ]
    footprint = robust_union(rooms)
    assert footprint.area == 8.0
