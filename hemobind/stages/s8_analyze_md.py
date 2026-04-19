import os
import json
from pathlib import Path
import pandas as pd
import MDAnalysis as mda
from MDAnalysis.analysis import rms
import prolif as plf
import matplotlib.pyplot as plt
import seaborn as sns
from hemobind.config import HemobindConfig
from hemobind.utils.logger import get_logger

log = get_logger(__name__)

def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    log.info("Starting Trajectory Analysis (Stage 8)...")
    
    # 1. Identify Topology and Trajectory
    # Use config overrides if provided, else look in context
    topo_path = Path(config.analysis.md_topology) if config.analysis.md_topology else context.get("md_topology")
    trj_path = Path(config.analysis.md_trajectory) if config.analysis.md_trajectory else context.get("md_trajectory")
    
    if not topo_path or not trj_path:
        # Try to guess if context is missing (manual run)
        log.warning("MD paths not found in context. Looking in run_dir...")
        cms_files = list(run_dir.glob("*.cms"))
        if cms_files:
            topo_path = cms_files[0]
            trj_dir = run_dir / (topo_path.stem + "_trj")
            if trj_dir.exists():
                trj_path = trj_dir
    
    if not topo_path or not trj_path:
        raise FileNotFoundError(f"Could not find topology or trajectory in {run_dir}")

    log.info(f"Topology: {topo_path}")
    log.info(f"Trajectory: {trj_path}")

    # 2. Load Universe
    u = mda.Universe(str(topo_path), str(trj_path))
    log.info(f"Loaded Universe with {len(u.trajectory)} frames")

    # Stride
    stride = config.analysis.md_stride or 1
    
    # 3. Align Trajectory
    ref = mda.Universe(str(topo_path))
    alignment = rms.AlignTraj(u, ref, select="backbone", in_memory=True)
    alignment.run()
    log.info("Trajectory aligned to backbone.")

    # 4. RMSD Calculation
    log.info("Calculating RMSD...")
    prot_rmsd = rms.RMSD(u, ref, select="backbone")
    prot_rmsd.run()
    
    # Ligand selection
    lig_selection = "resname LIG"
    if not u.select_atoms(lig_selection):
        # Fallback if resname is different
        log.warning("Residue 'LIG' not found. Using context['ligand_resname']")
        lig_selection = f"resname {context.get('ligand_resname', 'UNK')}"

    lig_rmsd = rms.RMSD(u, ref, select=lig_selection)
    lig_rmsd.run()

    # Save RMSD data
    rmsd_df = pd.DataFrame({
        "Frame": prot_rmsd.results.rmsd[:, 1],
        "Protein_Backbone": prot_rmsd.results.rmsd[:, 2],
        "Ligand": lig_rmsd.results.rmsd[:, 2]
    })
    rmsd_csv = run_dir / "rmsd_analysis.csv"
    rmsd_df.to_csv(rmsd_csv, index=False)

    # 5. ProLIF Interaction Analysis
    log.info("Performing Interaction Fingerprinting (ProLIF)...")
    lig_atoms = u.select_atoms(lig_selection)
    prot_atoms = u.select_atoms("protein")
    
    # Create ProLIF molecules
    lig_mol = plf.Molecule.from_mda(lig_atoms)
    prot_mol = plf.Molecule.from_mda(prot_atoms)
    
    fp = plf.Fingerprint()
    fp.run(u.trajectory[::stride], lig_atoms, prot_atoms)
    
    df = fp.to_dataframe()
    # Flatten the multi-index columns for easier reading
    df.columns = [f"{res}_{int_type}" for lig, res, int_type in df.columns]
    
    int_csv = run_dir / "interactions_over_time.csv"
    df.to_csv(int_csv)
    
    # Interaction Frequencies
    occ = df.mean().sort_values(ascending=False)
    occ_csv = run_dir / "interaction_frequencies.csv"
    occ.to_csv(occ_csv)

    # 6. Visualization
    log.info("Generating plots...")
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=rmsd_df, x="Frame", y="Protein_Backbone", label="Protein Backbone")
    sns.lineplot(data=rmsd_df, x="Frame", y="Ligand", label="Ligand")
    plt.title("RMSD over Time")
    plt.ylabel("RMSD (Å)")
    plt.savefig(run_dir / "plot_rmsd.png")
    plt.close()

    # Heatmap of top interactions
    if not occ.empty:
        top_interactions = occ.head(15).index
        plt.figure(figsize=(12, 8))
        sns.heatmap(df[top_interactions].T, cmap="Greens", cbar=False)
        plt.title("Top 15 Protein-Ligand Interactions Over Time")
        plt.xlabel("Frame")
        plt.savefig(run_dir / "plot_interactions_heatmap.png")
        plt.close()

    context["analysis_md"] = {
        "rmsd_csv": rmsd_csv,
        "interactions_csv": int_csv,
        "frequencies_csv": occ_csv,
        "plots": [
            str(run_dir / "plot_rmsd.png"),
            str(run_dir / "plot_interactions_heatmap.png")
        ]
    }
    
    log.info(f"Analysis complete. Results saved in {run_dir}")
    return context
