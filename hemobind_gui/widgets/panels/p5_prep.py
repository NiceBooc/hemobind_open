from PySide6.QtWidgets import QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QComboBox, QWidget
from hemobind_gui.widgets.stage_panel import StagePanel

class PrepPanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s5", "MD Setup & Prep", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        # Common Settings
        self.sp_ph = QDoubleSpinBox(); self.sp_ph.setRange(0, 14); self.sp_ph.setValue(7.0)
        form.addRow("Protonation pH:", self.sp_ph)
        
        self.cb_charge = QComboBox()
        self.cb_charge.addItems(["am1bcc", "existing"])
        form.addRow("Ligand Charge Method:", self.cb_charge)
        
        self.cb_fill = QCheckBox("Fill side chains"); self.cb_fill.setChecked(True)
        form.addRow(self.cb_fill)
        
        self.sp_parallel = QSpinBox(); self.sp_parallel.setRange(1, 64); self.sp_parallel.setValue(3)
        form.addRow("Parallel Jobs:", self.sp_parallel)
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "ph": self.sp_ph.value(),
            "fill_sidechains": self.cb_fill.isChecked(),
            "parallel_jobs": self.sp_parallel.value(),
            "ligand_charge_method": self.cb_charge.currentText()
        }

    def set_config(self, cfg: dict):
        self.sp_ph.setValue(cfg.get("ph", 7.0))
        self.cb_fill.setChecked(cfg.get("fill_sidechains", True))
        self.sp_parallel.setValue(cfg.get("parallel_jobs", 3))
        self.cb_charge.setCurrentText(cfg.get("ligand_charge_method", "am1bcc"))
