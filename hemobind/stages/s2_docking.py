"""
s2_docking.py — AutoDock-GPU docking + DLG parsing.
Adapted from Docking/scripts/extract_dlg.py and run_adgpu.py
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.fileio import sanitize_pdb
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s2")


def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    dock_dir = run_dir / "docking"
    dock_dir.mkdir(exist_ok=True)

    receptor_pdbqt: Path = context["receptor_pdbqt"]
    lig_pdbqts: dict = context["lig_pdbqts"]
    grid_box: dict = context["grid_box"]

    all_poses: dict[str, list[dict]] = {}

    for lig_name, lig_pdbqt in lig_pdbqts.items():
        log.info(f"Docking: {lig_name}")
        lig_dir = dock_dir / lig_name
        lig_dir.mkdir(exist_ok=True)

        dlg_file = _run_adgpu(
            receptor_pdbqt=receptor_pdbqt,
            ligand_pdbqt=lig_pdbqt,
            output_dir=lig_dir,
            grid_box=grid_box,
            n_runs=config.docking.n_poses * 10,  # AD-GPU runs >> poses
        )

        poses = _extract_dlg(dlg_file, lig_dir, n_top=config.docking.n_poses)
        all_poses[lig_name] = poses
        log.info(f"  {lig_name}: {len(poses)} poses extracted, best ΔG={poses[0]['energy']:.2f}")

    return {**context, "all_poses": all_poses, "dock_dir": dock_dir}


def _run_adgpu(receptor_pdbqt: Path, ligand_pdbqt: Path,
               output_dir: Path, grid_box: dict, n_runs: int = 100) -> Path:
    """Generate map files and run AutoDock-GPU. Returns path to DLG file."""
    # Copy receptor to docking dir for autogrid4
    local_receptor = output_dir / receptor_pdbqt.name
    if not local_receptor.exists():
        local_receptor.write_bytes(receptor_pdbqt.read_bytes())

    # Extract receptor atom types dynamically
    rec_types = _get_pdbqt_types(local_receptor)
    log.info(f"Receptor atom types: {', '.join(rec_types)}")

    # Generate GPF for autogrid4
    gpf_file = output_dir / "grid.gpf"
    glg_file = output_dir / "grid.glg"
    fld_file = output_dir / f"{receptor_pdbqt.stem}.maps.fld"

    cx, cy, cz = grid_box["center"]
    sx, sy, sz = grid_box["size"]
    npts_x = int(sx / 0.375)
    npts_y = int(sy / 0.375)
    npts_z = int(sz / 0.375)

    # Autodock atom types for maps (usually we map common types)
    # The receptor types MUST match what is in the PDBQT exactly
    map_types = ["A", "C", "NA", "OA", "N", "SA", "HD"]
    
    gpf_lines = [
        f"npts {npts_x} {npts_y} {npts_z}",
        f"gridfld {fld_file.name}",
        "spacing 0.375",
        f"receptor_types {' '.join(rec_types)}",
        f"ligand_types {' '.join(map_types)}",
        f"receptor {receptor_pdbqt.name}",
        f"gridcenter {cx:.3f} {cy:.3f} {cz:.3f}",
        "smooth 0.5"
    ]
    
    for t in map_types:
        gpf_lines.append(f"map {receptor_pdbqt.stem}.{t}.map")
    
    gpf_lines += [
        f"elecmap {receptor_pdbqt.stem}.e.map",
        f"dsolvmap {receptor_pdbqt.stem}.d.map",
        "dielectric -0.1465"
    ]
    
    gpf_file.write_text("\n".join(gpf_lines) + "\n")

    # Run autogrid4
    log.info("Running autogrid4...")
    result = subprocess.run(["autogrid4", "-p", str(gpf_file), "-l", str(glg_file)],
                            capture_output=True, text=True, cwd=str(output_dir))
    if result.returncode != 0:
        raise RuntimeError(f"autogrid4 failed:\n{result.stderr}")

    if not fld_file.exists():
        raise RuntimeError(f"autogrid4 produced no FLD file: {fld_file}")

    # Run AD-GPU
    dlg_file = output_dir / f"{ligand_pdbqt.stem}_adgpu.dlg"
    log.info(f"Running AutoDock-GPU ({n_runs} runs)...")
    result = subprocess.run(
        ["adgpu",
         "--ffile", str(fld_file),
         "--lfile", str(ligand_pdbqt),
         "--nrun", str(n_runs),
         "--heurmax", "134217728",
         "--resnam", str(dlg_file.stem),
         "--xmloutput", "0"],
        capture_output=True, text=True, cwd=str(output_dir)
    )
    if result.returncode != 0:
        raise RuntimeError(f"AutoDock-GPU failed:\n{result.stderr}")

    # AD-GPU writes to CWD
    produced = output_dir / f"{dlg_file.stem}.dlg"
    if not produced.exists():
        raise RuntimeError(f"No DLG output found: {produced}")

    return produced


def _extract_dlg(dlg_file: Path, output_dir: Path, n_top: int = 10) -> list[dict]:
    """
    Extract top-N poses from AD-GPU DLG file.
    AD-GPU puts all models in 'DOCKED: ' lines at the end.
    """
    text = dlg_file.read_text()
    
    # Each model starts with "DOCKED: MODEL"
    model_blocks = re.split(r"DOCKED:\s+MODEL", text)[1:] # skip header
    results = []

    for block in model_blocks:
        # Energy is in the first few lines of the block
        energy_match = re.search(r"Estimated Free Energy of Binding\s+=\s+([-\d.]+)", block)
        if not energy_match:
            continue
        energy = float(energy_match.group(1))

        # Extract PDBQT coordinates
        pdbqt_lines = []
        for line in block.splitlines():
            # If line starts with "DOCKED: ", it's part of the model
            # Note: block starts AFTER "DOCKED: MODEL"
            if line.strip().startswith("ENDMDL"):
                break
            if line.startswith(" "): # and not "USER" or "REMARK"?
                # Some lines don't have "DOCKED: " because re.split consumed it?
                # No, re.split consumed "DOCKED: MODEL". The rest of the line is there.
                pass
            
            # Actually, the simplest way is to take all lines until ENDMDL
            # and strip "DOCKED: " from them if present.
            clean_line = line.replace("DOCKED: ", "").strip("\r\n")
            # Only keep ROOT, BRANCH, ATOM, etc.
            if any(clean_line.startswith(x) for x in ["ROOT", "BRANCH", "ATOM", "HETATM", "USER", "REMARK", "ENDBRANCH", "ENDROOT", "TORSDOF"]):
                pdbqt_lines.append(clean_line)

        if not pdbqt_lines:
            continue

        results.append({"energy": energy, "pdbqt_lines": pdbqt_lines})

    # Sort by energy
    results.sort(key=lambda x: x["energy"])
    top = results[:n_top]

    # Write pose PDBQTs and sanitized PDBs
    poses = []
    for i, r in enumerate(top):
        pose_n = i + 1
        pdbqt_file = output_dir / f"pose_{pose_n}.pdbqt"
        pdbqt_file.write_text("\n".join(r["pdbqt_lines"]))

        pdb_raw = output_dir / f"pose_{pose_n}_raw.pdb"
        pdb_clean = output_dir / f"pose_{pose_n}.pdb"
        subprocess.run(
            ["obabel", "-ipdbqt", str(pdbqt_file), "-opdb", "-O", str(pdb_raw), "-f", "1", "-l", "1"],
            capture_output=True, text=True
        )
        if pdb_raw.exists():
            sanitize_pdb(pdb_raw, pdb_clean)
            pdb_raw.unlink()

        poses.append({
            "pose": pose_n,
            "energy": r["energy"],
            "pdb_file": str(pdb_clean),
            "pdbqt_file": str(pdbqt_file),
        })

    return poses


def _get_pdbqt_types(pdbqt: Path) -> list[str]:
    """Extract unique atom types from columns 78-79 of PDBQT."""
    types = set()
    with open(pdbqt) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                t = line[77:79].strip()
                if t:
                    types.add(t)
    return sorted(list(types))
