from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel, QProgressBar, QVBoxLayout
from PySide6.QtCore import Signal

class RunControlWidget(QWidget):
    run_requested = Signal(str, str) # from, to
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        controls = QHBoxLayout()
        
        controls.addWidget(QLabel("From:"))
        self.cb_from = QComboBox()
        controls.addWidget(self.cb_from)
        
        controls.addWidget(QLabel("To:"))
        self.cb_to = QComboBox()
        controls.addWidget(self.cb_to)
        
        stages = ["s1_prepare", "s2_docking", "s3_analyze", "s4_select", "s5", "s6", "s7", "s8"]
        self.cb_from.addItems(stages)
        self.cb_to.addItems(stages)
        self.cb_to.setCurrentIndex(len(stages)-1)
        
        self.btn_run = QPushButton("▶ Run Pipeline")
        self.btn_run.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 10px;")
        self.btn_run.clicked.connect(self._on_run)
        controls.addWidget(self.btn_run)
        
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested)
        controls.addWidget(self.btn_stop)
        
        main_layout.addLayout(controls)
        
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

    def _on_run(self):
        self.run_requested.emit(self.cb_from.currentText(), self.cb_to.currentText())

    def set_running(self, running: bool):
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        if not running:
            self.progress_bar.setValue(0)

    def set_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
