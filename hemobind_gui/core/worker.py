import logging
from PySide6.QtCore import QThread, Signal
from hemobind.pipeline import Pipeline
from hemobind.config import HemobindConfig
from pathlib import Path

class GuiLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(record.levelname, msg)

class PipelineWorker(QThread):
    log_message = Signal(str, str)
    stage_started = Signal(str)
    stage_done = Signal(str)
    stage_failed = Signal(str, str)
    finished = Signal(bool)

    def __init__(self, config: HemobindConfig, run_dir: Path, from_stage=None, to_stage=None):
        super().__init__()
        self.config = config
        self.run_dir = run_dir
        self.from_stage = from_stage
        self.to_stage = to_stage
        self._is_running = True

    def run(self):
        # Setup logging redirection
        handler = GuiLogHandler(self.log_message)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        
        logger = logging.getLogger("hemobind")
        logger.addHandler(handler)
        
        try:
            pipeline = Pipeline(self.config, self.run_dir)
            
            def on_stage_started(stage_id):
                self.stage_started.emit(stage_id)
            
            def on_stage_done(stage_id, context):
                self.stage_done.emit(stage_id)
                # You could also emit context if needed
            
            # Patch _get_stage_fn for started signal
            orig_get = pipeline._get_stage_fn
            def patched_get(stage_id):
                on_stage_started(stage_id)
                return orig_get(stage_id)
            pipeline._get_stage_fn = patched_get

            # Run pipeline with done callback
            pipeline.run(
                from_stage=self.from_stage, 
                to_stage=self.to_stage,
                stage_callback=on_stage_done
            )
            self.finished.emit(True)
            
        except Exception as e:
            self.log_message.emit("ERROR", str(e))
            self.finished.emit(False)
        finally:
            logger.removeHandler(handler)

    def stop(self):
        self._is_running = False
        # Note: Core pipeline doesn't support easy interruption yet, 
        # but we can at least stop signal emission or wait for current stage.
