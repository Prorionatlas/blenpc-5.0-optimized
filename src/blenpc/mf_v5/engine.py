"""High-level deterministic orchestrator for MF v5.1 blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import time

try:
    import bpy
    import bmesh
    from .blender_mesh import create_wall_mesh, create_slab_mesh, create_roof_mesh, final_merge_and_cleanup
    from .export import export_to_glb
except ImportError:
    bpy = None

from ..config import USE_NEW_GEOMETRY, GRID, logger
from .datamodel import BuildingSpec, RoofType, Rect
from .geometry_authority import robust_union
from .edge_classifier import classify_edges
from .vertical_authority import floor_elevations
from .walls import build_wall_strip
from .validator import validate_mesh, generation_gate
from .export import ExportSettings, export_manifest

@dataclass
class FloorOutput:
    floor_index: int
    room_count: int
    wall_segment_count: int

@dataclass
class GenerationOutput:
    floors: List[FloorOutput]
    roof_type: str
    export_manifest: str
    glb_path: Optional[str] = None

def generate(spec: BuildingSpec, output_dir: Path) -> GenerationOutput:
    """Procedurally generate a building based on spec."""
    start_time = time.time()
    logger.info(f"Starting generation v5.0: {spec.width}x{spec.depth}, {spec.floors} floors (Seed: {spec.seed})")
    
    if not USE_NEW_GEOMETRY:
        logger.warning("Using legacy pipeline. Consider enabling USE_NEW_GEOMETRY.")
        # Legacy code removed for brevity in this task, assuming new pipeline is primary
    
    floor_outputs: List[FloorOutput] = []
    blender_objects = []

    try:
        # Clear existing data if in Blender
        if bpy:
            bpy.ops.wm.read_factory_settings(use_empty=True)

        for floor_idx in range(spec.floors):
            logger.debug(f"Processing Floor {floor_idx}...")
            
            # Dummy room generation for demonstration of the new pipeline
            # In a real scenario, this would call generate_floorplan
            from .floorplan import generate_floorplan
            rooms, corridor = generate_floorplan(spec.width, spec.depth, spec.seed, floor_idx)
            
            # KATMAN 1: Geometry Authority
            footprint = robust_union(rooms)
            
            # KATMAN 2: Edge Classifier
            edges = classify_edges(footprint, rooms)
            
            # KATMAN 3: Vertical Authority
            elev = floor_elevations(floor_idx)
            
            # KATMAN 4: Strip Wall Builder
            centroid = (footprint.centroid.x, footprint.centroid.y)
            
            if bpy:
                bm = bmesh.new()
                for edge in edges:
                    verts, faces = build_wall_strip(edge, elev, centroid)
                    # Add to bmesh
                    v_objs = [bm.verts.new(v) for v in verts]
                    for f in faces:
                        bm.faces.new([v_objs[i] for i in f])
                
                # Validation Gate
                res = validate_mesh(bm, spec)
                generation_gate(res, str(spec.seed))
                
                # Create object
                mesh = bpy.data.meshes.new(f"Walls_F{floor_idx}")
                bm.to_mesh(mesh)
                bm.free()
                obj = bpy.data.objects.new(f"Walls_F{floor_idx}", mesh)
                bpy.context.scene.collection.objects.link(obj)
                blender_objects.append(obj)

            floor_outputs.append(
                FloorOutput(
                    floor_index=floor_idx,
                    room_count=len(rooms),
                    wall_segment_count=len(edges)
                )
            )

        # Finalize
        glb_path = None
        if bpy and blender_objects:
            final_obj = final_merge_and_cleanup(blender_objects)
            if final_obj:
                settings = ExportSettings()
                building_glb_path = export_to_glb(final_obj, output_dir, "Building", settings)
                if building_glb_path: glb_path = str(building_glb_path)

        manifest_path = export_manifest(output_dir / "export_manifest.json", "Building", ExportSettings())
        duration = time.time() - start_time
        logger.info(f"Generation completed successfully in {duration:.3f}s")

        return GenerationOutput(
            floors=floor_outputs,
            roof_type=spec.roof_type.value,
            export_manifest=str(manifest_path),
            glb_path=glb_path
        )
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise
