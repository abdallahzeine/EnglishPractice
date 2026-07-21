from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ReadingTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        QVBoxLayout(self).addWidget(QLabel("Reading practice — step 6"))
