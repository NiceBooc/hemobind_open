import sys
from PySide6.QtWidgets import QApplication
import qdarktheme
from hemobind_gui.widgets.main_window import MainWindow

def run_app():
    app = QApplication(sys.argv)
    app.setApplicationName("HemoBind")
    app.setOrganizationName("HemoBind")
    app.setStyle("Fusion")
    
    # Setup dark theme (v0.1.7 uses load_stylesheet)
    try:
        app.setStyleSheet(qdarktheme.load_stylesheet())
    except AttributeError:
        # Fallback if somehow it's a newer version
        qdarktheme.setup_theme("dark")
    
    # Load extra QSS if it exists
    try:
        from importlib.resources import files
        qss_path = files("hemobind_gui.resources.styles").joinpath("extra.qss")
        if qss_path.exists():
            extra_qss = qss_path.read_text()
            app.setStyleSheet(app.styleSheet() + extra_qss)
    except Exception as e:
        print(f"Warning: Could not load extra.qss: {e}")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
