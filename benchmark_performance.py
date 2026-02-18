import sys
import os
import time
import json
from pathlib import Path
from dataclasses import asdict

# Add the current directory to sys.path
sys.path.append(os.getcwd())

import bpy
from mf_v5 import BuildingSpec, RoofType, generate

def get_mesh_stats():
    """Get vertex and face counts of the final generated building."""
    obj = bpy.data.objects.get("Building_Final")
    if obj and obj.type == 'MESH':
        return {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons)
        }
    return {"vertices": 0, "faces": 0}

def run_benchmark(width, depth, floors, name):
    print(f"--- Benchmarking: {name} ({width}x{depth}, {floors} floors) ---")
    
    # Clear Blender scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    output_dir = Path(f"./benchmark_output/{name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    spec = BuildingSpec(
        width=width,
        depth=depth,
        floors=floors,
        seed=42,
        roof_type=RoofType.HIP
    )
    
    start_time = time.time()
    output = generate(spec, output_dir)
    end_time = time.time()
    
    gen_duration = end_time - start_time
    stats = get_mesh_stats()
    
    result = {
        "name": name,
        "spec": {
            "width": width,
            "depth": depth,
            "floors": floors
        },
        "performance": {
            "total_time_sec": round(gen_duration, 4),
            "vertices": stats["vertices"],
            "faces": stats["faces"]
        },
        "floor_details": [asdict(f) for f in output.floors]
    }
    
    print(f"Done in {gen_duration:.4f}s. Verts: {stats['vertices']}, Faces: {stats['faces']}")
    return result

def main():
    benchmarks = [
        (10.0, 10.0, 1, "Small_1F"),
        (20.0, 16.0, 2, "Medium_2F"),
        (30.0, 24.0, 5, "Large_5F"),
        (40.0, 32.0, 10, "Extreme_10F")
    ]
    
    all_results = []
    for w, d, f, name in benchmarks:
        res = run_benchmark(w, d, f, name)
        all_results.append(res)
    
    with open("benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=4)
    
    print("\nAll benchmarks completed. Results saved to benchmark_results.json")

if __name__ == "__main__":
    main()
