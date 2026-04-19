"""
s1_prepare.py — Receptor and ligand preparation.
- Strip solvent from receptor PDB
- Convert receptor PDB → PDBQT (obabel -xr)
- Convert ligand mol2/sdf → PDBQT (meeko)
- Compute blind-docking grid box
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.fileio import strip_receptor_pdb
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s1")


def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    prep_dir = run_dir / "prep"
    prep_dir.mkdir(exist_ok=True)

    receptor_pdb = Path(config.receptor)
    clean_pdb = prep_dir / "receptor_clean.pdb"
    receptor_pdbqt = prep_dir / "receptor.pdbqt"

    # 1. Strip solvent and NMA from receptor
    log.info(f"Stripping receptor: {receptor_pdb.name}")
    strip_receptor_pdb(receptor_pdb, clean_pdb)

    # 2. Receptor PDB → PDBQT
    log.info("Converting receptor to PDBQT...")
    result = subprocess.run(
        ["obabel", str(clean_pdb), "-O", str(receptor_pdbqt), "-xr"],
        capture_output=True, text=True
    )
    if not receptor_pdbqt.exists():
        raise RuntimeError(f"obabel failed for receptor:\n{result.stderr}")

    # 2b. Fix charges (obabel -xr often leaves them 0.000, which crashes autogrid4)
    log.info("Fixing receptor partial charges for autogrid4...")
    _fix_pdbqt_charges(receptor_pdbqt)

    # 3. Compute grid box (blind: protein bounding box + 8Å padding)
    box = _compute_blind_box(clean_pdb, padding=8.0)
    log.info(f"Grid box: center={box['center']}, size={box['size']}")

    # 4. Ligand → PDBQT via meeko
    lig_pdbqts = {}
    for lig_path in config.ligands:
        lig = Path(lig_path)
        out_pdbqt = prep_dir / f"{lig.stem}.pdbqt"
        _prepare_ligand_meeko(lig, out_pdbqt)
        lig_pdbqts[lig.stem] = out_pdbqt

    return {
        "receptor_pdbqt": receptor_pdbqt,
        "receptor_clean_pdb": clean_pdb,
        "lig_pdbqts": lig_pdbqts,
        "grid_box": box,
    }


def _compute_blind_box(pdb: Path, padding: float = 8.0) -> dict:
    """Compute bounding box of all ATOM/HETATM coords in PDB."""
    xs, ys, zs = [], [], []
    for line in pdb.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                xs.append(float(line[30:38]))
                ys.append(float(line[38:46]))
                zs.append(float(line[46:54]))
            except ValueError:
                continue
    if not xs:
        raise ValueError("No atom coordinates found in receptor PDB")
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    cz = (min(zs) + max(zs)) / 2
    sx = max(xs) - min(xs) + 2 * padding
    sy = max(ys) - min(ys) + 2 * padding
    sz = max(zs) - min(zs) + 2 * padding
    return {"center": [round(cx, 3), round(cy, 3), round(cz, 3)],
            "size": [round(sx, 1), round(sy, 1), round(sz, 1)]}


def _prepare_ligand_meeko(lig_path: Path, out_pdbqt: Path) -> None:
    """Convert ligand mol2/sdf to PDBQT using Meeko."""
    log.info(f"Meeko: {lig_path.name} → {out_pdbqt.name}")
    try:
        from rdkit import Chem
        from meeko import MoleculePreparation

        if lig_path.suffix.lower() == ".mol2":
            mol = Chem.MolFromMol2File(str(lig_path), removeHs=False)
        else:
            mol = Chem.MolFromMolFile(str(lig_path), removeHs=False)

        if mol is None:
            raise ValueError(f"RDKit failed to read: {lig_path}")

        prep = MoleculePreparation()
        prep.prepare(mol)
        pdbqt_str = prep.write_pdbqt_string()
        out_pdbqt.write_text(pdbqt_str)
    except Exception as e:
        raise RuntimeError(f"Meeko failed for {lig_path}: {e}")


def _fix_pdbqt_charges(pdbqt: Path) -> None:
    """
    AutoDock-GPU / autogrid4 fails if receptor charges are all 0.000.
    This function assigns semi-reasonable dummy charges if they are zero.
    """
    lines = pdbqt.read_text().splitlines()
    new_lines = []
    
    # Simple charge model for common atoms
    charge_map = {
        "N": -0.20, "NA": -0.20, "OA": -0.20,
        "HD": 0.15, "H": 0.15,
        "C": 0.05, "A": 0.05,
        "S": -0.10, "SA": -0.10,
        "FE": 2.00, "Fe": 2.00,
        "MG": 2.00, "Mg": 2.00,
        "ZN": 2.00, "Zn": 2.00,
    }

    for line in lines:
        if line.startswith(("ATOM", "HETATM")):
            # Charge column in PDBQT is 71-76 (1-indexed)
            current_q_str = line[70:76].strip()
            try:
                q = float(current_q_str)
            except ValueError:
                q = 0.0
            
            if abs(q) < 0.0001:
                atom_type = line[77:79].strip()
                new_q = charge_map.get(atom_type, 0.001)
                
                # Format charge to 6 chars, right aligned
                q_str = f"{new_q:6.3f}"
                new_line = line[:70] + q_str + line[76:]
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    pdbqt.write_text("\n".join(new_lines) + "\n")
