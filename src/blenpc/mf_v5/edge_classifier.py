from enum import Enum, auto
from dataclasses import dataclass
from shapely.geometry import Polygon
from typing import List, Tuple
from .datamodel import Room
from .geometry_authority import quantize

class EdgeType(Enum):
    EXTERIOR = auto()
    INTERIOR = auto()

@dataclass
class ClassifiedEdge:
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    edge_type: EdgeType

def canonical_edge(p1, p2):
    """Direction-independent edge hash with quantized coordinates."""
    p1_q = (quantize(p1[0]), quantize(p1[1]))
    p2_q = (quantize(p2[0]), quantize(p2[1]))
    return tuple(sorted([p1_q, p2_q]))

from shapely.geometry import LineString

def classify_edges(footprint: Polygon, rooms: List[Room]) -> List[ClassifiedEdge]:
    """Identify which room edges are exterior vs interior.
    
    Uses Shapely's contains/covers for robust collinearity detection.
    """
    import shapely
    from ..config import GRID
    
    # Footprint boundary for containment checks
    # We use a small buffer to avoid precision issues with 'on the boundary'
    boundary = footprint.exterior
    
    result = []
    seen = set()
    
    for room in rooms:
        r = room.rect
        # Extract 4 edges from rectangle
        corners = [
            (r.min_x, r.min_y), (r.max_x, r.min_y),
            (r.max_x, r.max_y), (r.min_x, r.max_y)
        ]
        
        for i in range(4):
            p1, p2 = corners[i], corners[(i+1)%4]
            key = canonical_edge(p1, p2)
            
            if key in seen:
                continue # Shared wall - already added
            seen.add(key)
            
            # Create a line for this edge
            edge_line = LineString([p1, p2])
            
            # If the edge is on the footprint boundary, it's EXTERIOR
            # We use covers() on the boundary line
            if boundary.covers(edge_line):
                etype = EdgeType.EXTERIOR
            else:
                etype = EdgeType.INTERIOR
                
            result.append(ClassifiedEdge(p1, p2, etype))
            
    return result
