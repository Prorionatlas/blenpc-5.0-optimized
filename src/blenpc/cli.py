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
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

# Expert Fix: Add src/ to path for CLI to find the blenpc package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from blenpc import config

console = Console()

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
        with console.status("[bold green]Executing Blender task...", spinner="dots"):
            result = subprocess.run(blender_cmd, capture_output=True, text=True)
            
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                return json.load(f)
        else:
            error_msg = result.stderr if result.stderr else "No output from Blender."
            return {"status": "error", "message": f"Blender did not produce output. \n{error_msg}"}
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
    [bold cyan]BlenPC v5.1.2[/bold cyan] - Expert-Driven Procedural Building Generator.
    
    A professional tool for generating architectural assets and buildings using Blender.
    """
    if verbose:
        os.environ["MF_LOG_LEVEL"] = "DEBUG"
    if blender_path:
        os.environ["BLENDER_PATH"] = blender_path

@cli.command()
@click.option('--width', '-w', type=float, default=20.0, help="Building width in meters.")
@click.option('--depth', '-d', type=float, default=16.0, help="Building depth in meters.")
@click.option('--floors', '-f', type=int, default=1, help="Number of floors.")
@click.option('--seed', '-s', type=int, default=0, help="Random seed for generation.")
@click.option('--roof', '-r', type=click.Choice(['flat', 'gabled', 'hip', 'shed'], case_sensitive=False), default='flat', help="Roof type.")
@click.option('--output', '-o', type=click.Path(), default='./output', help="Output directory.")
@click.option('--spec', type=click.Path(exists=True), help="Path to YAML/JSON spec file.")
@click.option('--preview', is_flag=True, help="Open in Blender GUI after generation.")
def generate(width, depth, floors, seed, roof, output, spec, preview):
    """Generate a procedural building based on specifications."""
    rprint(Panel.fit("[bold green]BlenPC Generation Engine[/bold green]", subtitle="v5.1.2"))
    
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
            "width": width,
            "depth": depth,
            "floors": floors,
            "roof": roof,
            "output_dir": output
        }
    }
    
    table = Table(title="Generation Parameters")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Width", f"{width}m")
    table.add_row("Depth", f"{depth}m")
    table.add_row("Floors", str(floors))
    table.add_row("Seed", str(seed))
    table.add_row("Roof", roof.capitalize())
    table.add_row("Output", output)
    console.print(table)
    
    res = run_blender_task(input_data, preview)
    
    if res.get("status") == "success":
        rprint(f"\n[bold green]✓ Generation Successful![/bold green]")
        rprint(f"[bold]GLB Path:[/bold] {res['result']['glb_path']}")
        rprint(f"[bold]Manifest:[/bold] {res['result']['manifest']}")
    else:
        rprint(f"\n[bold red]✗ Generation Failed![/bold red]")
        rprint(f"[red]{res.get('message')}[/red]")

@cli.group()
def asset():
    """Manage architectural assets (walls, doors, etc.)."""
    pass

@asset.command(name='create-wall')
@click.option('--name', '-n', required=True, help="Name of the wall asset.")
@click.option('--length', '-l', type=float, default=4.0, help="Length of the wall.")
@click.option('--seed', '-s', type=int, default=0, help="Seed for slot generation.")
def create_wall(name, length, seed):
    """Create a new engineered wall asset with modular slots."""
    input_data = {
        "command": "create_wall",
        "seed": seed,
        "asset": {
            "name": name,
            "dimensions": {"width": length}
        }
    }
    rprint(f"Creating wall asset: [bold cyan]{name}[/bold cyan] (Length: {length}m)")
    res = run_blender_task(input_data)
    
    if res.get("status") == "success":
        rprint(f"[bold green]✓ Asset created and registered:[/bold green] {res['result']['blend_file']}")
    else:
        rprint(f"[bold red]✗ Failed to create asset:[/bold red] {res.get('message')}")

@cli.group()
def registry():
    """Manage the asset registry and inventory."""
    pass

@registry.command(name='list')
@click.option('--tags', '-t', help="Filter by tags (comma separated).")
def list_assets(tags):
    """List all registered assets in the inventory."""
    if not os.path.exists(config.INVENTORY_FILE):
        rprint("[yellow]Inventory file not found. Registry is empty.[/yellow]")
        return
        
    with open(config.INVENTORY_FILE, 'r') as f:
        inv = json.load(f)
    
    assets = inv.get('assets', {})
    if not assets:
        rprint("[yellow]No assets found in registry.[/yellow]")
        return

    filter_tags = [tag.strip() for tag in tags.split(',')] if tags else []
    
    table = Table(title="BlenPC Asset Registry")
    table.add_column("Name", style="cyan")
    table.add_column("Dimensions (WxHxD)", style="green")
    table.add_column("Slots", style="magenta")
    table.add_column("Tags", style="yellow")
    
    for name, data in assets.items():
        asset_tags = data.get('tags', [])
        if filter_tags and not all(t in asset_tags for t in filter_tags):
            continue
            
        dims = data.get('dimensions', {})
        dim_str = f"{dims.get('width', 0)}x{dims.get('height', 0)}x{dims.get('depth', 0)}"
        slots_count = len(data.get('slots', []))
        tags_str = ", ".join(asset_tags)
        
        table.add_row(name, dim_str, str(slots_count), tags_str)
        
    console.print(table)

@cli.command()
def info():
    """Display system and environment information."""
    table = Table(title="BlenPC System Information", show_header=False)
    table.add_row("BlenPC Version", "5.1.2")
    table.add_row("Python Version", platform.python_version())
    table.add_row("OS", f"{platform.system()} {platform.release()}")
    table.add_row("Blender Path", os.environ.get("BLENDER_PATH", config.BLENDER_PATH))
    table.add_row("Library Dir", config.LIBRARY_DIR)
    table.add_row("Registry Dir", config.REGISTRY_DIR)
    
    rprint(Panel(table, title="[bold cyan]Environment Info[/bold cyan]", expand=False))

@cli.command()
@click.option('--spec', type=click.Path(exists=True), required=True, help="Path to batch spec file.")
def batch(spec):
    """Run batch production of multiple buildings."""
    with open(spec, 'r') as f:
        spec_data = yaml.safe_load(f) if spec.endswith(('.yaml', '.yml')) else json.load(f)
    
    batch_list = spec_data.get('batch', {}).get('buildings', [])
    common_output = spec_data.get('batch', {}).get('output', {}).get('directory', './output')
    
    rprint(f"[bold cyan]Starting batch process for {len(batch_list)} buildings...[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[green]Processing buildings...", total=len(batch_list))
        
        for b in batch_list:
            seed = b.get('seed', 1000)
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
            res = run_blender_task(input_data)
            if res.get("status") == "error":
                rprint(f"[red]Error in seed {seed}: {res.get('message')}[/red]")
            progress.advance(task)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
def inspect(path):
    """Inspect a GLB or Blend file for architectural data."""
    size_kb = os.path.getsize(path) / 1024
    rprint(Panel.fit(
        f"[bold]File:[/bold] {os.path.basename(path)}\n"
        f"[bold]Path:[/bold] {path}\n"
        f"[bold]Size:[/bold] {size_kb:.2f} KB",
        title="[bold cyan]Asset Inspection[/bold cyan]"
    ))

if __name__ == '__main__':
    cli()
