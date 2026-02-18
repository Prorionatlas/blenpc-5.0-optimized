"""
Modular Wall System - Segment-based pre-cut architecture for BlenPC v5.2.0

This module implements a revolutionary wall system where:
- Walls are NOT single meshes
- Walls are segment lists (0.25m grid-aligned)
- Openings (doors/windows) are pre-cut (segments are blocked, not carved)
- No boolean operations (manifold-safe by design)

Key Concepts:
- Segment = 0.25m (meso grid unit) section of wall
- Opening = blocked segments (not generated)
- Slot = connection point for door/window asset
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import json

try:
    import bpy
    import bmesh
except ImportError:
    bpy = None
    bmesh = None

from ..engine.grid_pos import GridPos, meters_to_units, units_to_meters
from ..engine.grid_object import GridObjectMixin
from .. import config


@dataclass
class WallSegment:
    """
    A single segment of wall.
    
    Attributes:
        grid_pos: Position in grid space
        blocked: True if this segment is reserved for an opening
        segment_type: "wall" | "door_opening" | "window_opening"
    """
    grid_pos: GridPos
    blocked: bool = False
    segment_type: str = "wall"


@dataclass
class Opening:
    """
    Definition of a door or window opening in a wall.
    
    Attributes:
        opening_type: "door" | "window"
        center_x: Center position along wall (meters)
        width: Opening width (meters)
        height: Opening height (meters)
        sill_height: Height from floor to bottom of opening (meters)
    """
    opening_type: str  # "door" | "window"
    center_x: float
    width: float
    height: float
    sill_height: float = 0.0


@dataclass
class WallData(GridObjectMixin):
    """
    Complete wall data structure implementing IGridObject.
    
    Attributes:
        name: Unique wall identifier
        grid_pos: Position in grid space
        grid_size: Size in grid units (width, depth, height)
        snap_mode: Snap mode used
        segments: List of wall segments
        slots: List of opening slots (for door/window placement)
        tags: Classification tags
        meta: Additional metadata (AABB, dimensions, etc.)
    """
    name: str
    grid_pos: GridPos
    grid_size: Tuple[int, int, int]
    snap_mode: str
    segments: List[WallSegment] = field(default_factory=list)
    slots: List[Dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)


def build_wall(
    length: float,
    height: float,
    thickness: float = None,
    openings: Optional[List[Opening]] = None,
    name: str = "wall",
    seed: int = 0
) -> WallData:
    """
    Build a modular wall with segment-based pre-cut openings.
    
    Args:
        length: Wall length in meters
        height: Wall height in meters
        thickness: Wall thickness in meters (default: WALL_THICKNESS_BASE)
        openings: List of Opening objects (doors/windows)
        name: Wall identifier
        seed: Random seed for deterministic generation
    
    Returns:
        WallData object containing segments, slots, and metadata
    
    Example:
        >>> door = Opening("door", center_x=1.5, width=0.9, height=2.1)
        >>> window = Opening("window", center_x=3.5, width=1.2, height=1.4, sill_height=0.9)
        >>> wall = build_wall(5.0, 3.0, openings=[door, window])
        >>> len(wall.segments)
        20  # 5.0m / 0.25m = 20 segments
        >>> len(wall.slots)
        2   # door slot + window slot
    """
    if thickness is None:
        thickness = config.WALL_THICKNESS_BASE
    
    # Convert to grid coordinates (macro snap for walls)
    grid_pos = GridPos.from_meters(0, 0, 0, snap="macro")
    length_units = meters_to_units(length)
    height_units = meters_to_units(height)
    thickness_units = meters_to_units(thickness)
    
    grid_size = (length_units, thickness_units, height_units)
    
    # Calculate number of segments (meso grid = 0.25m)
    segment_size = config.SNAP_MODES["meso"]  # 10 units = 0.25m
    n_segments = length_units // segment_size
    
    # Initialize all segments as unblocked
    segments: List[WallSegment] = []
    for i in range(n_segments):
        seg_pos = GridPos(i * segment_size, 0, 0)
        segments.append(WallSegment(
            grid_pos=seg_pos,
            blocked=False,
            segment_type="wall"
        ))
    
    # Process openings and create slots
    slots: List[Dict] = []
    
    if openings:
        for idx, opening in enumerate(openings):
            # Convert opening dimensions to grid units
            center_units = meters_to_units(opening.center_x)
            width_units = meters_to_units(opening.width)
            half_width = width_units // 2
            
            # Calculate opening bounds
            start_unit = center_units - half_width
            end_unit = center_units + half_width
            
            # Block segments within opening
            start_seg = start_unit // segment_size
            end_seg = (end_unit + segment_size - 1) // segment_size
            
            for seg_idx in range(start_seg, min(end_seg, n_segments)):
                if 0 <= seg_idx < len(segments):
                    segments[seg_idx].blocked = True
                    segments[seg_idx].segment_type = f"{opening.opening_type}_opening"
            
            # Create slot for this opening
            slot_id = f"slot_{opening.opening_type}_{idx}"
            slot_pos_units = GridPos(
                center_units,
                thickness_units // 2,
                meters_to_units(opening.sill_height + opening.height / 2)
            )
            
            slot = {
                "id": slot_id,
                "type": f"{opening.opening_type}_opening",
                "grid_pos": slot_pos_units,
                "pos_meters": slot_pos_units.to_meters(),
                "size_meters": (opening.width, opening.height),
                "sill_height": opening.sill_height,
                "occupied": False,
                "required": True
            }
            slots.append(slot)
    
    # Calculate metadata
    meta = {
        "length_m": length,
        "height_m": height,
        "thickness_m": thickness,
        "segment_count": n_segments,
        "blocked_segments": sum(1 for s in segments if s.blocked),
        "opening_count": len(openings) if openings else 0,
        "aabb": {
            "min": [0.0, 0.0, 0.0],
            "max": [length, thickness, height]
        }
    }
    
    # Build tags
    tags = [
        "arch_wall",
        f"length_{int(length)}m",
        f"height_{int(height)}m",
        "modular_v2"
    ]
    
    return WallData(
        name=name,
        grid_pos=grid_pos,
        grid_size=grid_size,
        snap_mode="macro",
        segments=segments,
        slots=slots,
        tags=tags,
        meta=meta
    )


def generate_wall_mesh(wall_data: WallData) -> Optional[object]:
    """
    Generate Blender mesh from wall data (only unblocked segments).
    
    Args:
        wall_data: WallData object from build_wall()
    
    Returns:
        Blender object with mesh, or None if bpy not available
    
    Note:
        This function creates actual geometry in Blender.
        Blocked segments are NOT generated (pre-cut architecture).
    """
    if not bpy:
        raise ImportError("Blender 'bpy' module required for mesh generation")
    
    mesh = bpy.data.meshes.new(wall_data.name)
    obj = bpy.data.objects.new(wall_data.name, mesh)
    
    # Get scene collection
    if bpy.context.scene.collection:
        bpy.context.scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # Generate mesh for each unblocked segment
    segment_size_m = units_to_meters(config.SNAP_MODES["meso"])
    thickness_m = wall_data.meta["thickness_m"]
    height_m = wall_data.meta["height_m"]
    
    for segment in wall_data.segments:
        if segment.blocked:
            continue  # Skip blocked segments (pre-cut)
        
        # Get segment position in meters
        seg_x, seg_y, seg_z = segment.grid_pos.to_meters()
        
        # Create box for this segment
        # Vertices for a segment box (0.25m x thickness x height)
        verts = [
            (seg_x, 0, 0),
            (seg_x + segment_size_m, 0, 0),
            (seg_x + segment_size_m, thickness_m, 0),
            (seg_x, thickness_m, 0),
            (seg_x, 0, height_m),
            (seg_x + segment_size_m, 0, height_m),
            (seg_x + segment_size_m, thickness_m, height_m),
            (seg_x, thickness_m, height_m),
        ]
        
        # Create vertices
        bm_verts = [bm.verts.new(v) for v in verts]
        bm.verts.ensure_lookup_table()
        
        # Create faces (box)
        faces = [
            (0, 1, 2, 3),  # bottom
            (4, 5, 6, 7),  # top
            (0, 1, 5, 4),  # front
            (2, 3, 7, 6),  # back
            (0, 3, 7, 4),  # left
            (1, 2, 6, 5),  # right
        ]
        
        for face_indices in faces:
            try:
                bm.faces.new([bm_verts[i] for i in face_indices])
            except ValueError:
                pass  # Face already exists
    
    # Merge overlapping vertices
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    
    # Write to mesh
    bm.to_mesh(mesh)
    bm.free()
    
    # Store metadata in object custom properties
    obj["wall_data"] = json.dumps({
        "segments": len(wall_data.segments),
        "slots": len(wall_data.slots),
        "meta": wall_data.meta
    })
    
    if wall_data.slots:
        obj["slots_json"] = json.dumps(wall_data.slots, default=str)
    
    # Mark as asset
    obj.asset_mark()
    
    return obj


def wall_to_json(wall_data: WallData) -> str:
    """
    Serialize wall data to JSON.
    
    Args:
        wall_data: WallData object
    
    Returns:
        JSON string representation
    """
    # Convert slots to serializable format
    serializable_slots = []
    for slot in wall_data.slots:
        slot_copy = slot.copy()
        if "grid_pos" in slot_copy and hasattr(slot_copy["grid_pos"], "to_tuple"):
            slot_copy["grid_pos"] = slot_copy["grid_pos"].to_tuple()
        serializable_slots.append(slot_copy)
    
    # Handle hierarchical children in meta
    meta_copy = wall_data.meta.copy()
    if "children" in meta_copy:
        children = meta_copy["children"]
        serializable_children = {
            "doors": [],
            "windows": []
        }
        
        from .door import door_to_json
        from .window import window_to_json
        
        for door in children.get("doors", []):
            serializable_children["doors"].append(json.loads(door_to_json(door)))
        for window in children.get("windows", []):
            serializable_children["windows"].append(json.loads(window_to_json(window)))
            
        meta_copy["children"] = serializable_children
    
    data = {
        "name": wall_data.name,
        "grid_pos": wall_data.grid_pos.to_tuple(),
        "grid_size": wall_data.grid_size,
        "snap_mode": wall_data.snap_mode,
        "segments": [
            {
                "grid_pos": seg.grid_pos.to_tuple(),
                "blocked": seg.blocked,
                "type": seg.segment_type
            }
            for seg in wall_data.segments
        ],
        "slots": serializable_slots,
        "tags": wall_data.tags,
        "meta": meta_copy
    }
    return json.dumps(data, indent=2)


# Convenience function for backward compatibility
def create_engineered_wall(name: str, length: float, seed: int = 0):
    """
    Legacy function - creates a simple wall with one window slot.
    
    This function maintains backward compatibility with the old API
    while using the new segment-based system internally.
    """
    # Create a wall with one window opening at golden ratio position
    from .wall import golden_split, make_rng
    
    rng = make_rng(seed, "wall_slots")
    window_x = golden_split(length, rng)
    
    window = Opening(
        opening_type="window",
        center_x=window_x,
        width=config.WINDOW_DEFAULT_WIDTH,
        height=config.WINDOW_DEFAULT_HEIGHT,
        sill_height=config.WINDOW_SILL_HEIGHT_DEFAULT
    )
    
    wall_data = build_wall(
        length=length,
        height=config.STORY_HEIGHT,
        openings=[window],
        name=name,
        seed=seed
    )
    
    if bpy:
        return generate_wall_mesh(wall_data), wall_data.slots
    else:
        return wall_data, wall_data.slots



def build_wall_composed(
    wall_spec: Dict,
    opening_specs: Optional[List[Dict]] = None,
    name: str = "composed_wall",
    seed: int = 0
) -> Dict:
    """
    Build a complete wall with doors and windows in one operation.
    
    This is the high-level API that combines wall, door, and window
    generation into a single command.
    
    Args:
        wall_spec: Wall specification dict with keys:
            - length: float (meters)
            - height: float (meters)
            - thickness: float (meters, optional)
            - material: str (optional)
        opening_specs: List of opening specification dicts with keys:
            - type: "door" | "window"
            - position: dict with "x_ratio" (0.0-1.0) or "x_meters"
            - style: door/window style (optional)
            - material: door leaf / window frame material (optional)
            - ... (other door/window specific params)
        name: Composed wall identifier
        seed: Random seed
    
    Returns:
        Dict containing:
        - wall_data: WallData object
        - door_objects: List of DoorData objects
        - window_objects: List of WindowData objects
        - scene_grid: SceneGrid with all objects placed
    
    Example:
        >>> spec = {
        ...     "wall": {"length": 5.0, "height": 3.0},
        ...     "openings": [
        ...         {"type": "door", "position": {"x_ratio": 0.3}, "style": "single"},
        ...         {"type": "window", "position": {"x_ratio": 0.8}, "style": "standard"}
        ...     ]
        ... }
        >>> result = build_wall_composed(**spec, name="living_room_wall")
        >>> result["wall_data"].meta["opening_count"]
        2
    """
    from .door import build_door
    from .window import build_window
    from ..engine.grid_manager import SceneGrid
    
    # Parse wall spec
    length = wall_spec["length"]
    height = wall_spec.get("height", config.STORY_HEIGHT)
    thickness = wall_spec.get("thickness", config.WALL_THICKNESS_BASE)
    
    # Calculate opening positions and create Opening objects
    openings = []
    door_objects = []
    window_objects = []
    
    if opening_specs:
        for idx, opening_spec in enumerate(opening_specs):
            opening_type = opening_spec["type"]
            
            # Calculate position
            if "x_ratio" in opening_spec["position"]:
                center_x = length * opening_spec["position"]["x_ratio"]
            elif "x_meters" in opening_spec["position"]:
                center_x = opening_spec["position"]["x_meters"]
            else:
                raise ValueError("Opening position must have 'x_ratio' or 'x_meters'")
            
            if opening_type == "door":
                # Get door style and dimensions
                door_style = opening_spec.get("style", "single")
                door_dims = config.DOOR_STANDARDS[door_style]
                
                # Create Opening for wall
                opening = Opening(
                    opening_type="door",
                    center_x=center_x,
                    width=door_dims["w"],
                    height=door_dims["h"],
                    sill_height=0.0
                )
                openings.append(opening)
                
                # Create Door object
                door = build_door(
                    style=door_style,
                    material=opening_spec.get("material", "wood"),
                    swing=opening_spec.get("swing", "inward_left"),
                    name=f"{name}_door_{idx}",
                    position=(center_x - door_dims["w"] / 2, 0.0, 0.0)
                )
                door_objects.append(door)
                
            elif opening_type == "window":
                # Get window style and dimensions
                window_style = opening_spec.get("style", "standard")
                window_dims = config.WINDOW_STANDARDS[window_style]
                
                # Create Opening for wall
                opening = Opening(
                    opening_type="window",
                    center_x=center_x,
                    width=window_dims["w"],
                    height=window_dims["h"],
                    sill_height=window_dims["sill"]
                )
                openings.append(opening)
                
                # Create Window object
                window = build_window(
                    style=window_style,
                    frame_material=opening_spec.get("frame_material", "wood"),
                    glass_inner=opening_spec.get("glass_inner", "transparent"),
                    glass_outer=opening_spec.get("glass_outer", "transparent"),
                    has_sill=opening_spec.get("has_sill", True),
                    name=f"{name}_window_{idx}",
                    position=(center_x - window_dims["w"] / 2, 0.0, window_dims["sill"])
                )
                window_objects.append(window)
    
    # Build wall with openings
    wall_data = build_wall(
        length=length,
        height=height,
        thickness=thickness,
        openings=openings,
        name=name,
        seed=seed
    )
    
    # Create scene grid and place all objects
    scene = SceneGrid()
    
    # Place wall
    if not scene.place(wall_data):
        raise RuntimeError(f"Failed to place wall '{name}'")
    
    # Hierarchical Placement: Doors and windows are children of the wall.
    # They are NOT placed in the SceneGrid separately to avoid collision.
    # Instead, they are stored in the wall's metadata.
    wall_data.meta["children"] = {
        "doors": door_objects,
        "windows": window_objects
    }
    
    return {
        "wall_data": wall_data,
        "door_objects": door_objects,
        "window_objects": window_objects,
        "scene_grid": scene,
        "meta": {
            "total_objects": 1,  # Only the wall is in the grid
            "child_count": len(door_objects) + len(window_objects),
            "wall_length": length,
            "opening_count": len(openings)
        }
    }


def composed_wall_to_json(composed_data: Dict) -> str:
    """
    Serialize composed wall data to JSON.
    
    Args:
        composed_data: Dict from build_wall_composed()
    
    Returns:
        JSON string representation
    """
    data = {
        "wall": json.loads(wall_to_json(composed_data["wall_data"])),
        "doors": [json.loads(d.to_json()) if hasattr(d, 'to_json') else {} for d in composed_data["door_objects"]],
        "windows": [json.loads(w.to_json()) if hasattr(w, 'to_json') else {} for w in composed_data["window_objects"]],
        "scene_stats": composed_data["scene_grid"].get_stats(),
        "meta": composed_data["meta"]
    }
    return json.dumps(data, indent=2)
