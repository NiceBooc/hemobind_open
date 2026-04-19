from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QCheckBox, QPushButton
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat

class ConsoleWidget(QWidget):
    COLORS = {
        "INFO":    "#a8d8a8",
        "WARNING": "#f4d03f",
        "ERROR":   "#e74c3c",
        "DEBUG":   "#7f8c8d",
        "DONE":    "#2ecc71",
        "START":   "#3498db",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        self.cb_info = QCheckBox("INFO")
        self.cb_info.setChecked(True)
        self.cb_warn = QCheckBox("WARN")
        self.cb_warn.setChecked(True)
        self.cb_error = QCheckBox("ERROR")
        self.cb_error.setChecked(True)
        self.cb_debug = QCheckBox("DEBUG")
        
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear)

        toolbar.addWidget(self.cb_info)
        toolbar.addWidget(self.cb_warn)
        toolbar.addWidget(self.cb_error)
        toolbar.addWidget(self.cb_debug)
        toolbar.addStretch()
        toolbar.addWidget(btn_clear)
        layout.addLayout(toolbar)

        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background: #0d1117; font-family: monospace;")
        layout.addWidget(self.text_edit)

    @Slot(str, str)
    def append_message(self, level, message):
        # Filter check
        if level == "INFO" and not self.cb_info.isChecked(): return
        if level == "WARNING" and not self.cb_warn.isChecked(): return
        if level == "ERROR" and not self.cb_error.isChecked(): return
        if level == "DEBUG" and not self.cb_debug.isChecked(): return

        format = QTextCharFormat()
        color = self.COLORS.get(level, "#ffffff")
        format.setForeground(QColor(color))

        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"[{level}] {message}\n", format)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def clear(self):
        self.text_edit.clear()
