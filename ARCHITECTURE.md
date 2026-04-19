# HemoBind Open Architecture & Developer Guide

HemoBind Open is designed as a modular, extensible pipeline for molecular modeling using exclusively open-source tools.

## Core Philosophy

HemoBind follows a **Separation of Concerns** principle:
1.  **Core Stages (`hemobind/stages/`)**: Pure Python logic that performs scientific calculations.
2.  **GUI Layer (`hemobind_gui/`)**: A PySide6 wrapper for configuration and visualization.
3.  **Config System (`hemobind/config.py`)**: A centralized, type-safe configuration schema.

## Module Structure

### 1. The Pipeline Orchestrator (`hemobind/pipeline.py`)
The `Pipeline` class manages the execution logic and state:
- Maintains a list of ordered stages (`STAGES`).
- Manages a **Context Object** (`context.json`) passed between stages.
- Implements **Checkpointing** via success files (`.done`).

### 2. MD Engine Implementation
HemoBind Open is powered by the **OpenMM** ecosystem:
- `hemobind/stages/openmm/s5_prep.py`: Structure cleaning via `PDBFixer`.
- `hemobind/stages/openmm/s6_build.py`: Force-field assignment via `OpenFF` (Sage/Amber).
- `hemobind/stages/openmm/s7_md.py`: Simulation execution via `OpenMM`.

### 3. Stage Implementation Pattern
Every stage in `hemobind/stages/` implements a `run` function:
```python
def run(config: HemobindConfig, run_dir: Path, context: dict) -> dict:
    # 1. Perform calculations
    # 2. Update context
    return context
```

## GUI Interaction (`hemobind_gui/`)

- **Worker Thread**: `PipelineWorker` runs the scientific code in the background.
- **Config Panels**: Located in `widgets/panels/`. They translate UI state into `HemobindConfig`.

## Extension Guide

### How to add a new Stage
1.  Create `hemobind/stages/sX_new_stage.py`.
2.  Define the `run` function.
3.  Add the stage name to `STAGES` in `hemobind/pipeline.py`.
4.  Update `Pipeline._get_stage_fn` to include the new import.
