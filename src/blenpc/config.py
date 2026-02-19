import os
import platform
import logging
from typing import Any, Dict

"""BlenPC v5.1.1 - Core Configuration System."""

# --- 1. LOGGING CONFIGURATION ---
LOG_LEVEL = os.getenv("MF_LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("MF_LOG_FILE", None)
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s'

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE) if LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger("blenpc")

# --- 2. PATH MANAGEMENT ---
PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PACKAGE_ROOT))

LIBRARY_DIR = os.path.join(PROJECT_ROOT, "_library")
REGISTRY_DIR = os.path.join(PROJECT_ROOT, "_registry")
INVENTORY_FILE = os.path.join(REGISTRY_DIR, "inventory.json")
SLOTS_FILE = os.path.join(REGISTRY_DIR, "slot_types.json")
TAGS_FILE = os.path.join(REGISTRY_DIR, "tag_vocabulary.json")

# --- 3. BLENDER EXECUTABLE ---
def get_blender_path():
    env_path = os.getenv("BLENDER_PATH") or os.getenv("BLENDER_EXECUTABLE")
    if env_path and os.path.exists(env_path):
        return env_path
    
    if platform.system() == "Windows":
        paths = [
            r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            os.path.expandvars(r"%APPDATA%\Blender Foundation\Blender\blender.exe")
        ]
        for p in paths:
            if os.path.exists(p): return p
        return "blender.exe"
    elif platform.system() == "Darwin":
        return "/Applications/Blender.app/Contents/MacOS/Blender"
    else:
        return "/usr/bin/blender"

BLENDER_PATH = get_blender_path()
HEADLESS_ARGS = ["--background", "--python"]

# --- 4. PERFORMANCE & LIMITS ---
MAX_WORKER_PROCESSES = os.cpu_count() or 4
STRICT_VALIDATION = True
CACHE_ENABLED = True
AUTO_BACKUP_REGISTRY = True
BLENDER_MEMORY_WARN = 3000
USE_NEW_GEOMETRY = True  # BlenPC v5.0 New Pipeline Toggle

# --- 5. ARCHITECTURAL CONSTANTS ---
MICRO_UNIT = 0.025  # v5.2.0 Base Unit: 2.5cm (Integer Grid Base)
GRID = 0.25         # Standard Grid (10x Micro-Unit)
GRID_UNIT = 0.25    # Legacy - kept for backward compatibility
STORY_HEIGHT = 3.20 # WALL_HEIGHT + 0.2m (slab)
WALL_HEIGHT = 3.00  # Used only by vertical_authority.py
WALL_THICKNESS = 0.20 # Inner: symmetric, outer: single-sided
WALL_THICKNESS_BASE = 0.2
DEFAULT_UNIT_SYSTEM = "metric"
EXPORT_PRECISION = 4
MERGE_DISTANCE = 0.005 # Minimal cleanup for new pipeline

# --- 5.1. INTEGER GRID SYSTEM (v5.2.0) ---
SNAP_MODES = {
    "LOOSE": 0.25,
    "STRICT": 0.025,
    "MODULAR": 0.1
}

# --- 5.2. MODULAR STANDARDS (ISO 2848 + Game Standards) ---
WALL_STANDARDS = {
    "height":    {"min": 2.4, "default": 3.0,  "max": 4.5,  "step": 0.25},
    "thickness": {"thin": 0.1, "standard": 0.2, "thick": 0.3},
}

DOOR_STANDARDS = {
    "single":  {"w": 0.9,  "h": 2.1},
    "double":  {"w": 1.8,  "h": 2.1},
    "garage":  {"w": 2.4,  "h": 2.4},
}

WINDOW_STANDARDS = {
    "small":     {"w": 0.6,  "h": 0.6,  "sill": 1.2},
    "standard":  {"w": 1.2,  "h": 1.4,  "sill": 0.9},
    "large":     {"w": 1.8,  "h": 1.6,  "sill": 0.8},
    "panoramic": {"w": 2.4,  "h": 1.8,  "sill": 0.6},
}

# --- 6. MATH CONSTANTS ---
PHI = (1 + 5**0.5) / 2
GOLDEN_RATIO_VARIATION = 0.04

# --- 7. INVENTORY LOCKING ---
INVENTORY_LOCK_TIMEOUT = 5
INVENTORY_LOCK_POLL_INTERVAL = 0.1
INVENTORY_LOCK_STALE_AGE = 60

# --- 8. EXPORT SETTINGS ---
EXPORT_FORMATS_SUPPORTED = ["glb", "blend", "fbx", "obj"]

# --- 9. DEFAULTS ---
DEFAULT_ROOF_PITCH = 35.0
WINDOW_SILL_HEIGHT_DEFAULT = 1.2
WINDOW_DEFAULT_WIDTH = 1.0
WINDOW_DEFAULT_HEIGHT = 1.2
TEST_TIMEOUT_DEFAULT = 120

def get_settings() -> Dict[str, Any]:
    return {k: v for k, v in globals().items() if k.isupper()}
