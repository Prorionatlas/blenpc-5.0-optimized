import pytest
from blenpc.mf_v5.vertical_authority import floor_elevations

def test_floor_elevations():
    # Based on config: STORY_HEIGHT=3.2, WALL_HEIGHT=3.0
    # Floor 0
    elev0 = floor_elevations(0)
    assert elev0.base_z == 0.0
    assert elev0.wall_top_z == 3.0
    assert elev0.slab_top_z == 3.2
    
    # Floor 1
    elev1 = floor_elevations(1)
    assert elev1.base_z == 3.2
    assert elev1.wall_top_z == 6.2
    assert elev1.slab_top_z == 6.4
