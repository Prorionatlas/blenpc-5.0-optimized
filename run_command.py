import sys
import json
import os
import time
import bpy
import traceback
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Use absolute imports
from atoms.wall import create_engineered_wall
from engine.inventory_manager import InventoryManager
from mf_v5.engine import generate as generate_building
from mf_v5.datamodel import BuildingSpec, RoofType
import config

def run():
    input_file = None
    output_file = None
    try:
        if '--' in sys.argv:
            args = sys.argv[sys.argv.index('--') + 1:]
            if len(args) == 2:
                input_file = args[0]
                output_file = args[1]
            else:
                raise ValueError("Incorrect number of arguments after --")
        else:
            raise ValueError("Missing -- separator for arguments")
    except (ValueError, IndexError) as e:
        result = {"status": "error", "message": f"CLI Argument Error: {e}. Usage: blender --background --python run_command.py -- <input.json> <output.json>"}
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        sys.exit(1)

    if not os.path.exists(input_file):
        result = {"status": "error", "message": f"Input file not found: {input_file}"}
    else:
        try:
            with open(input_file, 'r') as f:
                command_data = json.load(f)
            
            # VALIDATE STRUCTURE
            if "command" not in command_data:
                raise ValueError("Missing 'command' field in input JSON")
            
            cmd = command_data.get("command")
            seed = command_data.get("seed", 0)
            
            if cmd == "create_wall":
                wall_data = command_data.get("asset", {})
                if not wall_data:
                    raise ValueError("Missing 'asset' field for create_wall command")
                
                name = wall_data.get("name", "GenWall")
                dimensions = wall_data.get("dimensions", {})
                length = dimensions.get("width", 4.0)
                
                # VALIDATE DIMENSIONS
                if length <= 0 or length > 100:
                    raise ValueError(f"Invalid wall length: {length}. Must be between 0 and 100 meters")
                
                # Create engineered mesh with slots
                obj, slots = create_engineered_wall(name, length, seed)
                
                # Register in inventory with slots
                asset_info = {
                    "name": name,
                    "tags": wall_data.get("tags", ["arch_wall"]),
                    "dimensions": {"width": length, "height": 3.0, "depth": 0.2},
                    "slots": slots,
                    "blend_file": os.path.join(config.LIBRARY_DIR, f"{name}.blend"),
                    "seed": seed
                }
                InventoryManager.register_asset(asset_info)
                
                # Save
                os.makedirs(config.LIBRARY_DIR, exist_ok=True)
                lib_path = os.path.join(config.LIBRARY_DIR, f"{name}.blend")
                bpy.ops.wm.save_as_mainfile(filepath=lib_path)
                
                result = {
                    "status": "success",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "result": {"asset_name": name, "slots_count": len(slots), "blend_file": lib_path}
                }
            elif cmd == "generate_building":
                spec_data = command_data.get("spec", {})
                width = spec_data.get("width", 20.0)
                depth = spec_data.get("depth", 16.0)
                floors = spec_data.get("floors", 1)
                roof_str = spec_data.get("roof", "flat").upper()
                output_dir = spec_data.get("output_dir", "./output")
                
                roof_type = getattr(RoofType, roof_str, RoofType.FLAT)
                
                spec = BuildingSpec(
                    width=width,
                    depth=depth,
                    floors=floors,
                    seed=seed,
                    roof_type=roof_type
                )
                
                out_path = Path(output_dir)
                out_path.mkdir(parents=True, exist_ok=True)
                
                gen_out = generate_building(spec, out_path)
                
                result = {
                    "status": "success",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "result": {
                        "glb_path": gen_out.glb_path,
                        "manifest": gen_out.export_manifest,
                        "floors": [f.__dict__ for f in gen_out.floors]
                    }
                }
            else:
                result = {"status": "error", "message": f"Unknown command: {cmd}"}
                
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
        except ValueError as e:
            result = {"status": "error", "message": f"Validation error: {e}"}
        except IOError as e:
            result = {"status": "error", "message": f"File I/O error: {e}"}
        except Exception as e:
            result = {
                "status": "error",
                "message": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }

    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        # If output_file could not be determined, print error to stderr
        print(json.dumps(result, indent=2), file=sys.stderr)

if __name__ == "__main__":
    run()
