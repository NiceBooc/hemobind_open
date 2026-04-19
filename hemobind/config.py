"""
config.py — Configuration loading and validation for HemoBind.
"""
from __future__ import annotations
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class DockingConfig:
    mode: str = "blind"                  # blind | targeted
    center: List[float] = field(default_factory=list)
    exhaustiveness: int = 32
    n_poses: int = 11
    tool: str = "adgpu"                  # adgpu | vina


@dataclass
class AnalysisConfig:
    plip_docker_image: str = "pharmai/plip"
    top_n: int = 3
    md_stride: int = 1
    md_topology: str = ""
    md_trajectory: str = ""


@dataclass
class MDConfig:
    cpu_jobs: int = 3
    gpu_index: int = 0
    sim_time_ns: float = 1.0
    box_buffer_ang: float = 15.0
    salt_conc_mol: float = 0.15
    water_model: str = "tip3p"
    ph: float = 7.0
    protein_ff: str = "amber14-all.xml"
    water_ff: str = "amber14/tip3p.xml"
    ligand_ff: str = "openff-2.1.0.offxml"
    ligand_charge_method: str = "am1bcc"  # am1bcc | existing


@dataclass
class HemobindConfig:
    receptor: str = ""
    ligands: List[str] = field(default_factory=list)
    docking: DockingConfig = field(default_factory=DockingConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    md: MDConfig = field(default_factory=MDConfig)
    output_dir: str = "runs/{timestamp}"
    log_level: str = "INFO"

    def validate(self):
        if not self.receptor:
            raise ValueError("receptor path is required in config")
        if not self.ligands:
            raise ValueError("at least one ligand is required in config")
        if not Path(self.receptor).exists():
            raise FileNotFoundError(f"Receptor not found: {self.receptor}")
        for lig in self.ligands:
            if not Path(lig).exists():
                raise FileNotFoundError(f"Ligand not found: {lig}")


def load_config(path: str | Path) -> HemobindConfig:
    """Load config from YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    cfg = HemobindConfig()
    cfg.receptor = raw.get("receptor", "")
    cfg.ligands = raw.get("ligands", [])
    cfg.output_dir = raw.get("output_dir", "runs/{timestamp}")
    cfg.log_level = raw.get("log_level", "INFO")

    if "docking" in raw:
        d = raw["docking"]
        cfg.docking = DockingConfig(
            mode=d.get("mode", "blind"),
            center=d.get("center", []),
            exhaustiveness=d.get("exhaustiveness", 32),
            n_poses=d.get("n_poses", 11),
            tool=d.get("tool", "adgpu"),
        )

    if "analysis" in raw:
        a = raw["analysis"]
        cfg.analysis = AnalysisConfig(
            plip_docker_image=a.get("plip_docker_image", "toni/plip"),
            top_n=a.get("top_n", 3),
            md_stride=a.get("md_stride", 1),
            md_topology=a.get("md_topology", ""),
            md_trajectory=a.get("md_trajectory", ""),
        )

    if "md" in raw:
        m = raw["md"]
        cfg.md = MDConfig(
            cpu_jobs=m.get("cpu_jobs", 3),
            gpu_index=m.get("gpu_index", 0),
            sim_time_ns=m.get("sim_time_ns", 1.0),
            box_buffer_ang=m.get("box_buffer_ang", 15.0),
            salt_conc_mol=m.get("salt_conc_mol", 0.15),
            water_model=m.get("water_model", "tip3p"),
            ph=m.get("ph", 7.0),
            protein_ff=m.get("protein_ff", "amber14-all.xml"),
            water_ff=m.get("water_ff", "amber14/tip3p.xml"),
            ligand_ff=m.get("ligand_ff", "openff-2.1.0.offxml"),
            ligand_charge_method=m.get("ligand_charge_method", "am1bcc"),
        )

    return cfg
