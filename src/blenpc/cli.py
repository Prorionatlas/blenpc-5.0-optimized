import click
import os
import sys
import json
import yaml
import platform
import subprocess
from typing import Optional, List, Dict
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.theme import Theme

# Define a professional, industrial theme
INDUSTRIAL_THEME = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold white",
    "header": "bold white",
    "label": "bold white",
    "value": "dim white",
    "border": "dim white"
})

console = Console(theme=INDUSTRIAL_THEME)

# Expert Fix: Add src/ to path for CLI to find the blenpc package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from blenpc import config

def run_blender_task(input_data: Dict, preview: bool = False) -> Dict:
    """Helper to run a single Blender task using the standardized run_command.py."""
    input_file = f"temp_in_{os.getpid()}.json"
    output_file = f"temp_out_{os.getpid()}.json"
    
    with open(input_file, 'w') as f:
        json.dump(input_data, f)
        
    run_cmd_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_command.py")
    
    blender_path = os.environ.get("BLENDER_PATH", config.BLENDER_PATH)
    blender_cmd = [blender_path]
    if not preview:
        blender_cmd.append("--background")
    
    blender_cmd.extend(["--python", run_cmd_path, "--", input_file, output_file])
    
    try:
        with console.status("[dim]Processing...", spinner="line"):
            result = subprocess.run(blender_cmd, capture_output=True, text=True)
            
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                return json.load(f)
        else:
            error_msg = result.stderr if result.stderr else "No output from Blender."
            return {"status": "error", "message": f"Execution failed: \n{error_msg}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="5.1.2", prog_name="BlenPC")
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose logging.")
@click.option('--blender-path', type=click.Path(exists=True), help="Custom path to Blender executable.")
def cli(verbose, blender_path):
    """
    BLENPC v5.1.2 | INDUSTRIAL PROCEDURAL GENERATOR
    
    A high-precision tool for architectural asset generation and building synthesis.
    """
    if verbose:
        os.environ["MF_LOG_LEVEL"] = "DEBUG"
    if blender_path:
        os.environ["BLENDER_PATH"] = blender_path

@cli.command()
@click.option('--width', '-w', type=float, default=20.0, help="Building width (m).")
@click.option('--depth', '-d', type=float, default=16.0, help="Building depth (m).")
@click.option('--floors', '-f', type=int, default=1, help="Floor count.")
@click.option('--seed', '-s', type=int, default=0, help="RNG seed.")
@click.option('--roof', '-r', type=click.Choice(['flat', 'gabled', 'hip', 'shed'], case_sensitive=False), default='flat', help="Roof geometry.")
@click.option('--output', '-o', type=click.Path(), default='./output', help="Output directory.")
@click.option('--spec', type=click.Path(exists=True), help="YAML/JSON specification file.")
@click.option('--preview', is_flag=True, help="Open in Blender GUI.")
def generate(width, depth, floors, seed, roof, output, spec, preview):
    """Execute building generation sequence."""
    console.print("\n[header]INITIALIZING GENERATION SEQUENCE[/header]")
    
    if spec:
        with open(spec, 'r') as f:
            spec_data = yaml.safe_load(f) if spec.endswith(('.yaml', '.yml')) else json.load(f)
        b_spec = spec_data.get('building', spec_data)
        width = b_spec.get('width', width)
        depth = b_spec.get('depth', depth)
        floors = b_spec.get('floors', floors)
        seed = b_spec.get('seed', seed)
        roof = b_spec.get('roof', {}).get('type', roof)
        output = b_spec.get('output', {}).get('directory', output)

    input_data = {
        "command": "generate_building",
        "seed": seed,
        "spec": {
            "width": width, "depth": depth, "floors": floors, "roof": roof, "output_dir": output
        }
    }
    
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_row("[label]WIDTH[/label]", f"[value]{width}m[/value]")
    table.add_row("[label]DEPTH[/label]", f"[value]{depth}m[/value]")
    table.add_row("[label]FLOORS[/label]", f"[value]{floors}[/value]")
    table.add_row("[label]SEED[/label]", f"[value]{seed}[/value]")
    table.add_row("[label]ROOF[/label]", f"[value]{roof.upper()}[/value]")
    table.add_row("[label]OUTPUT[/label]", f"[value]{output}[/value]")
    console.print(table)
    
    res = run_blender_task(input_data, preview)
    
    if res.get("status") == "success":
        console.print(f"\n[success]COMPLETED[/success]")
        console.print(f"[label]ASSET:[/label] [value]{res['result']['glb_path']}[/value]")
        console.print(f"[label]MANIFEST:[/label] [value]{res['result']['manifest']}[/value]\n")
    else:
        console.print(f"\n[error]FAILED[/error]")
        console.print(f"[error]{res.get('message')}[/error]\n")

@cli.group()
def asset():
    """Manage architectural asset components."""
    pass

@asset.command(name='create-wall')
@click.option('--name', '-n', required=True, help="Asset identifier.")
@click.option('--length', '-l', type=float, default=4.0, help="Component length (m).")
@click.option('--seed', '-s', type=int, default=0, help="RNG seed.")
def create_wall(name, length, seed):
    """Synthesize engineered wall component."""
    input_data = {
        "command": "create_wall",
        "seed": seed,
        "asset": {"name": name, "dimensions": {"width": length}}
    }
    console.print(f"\n[header]SYNTHESIZING COMPONENT:[/header] [value]{name}[/value]")
    res = run_blender_task(input_data)
    
    if res.get("status") == "success":
        console.print(f"[success]REGISTERED:[/success] [value]{res['result']['blend_file']}[/value]\n")
    else:
        console.print(f"[error]SYNTHESIS FAILED:[/error] [error]{res.get('message')}[/error]\n")

@cli.group()
def registry():
    """Access asset registry database."""
    pass

@registry.command(name='list')
@click.option('--tags', '-t', help="Filter by tags (csv).")
def list_assets(tags):
    """Query registered asset inventory."""
    if not os.path.exists(config.INVENTORY_FILE):
        console.print("[warning]DATABASE_NOT_FOUND[/warning]")
        return
        
    with open(config.INVENTORY_FILE, 'r') as f:
        inv = json.load(f)
    
    assets = inv.get('assets', {})
    if not assets:
        console.print("[warning]INVENTORY_EMPTY[/warning]")
        return

    filter_tags = [tag.strip() for tag in tags.split(',')] if tags else []
    
    table = Table(box=None, header_style="header", border_style="border")
    table.add_column("IDENTIFIER")
    table.add_column("DIMENSIONS (WxHxD)")
    table.add_column("SLOTS")
    table.add_column("TAGS")
    
    for name, data in assets.items():
        asset_tags = data.get('tags', [])
        if filter_tags and not all(t in asset_tags for t in filter_tags):
            continue
            
        dims = data.get('dimensions', {})
        dim_str = f"{dims.get('width', 0)}x{dims.get('height', 0)}x{dims.get('depth', 0)}"
        slots_count = len(data.get('slots', []))
        tags_str = ", ".join(asset_tags)
        
        table.add_row(f"[value]{name}[/value]", dim_str, str(slots_count), tags_str)
        
    console.print("\n[header]ASSET REGISTRY QUERY[/header]")
    console.print(table)
    console.print("")

@cli.command()
def info():
    """Display environment diagnostics."""
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_row("[label]VERSION[/label]", "[value]5.1.2[/value]")
    table.add_row("[label]PYTHON[/label]", f"[value]{platform.python_version()}[/value]")
    table.add_row("[label]SYSTEM[/label]", f"[value]{platform.system()} {platform.release()}[/value]")
    table.add_row("[label]BLENDER[/label]", f"[value]{os.environ.get('BLENDER_PATH', config.BLENDER_PATH)}[/value]")
    table.add_row("[label]LIBRARY[/label]", f"[value]{config.LIBRARY_DIR}[/value]")
    table.add_row("[label]REGISTRY[/label]", f"[value]{config.REGISTRY_DIR}[/value]")
    
    console.print("\n[header]SYSTEM DIAGNOSTICS[/header]")
    console.print(table)
    console.print("")

@cli.command()
@click.option('--spec', type=click.Path(exists=True), required=True, help="Batch specification file.")
def batch(spec):
    """Execute batch production sequence."""
    with open(spec, 'r') as f:
        spec_data = yaml.safe_load(f) if spec.endswith(('.yaml', '.yml')) else json.load(f)
    
    batch_list = spec_data.get('batch', {}).get('buildings', [])
    common_output = spec_data.get('batch', {}).get('output', {}).get('directory', './output')
    
    console.print(f"\n[header]BATCH SEQUENCE INITIATED ({len(batch_list)} UNITS)[/header]")
    
    with Progress(
        SpinnerColumn("line"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[dim]Processing...", total=len(batch_list))
        
        for b in batch_list:
            seed = b.get('seed', 1000)
            input_data = {
                "command": "generate_building", 
                "seed": seed,
                "spec": {
                    "width": b.get('width', 20.0), "depth": b.get('depth', 16.0),
                    "floors": b.get('floors', 1), "roof": b.get('roof', {}).get('type', 'flat'),
                    "output_dir": common_output
                }
            }
            res = run_blender_task(input_data)
            if res.get("status") == "error":
                console.print(f"[error]ERR_SEED_{seed}: {res.get('message')}[/error]")
            progress.advance(task)
    console.print("[success]BATCH SEQUENCE COMPLETED[/success]\n")

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def inspect(path):
    """Analyze architectural data file."""
    size_kb = os.path.getsize(path) / 1024
    console.print("\n[header]FILE ANALYSIS[/header]")
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_row("[label]FILE[/label]", f"[value]{os.path.basename(path)}[/value]")
    table.add_row("[label]PATH[/label]", f"[value]{path}[/value]")
    table.add_row("[label]SIZE[/label]", f"[value]{size_kb:.2f} KB[/value]")
    console.print(table)
    console.print("")

if __name__ == '__main__':
    cli()
