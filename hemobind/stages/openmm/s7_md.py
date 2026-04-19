"""
s7_md.py — OpenMM Molecular Dynamics Simulation.
"""
import concurrent.futures
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.logger import get_logger

log = get_logger("hemobind.s7")


def run_simulation(sys_dict: dict, config: HemobindConfig, output_dir: Path) -> dict:
    import openmm
    import openmm.app as app
    import openmm.unit as unit
    
    name = sys_dict["name"]
    pdb_path = sys_dict["solvated_pdb"]
    sys_path = sys_dict["system_xml"]
    
    out_dcd = output_dir / f"{name}_prod.dcd"
    out_log = output_dir / f"{name}_md.csv"
    out_state = output_dir / f"{name}_final.xml"
    
    if out_dcd.exists() and out_log.exists():
        log.info(f"Simulation {name} already completed.")
        return {**sys_dict, "trajectory": out_dcd, "md_log": out_log}

    log.info(f"Starting MD simulation for {name} on GPU {config.md.gpu_index}...")

    # Load System and Topology
    pdb = app.PDBFile(str(pdb_path))
    with open(sys_path, 'r') as f:
        system = openmm.XmlSerializer.deserialize(f.read())

    # Setup Integrator
    temperature = 300 * unit.kelvin
    friction = 1.0 / unit.picosecond
    dt = 2.0 * unit.femtoseconds
    integrator = openmm.LangevinMiddleIntegrator(temperature, friction, dt)

    # Set GPU Platform
    try:
        platform = openmm.Platform.getPlatformByName('CUDA')
        properties = {'DeviceIndex': str(config.md.gpu_index), 'Precision': 'mixed'}
    except Exception as e:
        log.warning(f"CUDA platform not available, falling back to CPU: {e}")
        platform = openmm.Platform.getPlatformByName('CPU')
        properties = {}

    simulation = app.Simulation(pdb.topology, system, integrator, platform, properties)
    simulation.context.setPositions(pdb.positions)

    # 1. Minimization
    log.info(f"[{name}] Minimizing energy...")
    simulation.minimizeEnergy()

    # 2. Equilibration (NVT)
    # 100 ps NVT
    log.info(f"[{name}] Running 100ps NVT equilibration...")
    simulation.context.setVelocitiesToTemperature(temperature)
    simulation.step(50000)

    # 3. Equilibration (NPT)
    # Add MonteCarloBarostat for NPT
    barostat = openmm.MonteCarloBarostat(1.0*unit.bar, temperature, 25)
    system.addForce(barostat)
    # Re-initialize simulation context with new force
    simulation.context.reinitialize(preserveState=True)
    
    log.info(f"[{name}] Running 100ps NPT equilibration...")
    simulation.step(50000)

    # 4. Production
    total_time_ns = config.md.sim_time_ns
    steps = int((total_time_ns * 1000 * unit.picosecond) / dt)
    
    # Save every 10ps
    report_interval = int((10 * unit.picosecond) / dt)
    
    simulation.reporters.append(app.DCDReporter(str(out_dcd), report_interval))
    simulation.reporters.append(app.StateDataReporter(
        str(out_log), report_interval, step=True, time=True,
        potentialEnergy=True, temperature=True, density=True, progress=True,
        remainingTime=True, speed=True, totalSteps=steps, separator='\t'
    ))

    log.info(f"[{name}] Running {total_time_ns}ns Production MD ({steps} steps)...")
    simulation.step(steps)

    # Save final state
    simulation.saveState(str(out_state))

    log.info(f"[{name}] Production MD finished.")
    return {**sys_dict, "trajectory": out_dcd, "md_log": out_log, "final_state": out_state}


def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    md_setup_dir: Path = context.get("md_setup_dir", run_dir / "md_setup")
    built_systems: list[dict] = context.get("built_systems", [])
    if not built_systems:
        raise ValueError("No built systems found in context")

    md_results = []

    log.info(f"Running OpenMM MD on {len(built_systems)} candidates...")

    # GPU jobs usually run sequentially or mapped to different GPUs.
    # For now, we run them sequentially on the specified GPU to avoid OOM.
    for sys in built_systems:
        try:
            res = run_simulation(sys, config, md_setup_dir)
            md_results.append(res)
        except Exception as e:
            log.error(f"MD failed for {sys['name']}: {e}")
            raise

    log.info("Molecular Dynamics completed for all selected poses.")
    return {**context, "md_results": md_results}
