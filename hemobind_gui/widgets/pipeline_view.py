from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Signal, Qt

class PipelineView(QWidget):
    stage_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        stages = [
            ("s1_prepare", "1. Prepare"),
            ("s2_docking", "2. Docking"),
            ("s3_analyze", "3. PLIP Analyze"),
            ("s4_select",  "4. Select Poses"),
            ("s5",         "5. System Prep"),
            ("s6",         "6. System Build"),
            ("s7",         "7. Molecular Dyn"),
            ("s8",         "8. Trajectory Analysis"),
        ]

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        for stage_id, title in stages:
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 8px; border: none; border-radius: 4px; }
                QPushButton:checked { background-color: #3498db; color: white; }
                QPushButton:hover { background-color: #3d4166; }
            """)
            btn.clicked.connect(lambda checked, s=stage_id: self.stage_selected.emit(s))
            layout.addWidget(btn)
            self.buttons[stage_id] = btn
            self.group.addButton(btn)

        self.buttons["s1_prepare"].setChecked(True)
        layout.addStretch()

    def set_status(self, stage_id, status):
        # status: idle, running, done, failed
        btn = self.buttons.get(stage_id)
        if not btn: return
        
        status_styles = {
            "idle":    "border-left: 5px solid #7f8c8d;",
            "running": "border-left: 5px solid #3498db; font-weight: bold;",
            "done":    "border-left: 5px solid #2ecc71;",
            "failed":  "border-left: 5px solid #e74c3c;"
        }
        
        base_style = """
            QPushButton { text-align: left; padding: 8px; border: none; border-radius: 4px; margin-left: 5px; }
            QPushButton:checked { background-color: #3498db; color: white; }
            QPushButton:hover { background-color: #3d4166; }
        """
        
        btn.setStyleSheet(base_style + status_styles.get(status, ""))
        
        # Update text with status icon
        icons = {"idle": "○", "running": "▶", "done": "✓", "failed": "✗"}
        parts = btn.text().split(" ", 2)
        if len(parts) >= 2:
             btn.setText(f"{parts[0]} {parts[1]} {icons.get(status, ' ')}")
