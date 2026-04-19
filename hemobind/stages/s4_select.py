"""
s4_select.py — Score and select top-N candidates for MD.
"""
import json
import math
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s4")


def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    select_dir = run_dir / "selected"
    select_dir.mkdir(exist_ok=True)

    plip_results: dict = context.get("plip_results", {})
    top_n = config.analysis.top_n

    all_scored = []

    for lig_name, poses in plip_results.items():
        for pose in poses:
            inter = pose["interactions"]
            # Scoring formula
            score = (-1.0 * pose["energy"]) + (0.5 * inter["hbonds"]) + (0.3 * inter["hydrophobic"])
            
            # Extract coordinates to compute centroid for clustering
            centroid = _get_centroid(Path(pose["pdb_file"]))
            
            all_scored.append({
                "ligand": lig_name,
                "pose": pose["pose"],
                "energy": pose["energy"],
                "score": score,
                "hbonds": inter["hbonds"],
                "hydrophobic": inter["hydrophobic"],
                "pdb_file": pose["pdb_file"],
                "centroid": centroid
            })

    # Sort by score descending
    all_scored.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate (Cluster within 3A)
    selected = []
    for candidate in all_scored:
        if len(selected) >= top_n:
            break
        
        is_unique = True
        for sel in selected:
            if _dist(candidate["centroid"], sel["centroid"]) < 3.0:
                is_unique = False
                break
        
        if is_unique:
            selected.append(candidate)

    # Save to select_dir
    final_paths = []
    for i, sel in enumerate(selected):
        rank = i + 1
        src = Path(sel["pdb_file"])
        dest = select_dir / f"rank{rank}_{sel['ligand']}_pose{sel['pose']}.pdb"
        dest.write_text(src.read_text())
        sel["selected_pdb"] = str(dest)
        final_paths.append(dest)
        log.info(f"Selected Rank {rank}: {sel['ligand']} pose {sel['pose']} (Score: {sel['score']:.2f})")

    with open(select_dir / "ranking.json", "w") as f:
        json.dump(selected, f, indent=2)

    return {**context, "selected_poses": selected, "selected_paths": final_paths}


def _get_centroid(pdb_file: Path) -> tuple[float, float, float]:
    xs, ys, zs = [], [], []
    for line in pdb_file.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                xs.append(float(line[30:38]))
                ys.append(float(line[38:46]))
                zs.append(float(line[46:54]))
            except ValueError:
                continue
    if not xs:
        return (0.0, 0.0, 0.0)
    return (sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs))


def _dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)
