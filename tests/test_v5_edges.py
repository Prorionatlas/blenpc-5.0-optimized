import pytest
from shapely.geometry import box
from blenpc.mf_v5.edge_classifier import classify_edges, EdgeType
from blenpc.mf_v5.datamodel import Room, Rect

def test_classify_edges_basic():
    # Single room
    rooms = [Room(Rect(0, 0, 2, 2), 0, 1)]
    footprint = box(0, 0, 2, 2)
    edges = classify_edges(footprint, rooms)
    
    assert len(edges) == 4
    for e in edges:
        assert e.edge_type == EdgeType.EXTERIOR

def test_classify_edges_shared():
    # Two rooms sharing a wall
    rooms = [
        Room(Rect(0, 0, 2, 2), 0, 1),
        Room(Rect(2, 0, 4, 2), 0, 2)
    ]
    # Footprint is 4x2
    footprint = box(0, 0, 4, 2)
    edges = classify_edges(footprint, rooms)
    
    # Total edges: 4 (room 1) + 4 (room 2) - 1 (shared) = 7
    assert len(edges) == 7
    
    # Find the shared wall (interior)
    interior_edges = [e for e in edges if e.edge_type == EdgeType.INTERIOR]
    assert len(interior_edges) == 1
    # The shared wall is at x=2, from y=0 to y=2
    e = interior_edges[0]
    coords = sorted([e.p1, e.p2])
    assert coords == [(2, 0), (2, 2)]
