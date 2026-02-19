from ..config import GRID, MICRO_UNIT
from .datamodel import Rect
import shapely
from shapely.ops import unary_union
from shapely.geometry import box, Polygon
from typing import List
from .datamodel import Room

def to_int_grid(value: float) -> int:
    """Convert float coordinate to integer grid units (1 unit = MICRO_UNIT)."""
    return int(round(value / MICRO_UNIT))

def from_int_grid(int_value: int) -> float:
    """Convert integer grid units back to float meters."""
    return int_value * MICRO_UNIT

def quantize(value: float) -> float:
    """Snap float to the nearest MICRO_UNIT (Integer Grid Base)."""
    return from_int_grid(to_int_grid(value))

def quantize_room(room_rect: Rect) -> Rect:
    """Quantize all coordinates of a room rectangle to the Integer Grid."""
    return Rect(
        min_x=quantize(room_rect.min_x),
        min_y=quantize(room_rect.min_y),
        max_x=quantize(room_rect.max_x),
        max_y=quantize(room_rect.max_y)
    )

def robust_union(rooms: List[Room]) -> Polygon:
    """Combine room rectangles into a single footprint polygon using Integer Grid precision.
    
    v5.2.0: Uses MICRO_UNIT precision to eliminate float drift.
    """
    if not rooms:
        # Avoid GEOSException: getX called on empty Point by returning a valid empty state or handling early
        raise ValueError("Cannot perform union on empty room list.")

    # Step 1: Quantize (mandatory, first)
    rooms_q = [quantize_room(r.rect) for r in rooms]
    
    # Step 2: set_precision with MICRO_UNIT (kills float drift)
    polys = []
    for r in rooms_q:
        # Ensure we don't create zero-area boxes
        if r.max_x > r.min_x and r.max_y > r.min_y:
            p = box(r.min_x, r.min_y, r.max_x, r.max_y)
            polys.append(shapely.set_precision(p, MICRO_UNIT))
    
    if not polys:
        raise ValueError("No valid rooms to union.")

    # Step 3: Union
    merged = unary_union(polys)
    
    # Step 4: MultiPolygon fallback via buffer (if rooms are touching but GEOS misses it)
    if merged.geom_type != 'Polygon':
        # Smallest possible overlap in the integer grid
        EPSILON = MICRO_UNIT * 0.5 
        polys_buf = [p.buffer(EPSILON, join_style='mitre') for p in polys]
        merged = unary_union(polys_buf).buffer(-EPSILON, join_style='mitre')
        
    if merged.geom_type != 'Polygon':
        # Final attempt: slightly more aggressive snap
        merged = shapely.set_precision(merged, GRID)
        
    if merged.geom_type != 'Polygon' and merged.geom_type != 'MultiPolygon':
        raise ValueError(f'Union failed: {merged.geom_type}. Room layout may be invalid.')
        
    return merged
