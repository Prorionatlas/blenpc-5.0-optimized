from dataclasses import dataclass
from typing import List, Tuple, Optional
from shapely.geometry import box, Polygon
from .datamodel import Room, Rect
from .geometry_authority import MICRO_UNIT

@dataclass
class CollisionResult:
    """Result of a collision check."""
    has_collision: bool
    overlap_area: float = 0.0
    conflicting_ids: List[int] = None

class CollisionEngine:
    """Detects and prevents spatial conflicts in building layouts."""
    
    def __init__(self, rooms: List[Room]):
        self.rooms = rooms
        self.polygons = {
            room.id: box(room.rect.min_x, room.rect.min_y, room.rect.max_x, room.rect.max_y)
            for room in rooms
        }

    def check_self_collisions(self) -> List[CollisionResult]:
        """Check for any overlapping rooms within the current layout."""
        results = []
        ids = list(self.polygons.keys())
        
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                id1, id2 = ids[i], ids[j]
                p1, p2 = self.polygons[id1], self.polygons[id2]
                
                # Small overlap tolerance for integer grid precision
                overlap = p1.intersection(p2)
                if overlap.area > (MICRO_UNIT * MICRO_UNIT * 0.1):
                    results.append(CollisionResult(
                        has_collision=True,
                        overlap_area=overlap.area,
                        conflicting_ids=[id1, id2]
                    ))
        return results

    def can_place_room(self, new_room_rect: Rect, exclude_ids: Optional[List[int]] = None) -> bool:
        """Check if a new room can be placed without colliding with existing ones."""
        if exclude_ids is None:
            exclude_ids = []
            
        new_poly = box(new_room_rect.min_x, new_room_rect.min_y, new_room_rect.max_x, new_room_rect.max_y)
        
        for rid, poly in self.polygons.items():
            if rid in exclude_ids:
                continue
                
            overlap = new_poly.intersection(poly)
            if overlap.area > (MICRO_UNIT * MICRO_UNIT * 0.1):
                return False
        return True

    @staticmethod
    def validate_layout(rooms: List[Room]) -> Tuple[bool, str]:
        """Static helper to validate an entire room layout."""
        engine = CollisionEngine(rooms)
        collisions = engine.check_self_collisions()
        
        if collisions:
            msg = f"LAYOUT_CONFLICT: Detected {len(collisions)} overlapping areas."
            for c in collisions:
                msg += f"\n- Overlap: {c.overlap_area:.4f}m2 between IDs {c.conflicting_ids}"
            return False, msg
            
        return True, "LAYOUT_VALID"
