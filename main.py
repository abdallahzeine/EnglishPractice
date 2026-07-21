import sys

from PyQt6.QtWidgets import QApplication

from app.core.database import init_db
from app.main_window import MainWindow


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
