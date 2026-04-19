from PySide6.QtWidgets import QFormLayout, QSpinBox, QComboBox
from hemobind_gui.widgets.stage_panel import StagePanel

class DockingPanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s2_docking", "Molecular Docking Settings", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.cb_tool = QComboBox()
        self.cb_tool.addItems(["adgpu", "vina"])
        form.addRow("Docking Tool:", self.cb_tool)
        
        self.sp_runs = QSpinBox()
        self.sp_runs.setRange(1, 1000)
        self.sp_runs.setValue(30)
        form.addRow("Number of Runs:", self.sp_runs)
        
        self.sp_poses = QSpinBox()
        self.sp_poses.setRange(1, 100)
        self.sp_poses.setValue(10)
        form.addRow("Max Poses:", self.sp_poses)
        
        self.sp_exhaust = QSpinBox()
        self.sp_exhaust.setRange(1, 128)
        self.sp_exhaust.setValue(32)
        self.sp_exhaust.setEnabled(False) # Only for Vina
        form.addRow("Exhaustiveness (Vina):", self.sp_exhaust)
        
        self.cb_tool.currentTextChanged.connect(lambda t: self.sp_exhaust.setEnabled(t == "vina"))
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "tool": self.cb_tool.currentText(),
            "n_runs": self.sp_runs.value(),
            "n_poses": self.sp_poses.value(),
            "exhaustiveness": self.sp_exhaust.value()
        }

    def set_config(self, cfg: dict):
        self.cb_tool.setCurrentText(cfg.get("tool", "adgpu"))
        self.sp_runs.setValue(cfg.get("n_runs", 30))
        self.sp_poses.setValue(cfg.get("n_poses", 10))
        self.sp_exhaust.setValue(cfg.get("exhaustiveness", 32))
