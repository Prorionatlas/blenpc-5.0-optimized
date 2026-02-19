import time
import sys
import random
from rich.console import Console
from ..ascii_art.logos import CYBERPUNK_LOGO, SCIFI_DECO

def run_boot_sequence(console: Console, skip: bool = False):
    """Run an authentic 90s-style boot animation."""
    if skip:
        return

    # Clear screen (ANSI escape code)
    print("\033[H\033[J", end="")
    
    boot_messages = [
        "BLENPC BIOS v5.1.2 (C) 2026 CYBERPUNK SYSTEMS",
        "CPU: NEURAL_PROCESSOR_X900 @ 5.4GHz",
        "MEMORY: 128GB NEURO_RAM... OK",
        "STORAGE: QUANTUM_SSD_NVME... OK",
        "INITIALIZING BLENDER_ENGINE_CORE...",
        "CONNECTING TO ARCH_DATABASE...",
        "AUTHENTICATING USER: PRORIONATLAS...",
        "ESTABLISHING HUMAN-AI HYBRID INTERFACE...",
    ]

    for msg in boot_messages:
        console.print(f"[dim white]{msg}[/dim white]")
        time.sleep(random.uniform(0.05, 0.2))

    time.sleep(0.5)
    console.print(f"\n[bold cyan]{CYBERPUNK_LOGO}[/bold cyan]")
    console.print(f"[cyan]{SCIFI_DECO}[/cyan]\n")
    
    # Fake progress bar
    with console.status("[bold cyan]UPLOADING CORE MODULES...", spinner="dots"):
        time.sleep(1.5)
    
    console.print("[bold green]SYSTEM READY.[/bold green]\n")
    time.sleep(0.5)
