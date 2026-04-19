from PySide6.QtWidgets import QFormLayout, QRadioButton, QButtonGroup, QDoubleSpinBox, QHBoxLayout, QVBoxLayout, QWidget
from hemobind_gui.widgets.stage_panel import StagePanel
from hemobind_gui.widgets.file_input import FileInputWidget

class PreparePanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s1_prepare", "Receptor & Ligand Preparation", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.receptor_input = FileInputWidget("Receptor PDB:", filter="PDB Files (*.pdb)")
        form.addRow(self.receptor_input)
        
        self.ligand_input = FileInputWidget("Ligand Mol2:", filter="Mol2 Files (*.mol2 *.sdf)")
        form.addRow(self.ligand_input)
        
        # Grid Mode
        self.bg_mode = QButtonGroup(self)
        self.rb_blind = QRadioButton("Blind")
        self.rb_targeted = QRadioButton("Targeted")
        self.rb_blind.setChecked(True)
        self.bg_mode.addButton(self.rb_blind)
        self.bg_mode.addButton(self.rb_targeted)
        
        h_mode = QHBoxLayout()
        h_mode.addWidget(self.rb_blind)
        h_mode.addWidget(self.rb_targeted)
        form.addRow("Grid Mode:", h_mode)
        
        # Targeted coords
        self.targeted_widget = QWidget()
        t_layout = QFormLayout(self.targeted_widget)
        self.sp_x = QDoubleSpinBox(); self.sp_x.setRange(-1000, 1000)
        self.sp_y = QDoubleSpinBox(); self.sp_y.setRange(-1000, 1000)
        self.sp_z = QDoubleSpinBox(); self.sp_z.setRange(-1000, 1000)
        t_layout.addRow("Center X:", self.sp_x)
        t_layout.addRow("Center Y:", self.sp_y)
        t_layout.addRow("Center Z:", self.sp_z)
        self.targeted_widget.setVisible(False)
        form.addRow(self.targeted_widget)
        
        self.rb_targeted.toggled.connect(self.targeted_widget.setVisible)
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "receptor": self.receptor_input.text(),
            "ligand": self.ligand_input.text(),
            "mode": "blind" if self.rb_blind.isChecked() else "targeted",
            "center": [self.sp_x.value(), self.sp_y.value(), self.sp_z.value()]
        }

    def set_config(self, cfg: dict):
        self.receptor_input.setText(cfg.get("receptor", ""))
        self.ligand_input.setText(cfg.get("ligand", ""))
        if cfg.get("mode") == "targeted":
            self.rb_targeted.setChecked(True)
            c = cfg.get("center", [0, 0, 0])
            self.sp_x.setValue(c[0]); self.sp_y.setValue(c[1]); self.sp_z.setValue(c[2])
        else:
            self.rb_blind.setChecked(True)
