from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from app.domain.models import AppSettings, WordCheckMode
from app.repositories.session_repository import SettingsRepository


class SettingsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._repo = SettingsRepository()
        layout = QFormLayout(self)

        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.model = QLineEdit()
        self.word_check = QComboBox()
        self.word_check.addItems(["off", "immediate", "on_finish"])
        save = QPushButton("Save")
        save.clicked.connect(self._save)

        layout.addRow("OpenRouter API key", self.api_key)
        layout.addRow("AI model", self.model)
        layout.addRow("Word check mode", self.word_check)
        layout.addRow(save)

        settings = self._repo.load()
        self.api_key.setText(settings.openrouter_api_key)
        self.model.setText(settings.ai_model)
        self.word_check.setCurrentText(settings.word_check_mode)

    def _save(self) -> None:
        self._repo.save(
            AppSettings(
                openrouter_api_key=self.api_key.text().strip(),
                ai_model=self.model.text().strip(),
                word_check_mode=cast_mode(self.word_check.currentText()),
            )
        )
        QMessageBox.information(self, "Settings", "Saved.")


def cast_mode(value: str) -> WordCheckMode:
    return value if value in ("off", "immediate", "on_finish") else "on_finish"  # type: ignore[return-value]
