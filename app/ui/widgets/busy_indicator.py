from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget


class BusyIndicator(QWidget):
    """Indeterminate progress bar with a label. Hidden by default."""

    def __init__(self, text: str = "Working…") -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QProgressBar()
        bar.setRange(0, 0)  # busy mode
        bar.setTextVisible(False)
        bar.setFixedHeight(14)
        layout.addWidget(bar, stretch=1)
        layout.addWidget(QLabel(text))
        self.hide()
