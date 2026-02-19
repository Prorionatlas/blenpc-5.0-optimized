from ..config import GRID
from .datamodel import Rect

def quantize(value: float) -> float:
    """Single coordinate snap. All pipeline uses this function."""
    return round(value / GRID) * GRID

def quantize_room(room_rect: Rect) -> Rect:
    """Quantize all coordinates of a room rectangle."""
    return Rect(
        min_x=quantize(room_rect.min_x),
        min_y=quantize(room_rect.min_y),
        max_x=quantize(room_rect.max_x),
        max_y=quantize(room_rect.max_y)
    )

import shapely
from shapely.ops import unary_union
from shapely.geometry import box, Polygon
from typing import List
from .datamodel import Room

def robust_union(rooms: List[Room]) -> Polygon:
    """Combine room rectangles into a single footprint polygon.
    
    Handles touching rooms via set_precision and buffer fallback.
    """
    # Step 1: Quantize (mandatory, first)
    rooms_q = [quantize_room(r.rect) for r in rooms]
    
    # Step 2: set_precision with snap (kills float drift)
    polys = [
        shapely.set_precision(box(r.min_x, r.min_y, r.max_x, r.max_y), GRID)
        for r in rooms_q
    ]
    
    # Step 3: Union
    merged = unary_union(polys)
    
    # Step 4: MultiPolygon fallback via buffer
    if merged.geom_type != 'Polygon':
        EPSILON = GRID * 0.4
        polys_buf = [p.buffer(EPSILON, join_style='mitre') for p in polys]
        merged = unary_union(polys_buf).buffer(-EPSILON, join_style='mitre')
        
    if merged.geom_type != 'Polygon':
        raise ValueError(f'Union failed: {merged.geom_type}. Room layout may be invalid.')
        
    return merged
