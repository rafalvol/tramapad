import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.database import criar_tabelas

criar_tabelas()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
