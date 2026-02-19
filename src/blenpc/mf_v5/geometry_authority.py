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
