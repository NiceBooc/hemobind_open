"""
pipeline.py — Stage orchestrator with checkpointing. (Open Source version)
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from hemobind.config import HemobindConfig
from hemobind.utils.logger import setup_logger, get_logger

STAGES = ["s1_prepare", "s2_docking", "s3_analyze", "s4_select",
          "s5", "s6", "s7", "s8"]

class Pipeline:
    def __init__(self, config: HemobindConfig, run_dir: Path):
        self.config = config
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        log_file = run_dir / "pipeline.log"
        self.log = setup_logger("hemobind", log_file=log_file, level=config.log_level)
        self._write_run_meta()

    def _write_run_meta(self):
        meta = {
            "started": datetime.now().isoformat(),
            "receptor": self.config.receptor,
            "ligands": self.config.ligands,
            "sim_time_ns": self.config.md.sim_time_ns,
        }
        (self.run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))

    def is_done(self, stage: str) -> bool:
        return (self.run_dir / f"{stage}.done").exists()

    def mark_done(self, stage: str):
        (self.run_dir / f"{stage}.done").touch()

    def run(self, from_stage: str | None = None, to_stage: str | None = None, stage_callback=None):
        from_idx = STAGES.index(from_stage) if from_stage else 0
        to_idx = STAGES.index(to_stage) + 1 if to_stage else len(STAGES)
        stages_to_run = STAGES[from_idx:to_idx]

        self.log.info(f"Run dir: {self.run_dir}")
        self.log.info(f"Stages: {stages_to_run}")

        context_file = self.run_dir / "context.json"
        context: dict = {}
        if context_file.exists():
            try:
                raw_context = json.loads(context_file.read_text())
                for k, v in raw_context.items():
                    if isinstance(v, str) and (v.startswith("/") or v.startswith("./")):
                        context[k] = Path(v)
                    elif isinstance(v, dict):
                        context[k] = {nk: Path(nv) if isinstance(nv, str) and (nv.startswith("/") or v.startswith("./")) else nv for nk, nv in v.items()}
                    else:
                        context[k] = v
            except Exception as e:
                self.log.warning(f"Failed to load context.json: {e}")

        for stage in stages_to_run:
            if self.is_done(stage) and not from_stage:
                self.log.info(f"[SKIP] {stage} already done")
                continue

            self.log.info(f"[START] {stage}")
            try:
                fn = self._get_stage_fn(stage)
                context = fn(self.config, self.run_dir, context) or context
                
                def _serializable(obj):
                    if isinstance(obj, Path): return str(obj)
                    if isinstance(obj, dict): return {k: _serializable(v) for k, v in obj.items()}
                    if isinstance(obj, list): return [_serializable(x) for x in obj]
                    return obj
                
                context_file.write_text(json.dumps(_serializable(context), indent=2))
                self.mark_done(stage)
                self.log.info(f"[DONE] {stage}")
                if stage_callback:
                    stage_callback(stage, context)
            except Exception as e:
                self.log.error(f"[FAIL] {stage}: {e}")
                raise

    def _get_stage_fn(self, stage: str):
        if stage == "s1_prepare":
            from hemobind.stages.s1_prepare import run as fn
        elif stage == "s2_docking":
            from hemobind.stages.s2_docking import run as fn
        elif stage == "s3_analyze":
            from hemobind.stages.s3_analyze import run as fn
        elif stage == "s4_select":
            from hemobind.stages.s4_select import run as fn
        elif stage == "s5":
            from hemobind.stages.openmm.s5_prep import run as fn
        elif stage == "s6":
            from hemobind.stages.openmm.s6_build import run as fn
        elif stage == "s7":
            from hemobind.stages.openmm.s7_md import run as fn
        elif stage == "s8":
            from hemobind.stages.s8_analyze_md import run as fn
        else:
            raise ValueError(f"Unknown stage: {stage}")
        return fn
