"""High-level deterministic orchestrator for MF v5.1 blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    import bpy
    from .blender_mesh import create_wall_mesh, create_slab_mesh, create_roof_mesh, final_merge_and_cleanup
    from .export import export_to_glb
except ImportError:
    bpy = None

from .adjacency import build_adjacency, corridor_facing_walls
from .cleanup import dedupe_segments, remove_zero_length_segments
from .datamodel import BuildingSpec, RoofType, Rect
from .doors import carve_doors, corridor_door_openings
from .export import ExportSettings, export_manifest
from .floorplan import generate_floorplan
from .merge import default_merge_plan, summarize_cleanup
from .roof import build_roof
from .slabs import build_floor_ceiling_slabs, build_navmesh_slabs
from .walls import build_room_wall_segments


@dataclass
class FloorOutput:
    floor_index: int
    room_count: int
    adjacency: Dict[int, Dict[str, int | None]]
    wall_segment_count: int
    door_count: int


@dataclass
class GenerationOutput:
    floors: List[FloorOutput]
    roof_type: str
    cleanup: Dict[str, object]
    export_manifest: str
    glb_path: Optional[str] = None


def generate(spec: BuildingSpec, output_dir: Path) -> GenerationOutput:
    floor_outputs: List[FloorOutput] = []
    top_footprint = None
    top_z = 0.0

    # For Blender rendering
    blender_objects = []

    for floor_idx in range(spec.floors):
        rooms, corridor = generate_floorplan(spec.width, spec.depth, spec.seed, floor_idx)
        adjacency = build_adjacency(rooms)
        wall_segments_by_room = build_room_wall_segments(rooms)
        corridor_faces = corridor_facing_walls(rooms, corridor)
        room_rect_lookup = {
            r.id: (r.rect.min_x, r.rect.min_y, r.rect.max_x, r.rect.max_y) for r in rooms
        }
        openings = corridor_door_openings(corridor_faces, room_rect_lookup)
        carved = carve_doors(wall_segments_by_room, openings)

        merged_walls = [seg for segs in carved.values() for seg in segs]
        merged_walls = dedupe_segments(remove_zero_length_segments(merged_walls))
        
        floor_z_offset = floor_idx * 3.2
        
        slabs = build_floor_ceiling_slabs(rooms, floor_idx)
        
        if bpy:
            # Create meshes in Blender
            wall_obj = create_wall_mesh(merged_walls, f"Walls_F{floor_idx}")
            wall_obj.location.z = floor_z_offset
            blender_objects.append(wall_obj)
            
            slab_obj = create_slab_mesh(slabs, f"Slabs_F{floor_idx}")
            # Slab Z is already calculated in slabs.py, but we might need to double check
            blender_objects.append(slab_obj)

        if rooms:
            min_x = min(r.rect.min_x for r in rooms)
            min_y = min(r.rect.min_y for r in rooms)
            max_x = max(r.rect.max_x for r in rooms)
            max_y = max(r.rect.max_y for r in rooms)
            top_footprint = (min_x, min_y, max_x, max_y)
            top_z = floor_idx * 3.2 + 3.2

        floor_outputs.append(
            FloorOutput(
                floor_index=floor_idx,
                room_count=len(rooms),
                adjacency=adjacency,
                wall_segment_count=len(merged_walls),
                door_count=len(openings),
            )
        )

    if top_footprint:
        roof_rect = Rect(*top_footprint)
        roof_geo = build_roof(roof_rect, top_z, spec.roof_type)
        if bpy and roof_geo:
            roof_obj = create_roof_mesh(roof_geo, "Roof")
            blender_objects.append(roof_obj)

    glb_path = None
    if bpy and blender_objects:
        final_obj = final_merge_and_cleanup(blender_objects)
        if final_obj:
            settings = ExportSettings()
            paths = export_to_glb(output_dir, "Building", settings)
            if paths:
                glb_path = str(paths[0])

    settings = ExportSettings()
    manifest_path = export_manifest(output_dir / "export_manifest.json", "Building", settings)

    return GenerationOutput(
        floors=floor_outputs,
        roof_type=spec.roof_type.value,
        cleanup=summarize_cleanup(default_merge_plan()),
        export_manifest=str(manifest_path),
        glb_path=glb_path
    )
