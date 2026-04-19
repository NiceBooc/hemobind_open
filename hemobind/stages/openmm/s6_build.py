"""
s6_build.py — OpenMM System Builder (Solvation and Parameterization).
"""
import concurrent.futures
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s6")

def build_system(sys_dict: dict, config: HemobindConfig, output_dir: Path) -> dict:
    import openmm.app as app
    from openmm.app import PDBFile, Modeller, ForceField
    from openff.toolkit.topology import Molecule
    from openmmforcefields.generators import SystemGenerator
    import openmm.unit as unit

    name = sys_dict["name"]
    rec_path = sys_dict["receptor"]
    lig_path = sys_dict["ligand"]
    
    out_pdb = output_dir / f"{name}_solvated.pdb"
    out_sys = output_dir / f"{name}_system.xml"
    
    if out_pdb.exists() and out_sys.exists():
        log.info(f"System {name} already built.")
        return {**sys_dict, "solvated_pdb": out_pdb, "system_xml": out_sys}

    log.info(f"Building system for {name}...")

    # 1. Load Protein
    pdb = PDBFile(str(rec_path))

    # 2. Load Ligand
    # openff-toolkit can read mol2 directly
    ligand = Molecule.from_file(str(lig_path), file_format="MOL2")
    
    if config.md.ligand_charge_method == "existing":
        log.info(f"Using existing charges for {name}...")
        # OpenFF will use the partial charges already in the Molecule object 
        # (loaded from MOL2) if we don't call generate_conformers/assign_partial_charges.
        if not ligand.partial_charges:
            log.warning(f"No partial charges found in {lig_path.name}! Falling back to am1bcc.")
            ligand.assign_partial_charges(partial_charge_method='am1bcc')
    else:
        log.info(f"Calculating AM1-BCC charges for {name}...")
        ligand.assign_partial_charges(partial_charge_method='am1bcc')
    forcefield_kwargs = {
        'constraints': app.HBonds,
        'rigidWater': True,
        'removeCMMotion': False,
        'hydrogenMass': 1.5 * unit.amu
    }
    
    system_generator = SystemGenerator(
        forcefields=[config.md.protein_ff, config.md.water_ff],
        small_molecule_forcefield=config.md.ligand_ff.replace(".offxml", ""), # openmmforcefields uses string names like 'openff-2.1.0'
        molecules=[ligand],
        forcefield_kwargs=forcefield_kwargs
    )

    # 4. Combine Topologies using Modeller
    modeller = Modeller(pdb.topology, pdb.positions)
    
    # Add ligand to modeller
    lig_top = ligand.to_topology().to_openmm()
    lig_pos = ligand.conformers[0]
    modeller.add(lig_top, lig_pos)

    # 5. Solvate
    log.info(f"Adding solvent ({config.md.water_model}) with {config.md.box_buffer_ang}A buffer...")
    # Map config water model to openmm solvent name
    water_model_map = {"tip3p": "tip3p", "tip4pew": "tip4pew", "spce": "spce"}
    solvent_name = water_model_map.get(config.md.water_model.lower(), "tip3p")
    
    system_generator.forcefield.loadFile(config.md.water_ff)
    
    modeller.addSolvent(
        system_generator.forcefield,
        model=solvent_name,
        padding=config.md.box_buffer_ang * unit.angstroms,
        ionicStrength=config.md.salt_conc_mol * unit.molar,
        positiveIon='Na+', negativeIon='Cl-'
    )

    # 6. Create System
    log.info(f"Parameterizing {name} (calculating AM1-BCC charges if needed)...")
    system = system_generator.create_system(modeller.topology)

    # 7. Save Outputs
    with open(out_pdb, 'w') as f:
        PDBFile.writeFile(modeller.topology, modeller.positions, f)

    import openmm
    with open(out_sys, 'w') as f:
        f.write(openmm.XmlSerializer.serialize(system))

    log.info(f"Finished building {name}.")
    return {**sys_dict, "solvated_pdb": out_pdb, "system_xml": out_sys}


def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    md_setup_dir: Path = context.get("md_setup_dir", run_dir / "md_setup")
    prepped_systems: list[dict] = context.get("prepped_systems", [])
    if not prepped_systems:
        raise ValueError("No prepped systems found in context")

    built_systems = []

    log.info(f"Running System Builder on {len(prepped_systems)} candidates "
             f"({config.md.cpu_jobs} parallel workers)...")

    # Due to OpenFF charge generation (AM1-BCC) taking a lot of memory and some issues with ProcessPool,
    # ThreadPool is safer, but might be bound by GIL. Still, calling external tools is usually fine.
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.md.cpu_jobs) as executor:
        futures = {executor.submit(build_system, sys, config, md_setup_dir): sys for sys in prepped_systems}
        for future in concurrent.futures.as_completed(futures):
            sys = futures[future]
            try:
                result = future.result()
                built_systems.append(result)
            except Exception as e:
                log.error(f"System Builder failed for {sys['name']}: {e}")
                raise

    log.info("System Building completed for all selected poses.")
    return {**context, "built_systems": built_systems}
