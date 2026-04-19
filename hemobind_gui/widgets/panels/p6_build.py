from PySide6.QtWidgets import QFormLayout, QDoubleSpinBox, QComboBox, QSpinBox
from hemobind_gui.widgets.stage_panel import StagePanel

class BuildPanel(StagePanel):
    def __init__(self, parent=None):
        super().__init__("s6_build", "Desmond System Builder", parent)
        self.setup_ui()

    def setup_ui(self):
        form = QFormLayout()
        
        self.cb_protein_ff = QComboBox()
        self.cb_protein_ff.addItems(["amber14-all.xml", "amber99sbildn.xml", "charmm36.xml"])
        form.addRow("Protein Force Field:", self.cb_protein_ff)

        self.cb_water_ff = QComboBox()
        self.cb_water_ff.addItems(["amber14/tip3p.xml", "amber14/tip4pew.xml", "charmm36/water.xml"])
        form.addRow("Water Force Field:", self.cb_water_ff)

        self.cb_ligand_ff = QComboBox()
        self.cb_ligand_ff.addItems(["openff-2.1.0.offxml", "openff-2.0.0.offxml"])
        form.addRow("Ligand Force Field:", self.cb_ligand_ff)
        
        self.cb_water = QComboBox()
        self.cb_water.addItems(["tip3p", "tip4pew", "spce"])
        form.addRow("Water Model (Solvent):", self.cb_water)
        
        self.sp_buffer = QDoubleSpinBox(); self.sp_buffer.setRange(5.0, 50.0); self.sp_buffer.setValue(15.0)
        form.addRow("Box Buffer (Å):", self.sp_buffer)
        
        self.sp_salt = QDoubleSpinBox(); self.sp_salt.setRange(0, 10); self.sp_salt.setValue(0.15)
        form.addRow("Salt Conc (M):", self.sp_salt)
        
        self.sp_parallel = QSpinBox(); self.sp_parallel.setRange(1, 64); self.sp_parallel.setValue(3)
        form.addRow("Parallel Jobs:", self.sp_parallel)
        
        self.main_layout.addLayout(form)
        self.main_layout.addStretch()

    def get_config(self) -> dict:
        return {
            "protein_ff": self.cb_protein_ff.currentText(),
            "water_ff": self.cb_water_ff.currentText(),
            "ligand_ff": self.cb_ligand_ff.currentText(),
            "water_model": self.cb_water.currentText(),
            "box_buffer": self.sp_buffer.value(),
            "salt_conc": self.sp_salt.value(),
            "parallel_jobs": self.sp_parallel.value()
        }

    def set_config(self, cfg: dict):
        self.cb_protein_ff.setCurrentText(cfg.get("protein_ff", "amber14-all.xml"))
        self.cb_water_ff.setCurrentText(cfg.get("water_ff", "amber14/tip3p.xml"))
        self.cb_ligand_ff.setCurrentText(cfg.get("ligand_ff", "openff-2.1.0.offxml"))
        self.cb_water.setCurrentText(cfg.get("water_model", "tip3p"))
        self.sp_buffer.setValue(cfg.get("box_buffer", 15.0))
        self.sp_salt.setValue(cfg.get("salt_conc", 0.15))
        self.sp_parallel.setValue(cfg.get("parallel_jobs", 3))
