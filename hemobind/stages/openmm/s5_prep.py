"""
s5_prep.py — OpenMM System Preparation (Receptor fixing and Ligand parsing).
"""
import concurrent.futures
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s5")

def fix_receptor(receptor_pdb: Path, output_pdb: Path, ph: float) -> Path:
    from pdbfixer import PDBFixer
    from openmm.app import PDBFile

    log.info(f"Fixing receptor {receptor_pdb.name} with PDBFixer at pH {ph}...")
    fixer = PDBFixer(filename=str(receptor_pdb))
    fixer.findMissingResidues()
    fixer.findNonstandardResidues()
    fixer.replaceNonstandardResidues()
    fixer.removeHeterogens(True) # Keep water? Let's remove them to be safe and re-solvate
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(ph)
    
    with open(output_pdb, 'w') as f:
        PDBFile.writeFile(fixer.topology, fixer.positions, f, keepIds=True)
    
    return output_pdb

def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    md_setup_dir = run_dir / "md_setup"
    md_setup_dir.mkdir(exist_ok=True)

    selected_paths: list[Path] = context.get("selected_paths", [])
    receptor_pdb: Path = context.get("receptor_clean_pdb")
    if not selected_paths:
        raise ValueError("No selected poses found in context")
    if not receptor_pdb:
        raise ValueError("Receptor PDB not found in context")

    prepped_systems = []

    # 1. Fix the receptor (only needs to be done once!)
    fixed_receptor_pdb = md_setup_dir / f"{receptor_pdb.stem}_fixed.pdb"
    if not fixed_receptor_pdb.exists():
        fix_receptor(receptor_pdb, fixed_receptor_pdb, config.md.ph)
    else:
        log.info(f"Fixed receptor already exists: {fixed_receptor_pdb.name}")

    # 2. Map fixed receptor with each ligand
    for input_ligand in selected_paths:
        # We just pass the ligand mol2 file forward. Parameterization will happen in s6_build.
        system_dict = {
            "name": input_ligand.stem,
            "receptor": fixed_receptor_pdb,
            "ligand": input_ligand
        }
        prepped_systems.append(system_dict)

    log.info("System preparation completed for all selected poses.")
    return {**context, "prepped_systems": prepped_systems, "md_setup_dir": md_setup_dir}
