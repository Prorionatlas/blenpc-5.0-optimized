import click
import os
import sys
import json
import yaml
import platform
import subprocess
import time
from typing import Optional, List, Dict
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.theme import Theme
from rich.panel import Panel

# Expert Design: 90s Cyberpunk Retro Theme
RETRO_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold cyan",
    "label": "bold white",
    "value": "cyan",
    "border": "cyan",
    "dim": "dim white",
    "ai": "bold magenta"
})

console = Console(theme=RETRO_THEME)

# Expert Fix: Add src/ to path for CLI to find the blenpc package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from blenpc import config
from blenpc.retro.boot_sequence import run_boot_sequence
from blenpc.ascii_art.logos import CYBERPUNK_LOGO, SCIFI_DECO, LINE_DECO
from blenpc.ai_extensions.model_registry import ModelRegistry

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
        with console.status("[bold cyan]EXECUTING NEURAL_SYNTHESIS...", spinner="dots"):
            result = subprocess.run(blender_cmd, capture_output=True, text=True)
            
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                return json.load(f)
        else:
            error_msg = result.stderr if result.stderr else "No output from Blender."
            return {"status": "error", "message": f"CRITICAL_FAILURE: \n{error_msg}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="5.2.0", prog_name="BlenPC")
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose logging.")
@click.option('--blender-path', type=click.Path(exists=True), help="Custom path to Blender executable.")
@click.option('--skip-boot', is_flag=True, help="Skip boot animation sequence.")
@click.option('--json-output', is_flag=True, help="Output only machine-readable JSON for AI agents.")
def cli(verbose, blender_path, skip_boot, json_output):
    """
    [bold cyan]BLENPC v5.2.0[/bold cyan] | [bold magenta]HUMAN-AI HYBRID INTERFACE[/bold magenta]
    
    [dim white]Cyberpunk-style procedural architecture generator with Integer Grid & Collision Engine.[/dim white]
    """
    if verbose:
        os.environ["MF_LOG_LEVEL"] = "DEBUG"
    if blender_path:
        os.environ["BLENDER_PATH"] = blender_path
    
    if not skip_boot and not json_output:
        run_boot_sequence(console)

@cli.command()
@click.option('--width', '-w', type=float, default=20.0, help="Building width (m).")
@click.option('--depth', '-d', type=float, default=16.0, help="Building depth (m).")
@click.option('--floors', '-f', type=int, default=1, help="Floor count.")
@click.option('--seed', '-s', type=int, default=0, help="RNG seed.")
@click.option('--roof', '-r', type=click.Choice(['flat', 'gabled', 'hip', 'shed'], case_sensitive=False), default='flat', help="Roof geometry.")
@click.option('--snap', type=click.Choice(['LOOSE', 'STRICT', 'MODULAR'], case_sensitive=False), default='STRICT', help="Grid snap mode (v5.2.0).")
@click.option('--output', '-o', type=click.Path(), default='./output', help="Output directory.")
@click.option('--spec', type=click.Path(exists=True), help="YAML/JSON specification file.")
@click.option('--name', '-n', help="Model name for registry storage.")
@click.option('--tags', '-t', help="Semantic tags (comma separated).")
@click.option('--preview', is_flag=True, help="Open in Blender GUI.")
@click.pass_context
def generate(ctx, width, depth, floors, seed, roof, snap, output, spec, name, tags, preview):
    """Execute building generation sequence with v5.2.0 Integer Grid."""
    json_mode = ctx.parent.params.get('json_output', False)
    
    if not json_mode:
        console.print(f"[cyan]{LINE_DECO}[/cyan]")
        console.print("[header]» INITIATING ARCHITECTURAL_SYNTHESIS_v5.2[/header]")
    
    if spec:
        with open(spec, 'r') as f:
            spec_data = yaml.safe_load(f) if spec.endswith(('.yaml', '.yml')) else json.load(f)
        b_spec = spec_data.get('building', spec_data)
        width = b_spec.get('width', width)
        depth = b_spec.get('depth', depth)
        floors = b_spec.get('floors', floors)
        seed = b_spec.get('seed', seed)
        roof = b_spec.get('roof', {}).get('type', roof)
        snap = b_spec.get('snap', snap)
        output = b_spec.get('output', {}).get('directory', output)

    input_data = {
        "command": "generate_building",
        "seed": seed,
        "spec": {
            "width": width, 
            "depth": depth, 
            "floors": floors, 
            "roof": roof, 
            "snap_mode": snap,
            "output_dir": output
        }
    }
    
    if not json_mode:
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_row("[label]WIDTH[/label]", f"[value]{width}m[/value]")
        table.add_row("[label]DEPTH[/label]", f"[value]{depth}m[/value]")
        table.add_row("[label]FLOORS[/label]", f"[value]{floors}[/value]")
        table.add_row("[label]SEED[/label]", f"[value]{seed}[/value]")
        table.add_row("[label]ROOF[/label]", f"[value]{roof.upper()}[/value]")
        table.add_row("[label]SNAP_MODE[/label]", f"[bold yellow]{snap}[/bold yellow] ([dim]{config.SNAP_MODES.get(snap)}m[/dim])")
        table.add_row("[label]OUTPUT[/label]", f"[value]{output}[/value]")
        console.print(table)
    
    res = run_blender_task(input_data, preview)
    
    if res.get("status") == "success":
        # Save to Model Registry if name is provided
        if name:
            tag_list = [t.strip() for t in tags.split(',')] if tags else []
            ModelRegistry.save_model(name, input_data["spec"], res["result"], tag_list)
            if not json_mode:
                console.print(f"[ai]MODEL_REGISTERED: {name} (Tags: {', '.join(tag_list)})[/ai]")
        
        if json_mode:
            print(json.dumps(res, indent=2))
        else:
            console.print(f"\n[success]SYNTHESIS_COMPLETE[/success]")
            console.print(f"[label]ASSET:[/label] [value]{res['result']['glb_path']}[/value]")
            console.print(f"[label]MANIFEST:[/label] [value]{res['result']['manifest']}[/value]\n")
            console.print(f"[cyan]{LINE_DECO}[/cyan]")
    else:
        if json_mode:
            print(json.dumps(res, indent=2))
        else:
            console.print(f"\n[error]SYNTHESIS_FAILED[/error]")
            # Collision Engine errors are formatted specifically
            msg = res.get('message', 'Unknown error')
            if "LAYOUT_CONFLICT" in msg:
                console.print(Panel(f"[bold red]COLLISION_ENGINE_ALERT[/bold red]\n\n{msg}", border_style="red"))
            else:
                console.print(f"[error]{msg}[/error]\n")

@cli.group()
def registry():
    """Access neural model registry database."""
    pass

@registry.command(name='list')
@click.option('--tags', '-t', help="Filter by tags (csv).")
@click.pass_context
def list_models(ctx, tags):
    """Query registered neural model inventory."""
    json_mode = ctx.parent.parent.params.get('json_output', False)
    tag_list = [t.strip() for t in tags.split(',')] if tags else []
    
    models = ModelRegistry.list_models(tag_list)
    
    if json_mode:
        print(json.dumps(models, indent=2))
        return

    if not models:
        console.print("[warning]DATABASE_EMPTY_OR_NO_MATCHES[/warning]")
        return

    table = Table(box=None, header_style="header", border_style="border")
    table.add_column("IDENTIFIER")
    table.add_column("DIMENSIONS")
    table.add_column("SNAP")
    table.add_column("TIMESTAMP")
    table.add_column("TAGS")
    
    for name, data in models.items():
        spec = data.get('spec', {})
        dim_str = f"{spec.get('width')}x{spec.get('depth')}x{spec.get('floors')}F"
        snap_str = spec.get('snap_mode', 'N/A')
        tags_str = ", ".join(data.get('tags', []))
        table.add_row(f"[value]{name}[/value]", dim_str, snap_str, data.get('timestamp'), tags_str)
        
    console.print("\n[header]NEURAL_MODEL_REGISTRY_QUERY[/header]")
    console.print(table)
    console.print("")

@cli.command()
def info():
    """Display neural core diagnostics."""
    console.print(f"\n[bold cyan]{CYBERPUNK_LOGO}[/bold cyan]")
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_row("[label]CORE_VERSION[/label]", "[value]5.2.0[/value]")
    table.add_row("[label]MICRO_UNIT[/label]", f"[value]{config.MICRO_UNIT}m[/value]")
    table.add_row("[label]PYTHON_RUNTIME[/label]", f"[value]{platform.python_version()}[/value]")
    table.add_row("[label]HOST_SYSTEM[/label]", f"[value]{platform.system()} {platform.release()}[/value]")
    table.add_row("[label]BLENDER_PATH[/label]", f"[value]{os.environ.get('BLENDER_PATH', config.BLENDER_PATH)}[/value]")
    table.add_row("[label]LIBRARY_PATH[/label]", f"[value]{config.LIBRARY_DIR}[/value]")
    table.add_row("[label]REGISTRY_PATH[/label]", f"[value]{config.REGISTRY_DIR}[/value]")
    
    console.print("\n[header]SYSTEM_DIAGNOSTICS[/header]")
    console.print(table)
    
    # Show snap modes
    snap_table = Table(title="ACTIVE_SNAP_MODES", box=None, header_style="bold yellow")
    snap_table.add_column("MODE")
    snap_table.add_column("PRECISION")
    for mode, prec in config.SNAP_MODES.items():
        snap_table.add_row(mode, f"{prec}m")
    console.print(snap_table)
    
    console.print(f"\n[ai]AI_AGENT_MODE: ACTIVE (Use --json-output for structured data)[/ai]")
    console.print(f"[cyan]{SCIFI_DECO}[/cyan]\n")

if __name__ == '__main__':
    cli()
