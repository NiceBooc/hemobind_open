from PySide6.QtWidgets import QFormLayout, QDoubleSpinBox, QSpinBox
from hemobind_gui.widgets.stage_panel import StagePanel

class SelectPanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s4_select", "Pose Selection & Scoring", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.sp_w_energy = QDoubleSpinBox(); self.sp_w_energy.setRange(-10, 10); self.sp_w_energy.setValue(-1.0)
        self.sp_w_hbond = QDoubleSpinBox(); self.sp_w_hbond.setRange(-10, 10); self.sp_w_hbond.setValue(5.0)
        self.sp_w_hydro = QDoubleSpinBox(); self.sp_w_hydro.setRange(-10, 10); self.sp_w_hydro.setValue(0.3)
        
        form.addRow("Weight ΔG:", self.sp_w_energy)
        form.addRow("Weight H-bond:", self.sp_w_hbond)
        form.addRow("Weight Hydrophobic:", self.sp_w_hydro)
        
        self.sp_radius = QDoubleSpinBox(); self.sp_radius.setRange(0.1, 10.0); self.sp_radius.setValue(3.0)
        form.addRow("Cluster Radius (Å):", self.sp_radius)
        
        self.sp_top_n = QSpinBox(); self.sp_top_n.setRange(1, 20); self.sp_top_n.setValue(2)
        form.addRow("Select Top N:", self.sp_top_n)
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "w_energy": self.sp_w_energy.value(),
            "w_hbond": self.sp_w_hbond.value(),
            "w_hydro": self.sp_w_hydro.value(),
            "cluster_radius": self.sp_radius.value(),
            "top_n": self.sp_top_n.value()
        }

    def set_config(self, cfg: dict):
        self.sp_w_energy.setValue(cfg.get("w_energy", -1.0))
        self.sp_w_hbond.setValue(cfg.get("w_hbond", 5.0))
        self.sp_w_hydro.setValue(cfg.get("w_hydro", 0.3))
        self.sp_radius.setValue(cfg.get("cluster_radius", 3.0))
        self.sp_top_n.setValue(cfg.get("top_n", 2))
