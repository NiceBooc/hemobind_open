from PySide6.QtWidgets import QFormLayout, QSpinBox, QCheckBox, QLabel, QVBoxLayout, QScrollArea, QWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from hemobind_gui.widgets.stage_panel import StagePanel
from hemobind_gui.widgets.file_input import FileInputWidget

class AnalyzeMDPanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s8", "Trajectory Analysis", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.sp_stride = QSpinBox()
        self.sp_stride.setRange(1, 1000)
        self.sp_stride.setValue(1)
        form.addRow("Analysis Stride (Frames):", self.sp_stride)
        
        self.cb_plots = QCheckBox("Generate Visualization Plots")
        self.cb_plots.setChecked(True)
        form.addRow(self.cb_plots)
        
        self.fs_topology = FileInputWidget("Topology File (CMS/PDB):", mode="file")
        self.fs_trajectory = FileInputWidget("Trajectory Dir/File:", mode="dir")
        
        form.addRow(self.fs_topology)
        form.addRow(self.fs_trajectory)

        self.main_layout.addLayout(form)
        
        self.results_info = QLabel("Results will appear here after run.")
        self.results_info.setWordWrap(True)
        self.main_layout.addWidget(self.results_info)
        
        # Scroll area for plots
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.scroll.setWidget(self.plot_container)
        self.main_layout.addWidget(self.scroll)
        
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "analysis_stride": self.sp_stride.value(),
            "generate_plots": self.cb_plots.isChecked(),
            "custom_topology": self.fs_topology.text(),
            "custom_trajectory": self.fs_trajectory.text()
        }

    def set_config(self, cfg: dict):
        self.sp_stride.setValue(cfg.get("analysis_stride", 1))
        self.cb_plots.setChecked(cfg.get("generate_plots", True))
        self.fs_topology.setText(cfg.get("custom_topology", ""))
        self.fs_trajectory.setText(cfg.get("custom_trajectory", ""))

    def update_results(self, context: dict):
        res = context.get("analysis_md")
        if not res:
            return
            
        info = f"RMSD: {res['rmsd_csv']}\nInteractions: {res['interactions_csv']}"
        self.results_info.setText(info)
        
        # Clear old plots
        while self.plot_layout.count():
            child = self.plot_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Show new plots
        for plot_path in res.get("plots", []):
            label = QLabel()
            pixmap = QPixmap(plot_path)
            label.setPixmap(pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.plot_layout.addWidget(label)
