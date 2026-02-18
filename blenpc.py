import click
import os
import sys
import json
import yaml
import platform
import subprocess
import time
import multiprocessing
from typing import Optional, List, Dict
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import config

def run_blender_task(input_data: Dict, input_file: str, output_file: str, preview: bool = False) -> Dict:
    """Helper to run a single Blender task."""
    with open(input_file, 'w') as f:
        json.dump(input_data, f)
        
    blender_cmd = [config.BLENDER_PATH]
    if not preview:
        blender_cmd.append("--background")
    
    blender_cmd.extend(["--python", "run_command.py", "--", input_file, output_file])
    
    try:
        subprocess.run(blender_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)
    return {"status": "error", "message": "Unknown error or no output produced"}

@click.group()
@click.version_option(version="5.1.0")
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose logging.")
@click.option('--config-file', type=click.Path(exists=True), help="Path to custom config file.")
@click.option('--blender-path', type=click.Path(exists=True), help="Custom path to Blender executable.")
def cli(verbose, config_file, blender_path):
    """BlenPC v5.1 - Procedural Building Generator for Blender 5.0.1"""
    if verbose:
        os.environ["MF_LOG_LEVEL"] = "DEBUG"
    if blender_path:
        os.environ["BLENDER_PATH"] = blender_path

@cli.command()
@click.option('--width', '-w', type=float, help="Building width in meters.")
@click.option('--depth', '-d', type=float, help="Building depth in meters.")
@click.option('--floors', '-f', type=int, help="Number of floors.")
@click.option('--seed', '-s', type=int, default=0, help="Random seed for deterministic generation.")
@click.option('--roof', '-r', type=click.Choice(['flat', 'gabled', 'hip', 'shed'], case_sensitive=False), default='flat', help="Roof type.")
@click.option('--output', '-o', type=click.Path(), default='./output', help="Output directory.")
@click.option('--spec', type=click.Path(exists=True), help="Path to YAML/JSON spec file.")
@click.option('--preview', is_flag=True, help="Open in Blender GUI after generation.")
def generate(width, depth, floors, seed, roof, output, spec, preview):
    """Generate a procedural building based on parameters or spec file."""
    
    spec_data = {}
    if spec:
        click.echo(f"Loading spec from {spec}...")
        with open(spec, 'r') as f:
            if spec.endswith(('.yaml', '.yml')):
                spec_data = yaml.safe_load(f)
            else:
                spec_data = json.load(f)
        
        b_spec = spec_data.get('building', spec_data)
        width = width or b_spec.get('width', 20.0)
        depth = depth or b_spec.get('depth', 16.0)
        floors = floors or b_spec.get('floors', 1)
        seed = seed or b_spec.get('seed', 0)
        roof = roof or b_spec.get('roof', {}).get('type', 'flat')
        output = output or b_spec.get('output', {}).get('directory', './output')
    else:
        width = width or 20.0
        depth = depth or 16.0
        floors = floors or 1

    click.echo(f"Generating building: {width}x{depth}, {floors} floors, Seed: {seed}, Roof: {roof}")
    
    input_data = {
        "command": "generate_building",
        "seed": seed,
        "spec": {
            "width": width, "depth": depth, "floors": floors, "roof": roof, "output_dir": output
        }
    }
    
    res = run_blender_task(input_data, f"gen_{seed}.json", f"out_{seed}.json", preview)
    
    if res.get("status") == "success":
        click.secho(f"Successfully generated building: {res['result']['glb_path']}", fg="green")
    else:
        click.secho(f"Error: {res.get('message')}", fg="red")

@cli.command()
@click.option('--spec', type=click.Path(exists=True), required=True, help="Path to batch YAML spec file.")
@click.option('--workers', '-w', type=int, default=multiprocessing.cpu_count(), help="Number of parallel workers.")
def batch(spec, workers):
    """Run batch production from a spec file."""
    click.echo(f"Starting batch production from {spec} with {workers} workers...")
    
    with open(spec, 'r') as f:
        spec_data = yaml.safe_load(f)
        
    batch_list = spec_data.get('batch', {}).get('buildings', [])
    if not batch_list:
        click.secho("No buildings found in batch spec.", fg="yellow")
        return
        
    common_output = spec_data.get('batch', {}).get('output', {}).get('directory', './output')
    
    tasks = []
    for i, b in enumerate(batch_list):
        seed = b.get('seed', 1000 + i)
        input_data = {
            "command": "generate_building",
            "seed": seed,
            "spec": {
                "width": b.get('width', 20.0),
                "depth": b.get('depth', 16.0),
                "floors": b.get('floors', 1),
                "roof": b.get('roof', {}).get('type', 'flat'),
                "output_dir": common_output
            }
        }
        tasks.append((input_data, f"batch_in_{seed}.json", f"batch_out_{seed}.json"))

    results = []
    with click.progressbar(length=len(tasks), label='Batch processing...') as bar:
        for task in tasks:
            res = run_blender_task(*task)
            results.append(res)
            bar.update(1)
            
    success_count = sum(1 for r in results if r.get('status') == 'success')
    click.echo(f"Batch completed: {success_count}/{len(tasks)} successful.")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--stats', is_flag=True, help="Show detailed statistics.")
