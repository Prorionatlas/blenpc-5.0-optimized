import math
from typing import List, Tuple
from ..config import WALL_THICKNESS
from .edge_classifier import ClassifiedEdge, EdgeType
from .vertical_authority import FloorElevations
from .datamodel import Room, WallSegment

def build_room_wall_segments(rooms: List[Room]) -> dict:
    """Legacy compatibility: map rooms to wall segments."""
    # This might be deprecated soon in favor of the strip builder
    return {}

def inward_normal(p1, p2, centroid) -> Tuple[float, float]:
    """Calculate normal vector pointing toward the building's center."""
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-6: return (0, 0)
    
    nx, ny = -dy/length, dx/length
    mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
    to_center = (centroid[0]-mid[0], centroid[1]-mid[1])
    
    if nx*to_center[0] + ny*to_center[1] < 0:
        nx, ny = -nx, -ny
    return nx, ny

def build_wall_strip(edge: ClassifiedEdge, elev: FloorElevations, centroid: Tuple[float, float]) -> Tuple[List, List]:
    """Generate vertices and faces for a wall strip based on edge type."""
    nx, ny = inward_normal(edge.p1, edge.p2, centroid)
    half = WALL_THICKNESS / 2
    
    if edge.edge_type == EdgeType.EXTERIOR:
        # Single-sided offset (inward)
        offset_in, offset_out = WALL_THICKNESS, 0.0
    else:
        # Symmetric (interior wall)
        offset_in, offset_out = half, half
        
    # 4 base corners
    p1_out = (edge.p1[0] - nx*offset_out, edge.p1[1] - ny*offset_out)
    p2_out = (edge.p2[0] - nx*offset_out, edge.p2[1] - ny*offset_out)
    p1_in = (edge.p1[0] + nx*offset_in, edge.p1[1] + ny*offset_in)
    p2_in = (edge.p2[0] + nx*offset_in, edge.p2[1] + ny*offset_in)
    
    z0, z1 = elev.base_z, elev.wall_top_z
    
    # 8 vertices (4 bottom, 4 top)
    verts = [
        (p1_out[0], p1_out[1], z0), (p2_out[0], p2_out[1], z0),
        (p2_in[0], p2_in[1], z0), (p1_in[0], p1_in[1], z0),
        (p1_out[0], p1_out[1], z1), (p2_out[0], p2_out[1], z1),
        (p2_in[0], p2_in[1], z1), (p1_in[0], p1_in[1], z1)
    ]
    
    # 6 faces (quads)
    faces = [
        (0, 1, 5, 4), # Outer face
        (2, 3, 7, 6), # Inner face
        (0, 4, 7, 3), # Cap 1
        (1, 2, 6, 5), # Cap 2
        (0, 3, 2, 1), # Bottom
        (4, 5, 6, 7)  # Top
    ]
    
    return verts, faces
