from dataclasses import dataclass, field
from typing import List
from ..config import GRID
from .vertical_authority import floor_elevations
from .exceptions import GenerationError

@dataclass
class ValidationResult:
    """Result of mesh validation with errors and warnings."""
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

def validate_mesh(bm, spec) -> ValidationResult:
    """Validate that the generated mesh meets production standards."""
    errors, warnings = [], []
    
    if not bm:
        return ValidationResult(False, ["Bmesh is null"], [])

    # 1. Non-manifold edge
    nm = [e for e in bm.edges if not e.is_manifold]
    if nm:
        errors.append(f'Non-manifold edges: {len(nm)} adet')
        
    # 2. Zero-area face
    za = [f for f in bm.faces if f.calc_area() < 1e-8]
    if za:
        errors.append(f'Zero-area faces: {len(za)} adet')
        
    # 3. Short edges (degenerate geometry)
    short = [e for e in bm.edges if e.calc_length() < GRID * 0.1]
    if short:
        warnings.append(f'Kısa edge: {len(short)} adet (< {GRID*0.1:.4f}m)')
        
    # 4. Roof-wall gap control
    expected_roof_z = floor_elevations(spec.floors - 1).wall_top_z
    # Find verts that are supposedly at roof level but have Z deviation
    # We only check vertices that are roughly at the top floor's wall top height
    roof_verts = [v for v in bm.verts if abs(v.co.z - expected_roof_z) < 0.1 and abs(v.co.z - expected_roof_z) > 1e-4]
    if roof_verts:
        errors.append(
            f'Roof-wall gap: beklenen z={expected_roof_z:.4f}, '
            f'{len(roof_verts)} vertex sapma gösteriyor'
        )
        
    return ValidationResult(len(errors) == 0, errors, warnings)

def generation_gate(result: ValidationResult, spec_id: str = "unknown") -> None:
    """Enforce validation and raise exception on failure."""
    if not result.passed:
        error_msg = f'[BlenPC] Mesh validation FAILED — spec_id={spec_id}\n'
        error_msg += '\n'.join(f' ERROR: {e}' for e in result.errors)
        if result.warnings:
            error_msg += '\n' + '\n'.join(f' WARN: {w}' for w in result.warnings)
        raise GenerationError(error_msg)
