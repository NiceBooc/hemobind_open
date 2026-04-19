from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from hemobind_gui.core.dependency_checker import DependencyChecker

class DependencyStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = DependencyChecker()
        self.tool_labels = {}
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("Dependency Status:")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        tools = ["obabel", "adgpu", "docker", "openmm", "pdbfixer", "openff"]
        for tool in tools:
            h_layout = QHBoxLayout()
            lbl_name = QLabel(f"{tool}:")
            lbl_status = QLabel("Checking...")
            h_layout.addWidget(lbl_name)
            h_layout.addWidget(lbl_status)
            h_layout.addStretch()
            layout.addLayout(h_layout)
            self.tool_labels[tool] = lbl_status

        btn_refresh = QPushButton("Re-check")
        btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(btn_refresh)

    def refresh(self, config_paths=None):
        results = self.checker.check_all(config_paths)
        for tool, res in results.items():
            if tool in self.tool_labels:
                lbl = self.tool_labels[tool]
                if res.ok:
                    lbl.setText("✓ OK")
                    lbl.setStyleSheet("color: #2ecc71;")
                    lbl.setToolTip(res.version or res.message)
                else:
                    lbl.setText("✗ Missing")
                    lbl.setStyleSheet("color: #e74c3c;")
                    lbl.setToolTip(res.message)
