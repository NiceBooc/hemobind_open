from PySide6.QtWidgets import QFormLayout, QSpinBox, QLineEdit
from hemobind_gui.widgets.stage_panel import StagePanel

class AnalyzePanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s3_analyze", "PLIP Interaction Analysis", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.le_image = QLineEdit("pharmai/plip")
        form.addRow("PLIP Docker Image:", self.le_image)
        
        self.sp_top_n = QSpinBox()
        self.sp_top_n.setRange(1, 50)
        self.sp_top_n.setValue(3)
        form.addRow("Analyze Top N Poses:", self.sp_top_n)
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "plip_docker_image": self.le_image.text(),
            "top_n": self.sp_top_n.value()
        }

    def set_config(self, cfg: dict):
        self.le_image.setText(cfg.get("plip_docker_image", "pharmai/plip"))
        self.sp_top_n.setValue(cfg.get("top_n", 3))
