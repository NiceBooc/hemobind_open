from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QDockWidget, QStackedWidget, QLabel, QPushButton, 
                               QStatusBar, QMenuBar)
from PySide6.QtCore import Qt, QSettings
from hemobind_gui.core.session import SessionManager
from pathlib import Path
import json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HemoBind GUI")
        self.resize(1200, 800)
        
        # Paths
        self.config_dir = Path.home() / ".config" / "hemobind"
        self.session_manager = SessionManager(self.config_dir)
        
        # Settings
        self.qsettings = QSettings("HemoBind", "HemoBindGUI")
        self.app_settings = {
            "adgpu": self.qsettings.value("adgpu", "adgpu"),
            "docker": self.qsettings.value("docker", "docker"),
        }
        
        self.setup_ui()
        self.load_last_session()
        
    def setup_ui(self):
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        
        # Stacked widget for stage panels
        self.stacked_widget = QStackedWidget()
        
        from hemobind_gui.widgets.panels.p1_prepare import PreparePanel
        from hemobind_gui.widgets.panels.p2_docking import DockingPanel
        from hemobind_gui.widgets.panels.p3_analyze import AnalyzePanel
        from hemobind_gui.widgets.panels.p4_select import SelectPanel
        from hemobind_gui.widgets.panels.p5_prep import PrepPanel
        from hemobind_gui.widgets.panels.p6_build import BuildPanel
        from hemobind_gui.widgets.panels.p7_md import MDPanel
        
        from hemobind_gui.widgets.panels.p8_analyze_md import AnalyzeMDPanel
        
        self.panels = {
            "s1_prepare": PreparePanel(),
            "s2_docking": DockingPanel(),
            "s3_analyze": AnalyzePanel(),
            "s4_select": SelectPanel(),
            "s5": PrepPanel(),
            "s6": BuildPanel(),
            "s7": MDPanel(),
            "s8": AnalyzeMDPanel(),
        }
        
        for panel in self.panels.values():
            self.stacked_widget.addWidget(panel)
            
        self.central_layout.addWidget(self.stacked_widget)
        
        # Run control
        from hemobind_gui.widgets.run_control import RunControlWidget
        self.run_control = RunControlWidget()
        self.run_control.run_requested.connect(self.run_pipeline)
        self.central_layout.addWidget(self.run_control)
        
        # Setup Docks
        self.setup_docks()
        
        # Setup Menu
        self.setup_menu()
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
        
    def setup_docks(self):
        # Left Dock: Pipeline View
        self.left_dock = QDockWidget("Pipeline Control", self)
        self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        
        from hemobind_gui.widgets.pipeline_view import PipelineView
        self.pipeline_view = PipelineView()
        self.pipeline_view.stage_selected.connect(self.switch_stage)
        left_layout.addWidget(self.pipeline_view)
        
        left_layout.addStretch()
        
        from hemobind_gui.widgets.dependency_status import DependencyStatusWidget
        self.dep_status = DependencyStatusWidget()
        left_layout.addWidget(self.dep_status)
        
        self.left_dock.setWidget(left_container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        
        # Bottom Dock: Console
        self.bottom_dock = QDockWidget("Console", self)
        self.bottom_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        from hemobind_gui.widgets.console_widget import ConsoleWidget
        self.console = ConsoleWidget()
        self.bottom_dock.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        
    def setup_menu(self):
        self.menu_bar = self.menuBar()
        
        # File Menu
        file_menu = self.menu_bar.addMenu("&File")
        file_menu.addAction("New Session", self.new_session)
        file_menu.addAction("Open Session...", self.open_session)
        file_menu.addAction("Save Session", self.save_session)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Run Menu
        run_menu = self.menu_bar.addMenu("&Run")
        run_menu.addAction("Run Full Pipeline", lambda: self.run_pipeline("s1_prepare", "s8"))
        run_menu.addAction("Open Run Directory", self.open_run_dir)
        
        # Tools Menu
        tools_menu = self.menu_bar.addMenu("&Tools")
        tools_menu.addAction("Settings...", self.open_settings)
        
        # Help Menu
        help_menu = self.menu_bar.addMenu("&Help")
        help_menu.addAction("About")
        
    def open_settings(self):
        from hemobind_gui.widgets.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.app_settings, self)
        if dialog.exec():
            self.app_settings = dialog.get_settings()
            # Save to QSettings
            for k, v in self.app_settings.items():
                self.qsettings.setValue(k, v)
            # Update dep status
            self.dep_status.refresh(self.app_settings)
            
    def new_session(self):
        # Reset all panels to defaults
        for panel in self.panels.values():
            panel.set_config({})
            
    def save_session(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Save Session", str(self.config_dir), "JSON Files (*.json)")
        if path:
            data = self._gather_all_configs()
            self.session_manager.save_session(Path(path), data)
            
    def open_session(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Open Session", str(self.config_dir), "JSON Files (*.json)")
        if path:
            data = self.session_manager.load_session(Path(path))
            if data:
                self._apply_all_configs(data)
                
    def load_last_session(self):
        data = self.session_manager.load_last_session()
        if data:
            self._apply_all_configs(data)
            
    def _gather_all_configs(self) -> dict:
        return {stage_id: panel.get_config() for stage_id, panel in self.panels.items()}
        
    def _apply_all_configs(self, data: dict):
        for stage_id, config in data.items():
            if stage_id in self.panels:
                self.panels[stage_id].set_config(config)
                
    def closeEvent(self, event):
        # Save last session on exit
        data = self._gather_all_configs()
        self.session_manager.save_session(self.session_manager.last_session_path, data)
        event.accept()
        
    def open_run_dir(self):
        import subprocess
        run_dir = Path("runs")
        if run_dir.exists():
            subprocess.run(["xdg-open", str(run_dir)])
            
    def switch_stage(self, stage_id: str):
        panel = self.panels.get(stage_id)
        if panel:
            self.stacked_widget.setCurrentWidget(panel)
            self.statusBar().showMessage(f"Configuring {panel.title}")
            
    def run_pipeline(self, from_stage, to_stage):
        from hemobind.config import HemobindConfig, DockingConfig, AnalysisConfig, MDConfig
        from hemobind_gui.core.worker import PipelineWorker
        from datetime import datetime
        from pathlib import Path

        # 1. Build config from panels
        p1 = self.panels["s1_prepare"].get_config()
        p2 = self.panels["s2_docking"].get_config()
        p3 = self.panels["s3_analyze"].get_config()
        p4 = self.panels["s4_select"].get_config()
        p5 = self.panels["s5"].get_config()
        p6 = self.panels["s6"].get_config()
        p7 = self.panels["s7"].get_config()
        p8 = self.panels["s8"].get_config()

        cfg = HemobindConfig(
            receptor=p1["receptor"],
            ligands=[p1["ligand"]],
            docking=DockingConfig(
                mode=p1["mode"],
                center=p1["center"],
                tool=p2["tool"],
                n_poses=p2["n_poses"],
                exhaustiveness=p2["exhaustiveness"]
            ),
            analysis=AnalysisConfig(
                plip_docker_image=p3["plip_docker_image"],
                top_n=p3["top_n"],
                md_stride=p8["analysis_stride"],
                md_topology=p8["custom_topology"],
                md_trajectory=p8["custom_trajectory"]
            ),
            md=MDConfig(
                ph=p5["ph"],
                sim_time_ns=p7["sim_time_ns"],
                gpu_index=p7["gpu_index"],
                water_model=p6["water_model"],
                box_buffer_ang=p6["box_buffer"],
                salt_conc_mol=p6["salt_conc"],
                protein_ff=p6.get("protein_ff", "amber14-all.xml"),
                water_ff=p6.get("water_ff", "amber14/tip3p.xml"),
                ligand_ff=p6.get("ligand_ff", "openff-2.1.0.offxml"),
                ligand_charge_method=p5.get("ligand_charge_method", "am1bcc"),
            )
        )

        # 2. Setup run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"runs/gui_run_{timestamp}")
        
        # 3. Create worker
        self.worker = PipelineWorker(cfg, run_dir, from_stage, to_stage)
        self.worker.log_message.connect(self.console.append_message)
        self.worker.stage_started.connect(lambda s: self.pipeline_view.set_status(s, "running"))
        self.worker.stage_done.connect(self.on_stage_finished)
        self.worker.finished.connect(self.on_pipeline_finished)
        
        # 4. Start
        self.run_control.set_running(True)
        self.worker.start()

    def on_stage_finished(self, stage_id):
        self.pipeline_view.set_status(stage_id, "done")
        # Update results in panel if it supports it
        panel = self.panels.get(stage_id)
        if panel and hasattr(panel, "update_results"):
            # Load context from run_dir to get latest results
            context_file = Path(self.worker.run_dir) / "context.json"
            if context_file.exists():
                try:
                    context = json.loads(context_file.read_text())
                    panel.update_results(context)
                except:
                    pass

    def on_pipeline_finished(self, success):
        self.run_control.set_running(False)
        msg = "Pipeline completed successfully!" if success else "Pipeline failed."
        self.statusBar().showMessage(msg)
        if success:
            # Mark all as done for visual feedback
            for s in self.panels:
                self.pipeline_view.set_status(s, "done")
