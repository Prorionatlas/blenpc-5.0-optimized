from ..config import STORY_HEIGHT, WALL_HEIGHT
from dataclasses import dataclass

@dataclass(frozen=True)
class FloorElevations:
    """Standardized vertical coordinates for a floor."""
    base_z: float      # Floor top
    wall_top_z: float  # Wall top = Roof base
    slab_top_z: float  # Floor top + slab thickness (STORY_HEIGHT)

def floor_elevations(floor_idx: int) -> FloorElevations:
    """Calculate all Z coordinates for a specific floor index.
    
    KULLANIM KURALI:
    - roof.py -> floor_elevations(floor_count - 1).wall_top_z
    - walls.py -> floor_elevations(floor_idx).base_z ve .wall_top_z
    - BAŞKA YERDE height hesabı yapma!
    """
    base = floor_idx * STORY_HEIGHT
    wall_top = base + WALL_HEIGHT
    slab_top = base + STORY_HEIGHT
    return FloorElevations(base, wall_top, slab_top)
