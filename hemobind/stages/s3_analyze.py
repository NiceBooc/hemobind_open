"""
s3_analyze.py — Interaction analysis using PLIP via Docker.
"""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s3")


def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    analysis_dir = run_dir / "analysis"
    analysis_dir.mkdir(exist_ok=True)

    receptor_pdb: Path = context["receptor_clean_pdb"]
    all_poses: dict = context.get("all_poses", {})

    plip_results = {}

    for lig_name, poses in all_poses.items():
        log.info(f"Analyzing PLIP interactions for {lig_name}...")
        lig_results = []

        for pose in poses:
            pose_num = pose["pose"]
            pose_pdb = Path(pose["pdb_file"])
            
            # Merge receptor and pose
            complex_pdb = analysis_dir / f"{lig_name}_pose_{pose_num}_complex.pdb"
            _merge_pdb(receptor_pdb, pose_pdb, complex_pdb)

            # Run PLIP
            out_dir = analysis_dir / f"{lig_name}_pose_{pose_num}"
            out_dir.mkdir(exist_ok=True)
            _run_plip(complex_pdb, out_dir, config.analysis.plip_docker_image)

            # PLIP -x produces {input_stem}_report.xml
            report_xml = out_dir / f"{complex_pdb.stem}_report.xml"
            if report_xml.exists():
                interactions = _parse_plip_xml(report_xml)
                lig_results.append({
                    "pose": pose_num,
                    "energy": pose["energy"],
                    "pdb_file": str(pose_pdb),
                    "complex_file": str(complex_pdb),
                    "interactions": interactions
                })
            else:
                log.warning(f"PLIP report not found for {lig_name} pose {pose_num}")
                lig_results.append({
                    "pose": pose_num,
                    "energy": pose["energy"],
                    "pdb_file": str(pose_pdb),
                    "complex_file": str(complex_pdb),
                    "interactions": {"hbonds": 0, "hydrophobic": 0, "pi_stacking": 0}
                })

        plip_results[lig_name] = lig_results

    # Save summary
    with open(analysis_dir / "analysis_results.json", "w") as f:
        json.dump(plip_results, f, indent=2)

    return {**context, "plip_results": plip_results, "analysis_dir": analysis_dir}


def _merge_pdb(receptor_pdb: Path, ligand_pdb: Path, out_pdb: Path) -> None:
    rec_lines = [l for l in receptor_pdb.read_text().splitlines() if not l.startswith("END")]
    lig_lines = [l for l in ligand_pdb.read_text().splitlines() if l.startswith(("ATOM", "HETATM"))]
    out_pdb.write_text("\n".join(rec_lines + lig_lines + ["END\n"]))


def _run_plip(complex_pdb: Path, out_dir: Path, docker_image: str) -> None:
    # Get user and group IDs to prevent root-owned files from docker
    uid = subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()
    gid = subprocess.run(["id", "-g"], capture_output=True, text=True).stdout.strip()

    cmd = [
        "docker", "run", "--rm",
        "--user", f"{uid}:{gid}",
        "-v", f"{complex_pdb.parent.resolve()}:/data",
        docker_image,
        "-f", f"/data/{complex_pdb.name}", "-x", "-o", f"/data/{out_dir.name}"
    ]
    subprocess.run(cmd, capture_output=True, text=True)


def _parse_plip_xml(xml_file: Path) -> dict:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        hbonds = len(root.findall(".//hydrogen_bond"))
        hydrophobic = len(root.findall(".//hydrophobic_interaction"))
        pistacks = len(root.findall(".//pi_stack"))
        return {
            "hbonds": hbonds,
            "hydrophobic": hydrophobic,
            "pi_stacking": pistacks
        }
    except Exception as e:
        log.error(f"Failed to parse PLIP XML {xml_file}: {e}")
        return {"hbonds": 0, "hydrophobic": 0, "pi_stacking": 0}