def inspect(path, stats):
    """Inspect a GLB or Blend file for building/asset information."""
    click.echo(f"Inspecting: {path}")
    
    if path.endswith('.glb'):
        size = os.path.getsize(path) / 1024
        click.echo(f"  Format: GLB (Binary glTF)")
        click.echo(f"  Size: {size:.2f} KB")
    elif path.endswith('.blend'):
        click.echo(f"  Format: Blender Project")
    else:
        click.echo("  Format: Unknown")

@cli.command()
@click.option('--spec', type=click.Path(exists=True), help="Validate a spec file.")
@click.option('--registry', is_flag=True, help="Validate the entire asset registry.")
def validate(spec, registry):
    """Validate spec files or the asset registry."""
    if spec:
        click.echo(f"Validating spec: {spec}")
        try:
            with open(spec, 'r') as f:
                if spec.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            click.secho("✓ Spec is valid.", fg="green")
        except Exception as e:
            click.secho(f"✗ Spec validation failed: {e}", fg="red")
            
    if registry:
        click.echo("Validating registry...")
        if os.path.exists(config.INVENTORY_FILE):
            try:
                with open(config.INVENTORY_FILE, 'r') as f:
                    inv = json.load(f)
                click.secho(f"✓ Registry is valid. {len(inv.get('assets', {}))} assets registered.", fg="green")
            except Exception as e:
                click.secho(f"✗ Registry validation failed: {e}", fg="red")
        else:
            click.echo("Registry file not found.")

@click.group()
def registry():
    """Manage the asset registry (inventory)."""
    pass

@registry.command(name='list')
@click.option('--tags', help="Filter by tags.")
def list_assets(tags):
    """List all registered assets."""
    if os.path.exists(config.INVENTORY_FILE):
        with open(config.INVENTORY_FILE, 'r') as f:
            inv = json.load(f)
        
        assets = inv.get('assets', {})
        filter_tags = tags.split(',') if tags else []
        
        click.echo(f"Registry: {len(assets)} assets found.")
        for name, data in assets.items():
            asset_tags = data.get('tags', [])
            if not filter_tags or all(t in asset_tags for t in filter_tags):
                click.echo(f"  - {name} [{', '.join(asset_tags)}]")
    else:
        click.echo("Registry file not found.")

@registry.command(name='clean')
@click.option('--unused', is_flag=True, help="Clean unused assets from library.")
def clean_registry(unused):
    """Clean the registry and library."""
    click.echo("Cleaning registry...")
    # Implementation logic for cleaning unused assets

cli.add_command(registry)

@cli.command()
@click.argument('asset_type', type=click.Choice(['wall', 'door', 'window'], case_sensitive=False))
@click.option('--name', '-n', required=True, help="Asset name.")
@click.option('--length', '-l', type=float, help="Length (for walls).")
@click.option('--seed', '-s', type=int, default=0, help="Random seed.")
@click.option('--tags', '-t', help="Comma-separated tags.")
def create(asset_type, name, length, seed, tags):
    """Create a specific building asset (e.g., a wall)."""
    if asset_type == 'wall':
        if not length:
            click.echo("Error: --length is required for wall creation.", err=True)
            return
            
        input_data = {
            "command": "create_wall",
            "seed": seed,
            "asset": {
                "name": name, "dimensions": {"width": length},
                "tags": tags.split(',') if tags else ["arch_wall"]
            }
        }
        res = run_blender_task(input_data, "asset_in.json", "asset_out.json")
        if res.get("status") == "success":
            click.secho(f"Successfully created asset: {name}", fg="green")
        else:
            click.secho(f"Error: {res.get('message')}", fg="red")

@cli.command()
def version():
    """Display version information."""
    click.echo(f"blenpc v5.1.0")
    click.echo(f"Blender: {config.BLENDER_PATH}")
    click.echo(f"Python: {platform.python_version()}")
    click.echo(f"Platform: {platform.system()} {platform.release()}")

if __name__ == '__main__':
    cli()
