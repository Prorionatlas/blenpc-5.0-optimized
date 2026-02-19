import pytest
from blenpc.config import SNAP_MODES
from blenpc.mf_v5.geometry_authority import quantize, to_int_grid

def test_snap_modes_configuration():
    """Ensure all required snap modes exist in config."""
    assert "LOOSE" in SNAP_MODES
    assert "STRICT" in SNAP_MODES
    assert "MODULAR" in SNAP_MODES
    
    assert SNAP_MODES["LOOSE"] == 0.25
    assert SNAP_MODES["STRICT"] == 0.025
    assert SNAP_MODES["MODULAR"] == 0.1

def test_quantization_precision():
    """Verify quantization against the 0.025m (STRICT) base."""
    # 0.124 should snap to 0.125 (5 * 0.025)
    assert quantize(0.124) == 0.125
    # 0.012 should snap to 0.0 (0 * 0.025)
    assert quantize(0.012) == 0.0
    # 0.013 should snap to 0.025 (1 * 0.025)
    assert quantize(0.013) == 0.025

def test_integer_grid_consistency():
    """Ensure float to int conversion is consistent."""
    # 1.0m should be exactly 40 units (1.0 / 0.025)
    assert to_int_grid(1.0) == 40
    # 0.25m should be exactly 10 units
    assert to_int_grid(0.25) == 10
