import sys
import json
import os
import time
import traceback
from pathlib import Path

# Expert Fix: Add src/ to path so 'blenpc' can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

try:
    import bpy
except ImportError:
    bpy = None

# Expert Fix: Absolute imports from the package
from blenpc import config
from blenpc.atoms.wall import create_engineered_wall
from blenpc.engine.inventory_manager import InventoryManager
from blenpc.mf_v5.engine import generate as generate_building
from blenpc.mf_v5.datamodel import BuildingSpec, RoofType

def run():
    input_file = None
    output_file = None
    try:
        if '--' in sys.argv:
            args = sys.argv[sys.argv.index('--') + 1:]
            if len(args) >= 2:
                input_file = args[0]
                output_file = args[1]
            else:
                raise ValueError("Incorrect arguments. Usage: blender --python run_command.py -- <in> <out>")
        else:
            raise ValueError("Missing -- separator")
    except Exception as e:
        print(f"CLI Error: {e}")
        sys.exit(1)

    if not os.path.exists(input_file):
        result = {"status": "error", "message": f"Input file not found: {input_file}"}
    else:
        try:
            with open(input_file, 'r') as f:
                command_data = json.load(f)
            
            cmd = command_data.get("command")
            seed = command_data.get("seed", 0)
            
            if cmd == "create_wall":
                wall_data = command_data.get("asset", {})
                name = wall_data.get("name", "GenWall")
                length = wall_data.get("dimensions", {}).get("width", 4.0)
                
                if not bpy:
                    raise ImportError("Blender 'bpy' module is not available.")
                
                obj, slots = create_engineered_wall(name, length, seed)
                
                asset_info = {
                    "name": name,
                    "tags": wall_data.get("tags", ["arch_wall"]),
                    "dimensions": {"width": length, "height": config.STORY_HEIGHT, "depth": config.WALL_THICKNESS_BASE},
                    "slots": slots,
                    "blend_file": os.path.join(config.LIBRARY_DIR, f"{name}.blend"),
                    "seed": seed
                }
                InventoryManager.register_asset(asset_info)
                
                os.makedirs(config.LIBRARY_DIR, exist_ok=True)
                lib_path = os.path.join(config.LIBRARY_DIR, f"{name}.blend")
                bpy.ops.wm.save_as_mainfile(filepath=lib_path)
                
                result = {"status": "success", "result": {"asset_name": name, "blend_file": lib_path}}
                
            elif cmd == "generate_building":
                spec_data = command_data.get("spec", {})
                roof_str = spec_data.get("roof", "flat").upper()
                roof_type = getattr(RoofType, roof_str, RoofType.FLAT)
                
                spec = BuildingSpec(
                    width=spec_data.get("width", 20.0),
                    depth=spec_data.get("depth", 16.0),
                    floors=spec_data.get("floors", 1),
                    seed=seed,
                    roof_type=roof_type
                )
                
                out_path = Path(spec_data.get("output_dir", "./output"))
                out_path.mkdir(parents=True, exist_ok=True)
                
                gen_out = generate_building(spec, out_path)
                
                result = {
                    "status": "success",
                    "result": {
                        "glb_path": str(gen_out.glb_path),
                        "manifest": gen_out.export_manifest
                    }
                }
            else:
                result = {"status": "error", "message": f"Unknown command: {cmd}"}
                
        except Exception as e:
            result = {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    run()
