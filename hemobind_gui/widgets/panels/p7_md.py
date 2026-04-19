from PySide6.QtWidgets import QFormLayout, QDoubleSpinBox, QSpinBox
from hemobind_gui.widgets.stage_panel import StagePanel

class MDPanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s7_md", "Molecular Dynamics (Desmond)", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.sp_time = QDoubleSpinBox(); self.sp_time.setRange(0.001, 10000); self.sp_time.setValue(1.0)
        form.addRow("Sim Time (ns):", self.sp_time)
        
        self.sp_gpu = QSpinBox(); self.sp_gpu.setRange(0, 8); self.sp_gpu.setValue(0)
        form.addRow("GPU Index:", self.sp_gpu)
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "sim_time_ns": self.sp_time.value(),
            "gpu_index": self.sp_gpu.value()
        }

    def set_config(self, cfg: dict):
        self.sp_time.setValue(cfg.get("sim_time_ns", 1.0))
        self.sp_gpu.setValue(cfg.get("gpu_index", 0))
