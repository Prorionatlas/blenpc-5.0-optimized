import pytest
from blenpc.mf_v5.walls import build_wall_strip, inward_normal
from blenpc.mf_v5.edge_classifier import ClassifiedEdge, EdgeType
from blenpc.mf_v5.vertical_authority import FloorElevations

def test_inward_normal():
    # Horizontal edge at bottom of footprint
    p1, p2 = (0, 0), (4, 0)
    centroid = (2, 1)
    nx, ny = inward_normal(p1, p2, centroid)
    # Normal should point UP (0, 1)
    assert nx == 0
    assert ny == 1

def test_build_wall_strip_exterior():
    edge = ClassifiedEdge((0, 0), (4, 0), EdgeType.EXTERIOR)
    elev = FloorElevations(0, 3, 3.2)
    centroid = (2, 1)
    
    verts, faces = build_wall_strip(edge, elev, centroid)
    
    assert len(verts) == 8
    assert len(faces) == 6
    
    # Exterior walls grow inward. 
    # Normal is (0, 1). 
    # Outward points (offset_out=0) are at y=0.
    # Inward points (offset_in=0.2) are at y=0.2.
    y_coords = [v[1] for v in verts]
    assert min(y_coords) == 0.0
    assert max(y_coords) == 0.2
