from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import Signal, Qt
from pathlib import Path

class FileInputWidget(QWidget):
    path_changed = Signal(str)

    def __init__(self, label: str, mode: str = "file", filter: str = "All Files (*)", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.filter = filter
        self.setup_ui(label)

    def setup_ui(self, label_text):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label_text)
        self.label.setMinimumWidth(100)
        
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.path_changed.emit)
        
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(btn_browse)

    def browse(self):
        if self.mode == "file":
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.filter)
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")

        if path:
            self.line_edit.setText(path)

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)
