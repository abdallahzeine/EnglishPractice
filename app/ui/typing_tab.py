from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TypingTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        QVBoxLayout(self).addWidget(QLabel("Typing practice — step 3"))
