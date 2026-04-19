from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QLabel
from hemobind_gui.widgets.file_input import FileInputWidget

class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(500, 300)
        self.settings = settings
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.adgpu_input = FileInputWidget("AutoDock-GPU Path:")
        self.adgpu_input.setText(self.settings.get("adgpu", "adgpu"))
        form.addRow(self.adgpu_input)
        
        self.docker_input = FileInputWidget("Docker Path:")
        self.docker_input.setText(self.settings.get("docker", "docker"))
        form.addRow(self.docker_input)
        
        layout.addLayout(form)
        layout.addStretch()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> dict:
        return {
            "adgpu": self.adgpu_input.text(),
            "docker": self.docker_input.text(),
        }
