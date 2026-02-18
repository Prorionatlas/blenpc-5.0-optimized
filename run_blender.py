import sys
import os
from pathlib import Path

# Add the current directory to sys.path so we can import mf_v5
sys.path.append(os.getcwd())

from mf_v5 import BuildingSpec, RoofType, generate

def main():
    # Define output directory
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    # Define building spec
    spec = BuildingSpec(
        width=20.0,
        depth=16.0,
        floors=2,
        seed=42,
        roof_type=RoofType.HIP
    )
    
    print(f"Generating building with spec: {spec}")
    output = generate(spec, output_dir)
    
    print("Generation complete!")
    print(f"Manifest: {output.export_manifest}")
    print(f"GLB Path: {output.glb_path}")
    
    for floor in output.floors:
        print(f"Floor {floor.floor_index}: {floor.room_count} rooms, {floor.wall_segment_count} wall segments")

if __name__ == "__main__":
    main()
