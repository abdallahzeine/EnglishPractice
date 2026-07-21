from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import AppSettings, ContextDocument, WordCheckMode
from app.repositories.document_repository import DocumentRepository
from app.repositories.session_repository import SettingsRepository


class SettingsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._settings_repo = SettingsRepository()
        self._docs_repo = DocumentRepository()
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

        self.docs_box = QGroupBox("Context documents")
        self.docs_layout = QVBoxLayout(self.docs_box)
        import_btn = QPushButton("Import PDF…")
        import_btn.clicked.connect(self._import_pdf)
        layout.addRow(self.docs_box)
        layout.addRow(import_btn)

        settings = self._settings_repo.load()
        self.api_key.setText(settings.openrouter_api_key)
        self.model.setText(settings.ai_model)
        self.word_check.setCurrentText(settings.word_check_mode)
        self._reload_documents()

    def _save(self) -> None:
        self._settings_repo.save(
            AppSettings(
                openrouter_api_key=self.api_key.text().strip(),
                ai_model=self.model.text().strip(),
                word_check_mode=cast_mode(self.word_check.currentText()),
            )
        )
        QMessageBox.information(self, "Settings", "Saved.")

    def _import_pdf(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Import PDF", "", "PDF files (*.pdf)"
        )
        if not path_str:
            return
        try:
            self._docs_repo.import_pdf(Path(path_str))
        except ValueError as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        self._reload_documents()

    def _reload_documents(self) -> None:
        while self.docs_layout.count():
            item = self.docs_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        documents = self._docs_repo.list_documents()
        if not documents:
            self.docs_layout.addWidget(QLabel("No documents imported yet."))
            return
        for doc in documents:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(QLabel(doc.filename), stretch=1)
            typing_cb = QCheckBox("Typing")
            typing_cb.setChecked(doc.use_for_typing)
            reading_cb = QCheckBox("Reading")
            reading_cb.setChecked(doc.use_for_reading)

            def on_toggle(
                _checked: bool,
                d: ContextDocument = doc,
                t: QCheckBox = typing_cb,
                r: QCheckBox = reading_cb,
            ) -> None:
                self._docs_repo.set_usage(d.id, t.isChecked(), r.isChecked())

            typing_cb.toggled.connect(on_toggle)
            reading_cb.toggled.connect(on_toggle)
            row_layout.addWidget(typing_cb)
            row_layout.addWidget(reading_cb)
            self.docs_layout.addWidget(row)


def cast_mode(value: str) -> WordCheckMode:
    if value in ("off", "immediate", "on_finish"):
        return value  # type: ignore[return-value]
    return "on_finish"
