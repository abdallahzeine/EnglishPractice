from PyQt6.QtWidgets import QMainWindow, QTabWidget

from app.ui.reading_tab import ReadingTab
from app.ui.settings_tab import SettingsTab
from app.ui.typing_tab import TypingTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("English Practice")
        self.resize(1000, 700)
        tabs = QTabWidget()
        tabs.addTab(ReadingTab(), "Reading")
        tabs.addTab(TypingTab(), "Typing")
        tabs.addTab(SettingsTab(), "Settings")
        self.setCentralWidget(tabs)
