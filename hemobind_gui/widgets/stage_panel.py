from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

class StagePanel(QWidget):
    config_changed = Signal(dict)

    def __init__(self, stage_id: str, title: str, parent=None):
        super().__init__(parent)
        self.stage_id = stage_id
        self.title = title
        
        self.main_layout = QVBoxLayout(self)
        
        header = QLabel(f"<h2>{title}</h2>")
        self.main_layout.addWidget(header)

    def get_config(self) -> dict:
        raise NotImplementedError

    def set_config(self, cfg: dict):
        raise NotImplementedError

    def validate(self) -> list[str]:
        return []
