# HemoBind (Open Source Edition)

HemoBind is a specialized tool for protein-ligand docking and Molecular Dynamics (MD) trajectory analysis. It is designed to be lightweight, portable, and hardware-agnostic.

## Features

- **Automated Docking**: Support for AutoDock-GPU and Vina.
- **MD Simulation**: Native OpenMM integration for GPU-accelerated MD.
- **Trajectory Analysis**: 
  - RMSD calculation for protein and ligand.
  - Interaction fingerprinting using ProLIF.
  - Automated visualization of binding interactions.
- **Hardware Agnostic**: Supports NVIDIA GPUs (CUDA), AMD GPUs (OpenCL), and CPU-only execution.

## Quick Start (Linux)

To run HemoBind on any Linux distribution, simply clone the repository and execute the bootstrapper:

```bash
git clone https://github.com/NiceBooc/hemobind_open.git
cd hemobind_open
./run.sh
```

The bootstrapper will automatically:
1. Download a portable package manager (Micromamba).
2. Create an isolated scientific environment with all dependencies.
3. Launch the graphical user interface.

## Requirements

- Linux (Ubuntu, Debian, CentOS, etc.)
- NVIDIA drivers (optional, for CUDA acceleration)
- Git and Curl

## License

MIT License. See LICENSE for details.
