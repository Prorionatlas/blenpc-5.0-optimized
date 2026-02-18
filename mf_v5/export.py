"""Godot-oriented export settings and manifest generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    import bpy
except ImportError:
    bpy = None

@dataclass(frozen=True)
class ExportSettings:
    format: str = "GLTF2"
    y_up: bool = True
    apply_modifiers: bool = True
    apply_scale: bool = True
    selected_only: bool = True
    collider_suffix: str = "-col"
    navmesh_collection: str = "MF_Navmesh"

def export_manifest(output_path: Path, building_name: str, settings: ExportSettings) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, object] = {
        "building": f"{building_name}.glb",
        "collider": f"{building_name}{settings.collider_suffix}.glb",
        "navmesh": f"{building_name}_navmesh.glb",
        "settings": settings.__dict__,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path

def export_to_glb(output_dir: Path, building_name: str, settings: ExportSettings = ExportSettings()):
    """Actual GLB export using bpy.ops."""
    if bpy is None:
        return None
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export main building
    # Assuming the main building is selected
    building_path = output_dir / f"{building_name}.glb"
    
    bpy.ops.export_scene.gltf(
        filepath=str(building_path),
        export_format='GLB',
        use_selection=settings.selected_only,
        export_yup=settings.y_up,
        export_apply=settings.apply_modifiers,
    )
    
    # Export collider (duplicate of building with suffix)
    collider_path = output_dir / f"{building_name}{settings.collider_suffix}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(collider_path),
        export_format='GLB',
        use_selection=settings.selected_only,
        export_yup=settings.y_up,
        export_apply=settings.apply_modifiers,
    )
    
    return building_path, collider_path
