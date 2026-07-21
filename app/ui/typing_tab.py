import time

from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from app.core.animations import fade_in
from app.domain.models import Passage, TypedWord
from app.repositories.document_repository import DocumentRepository
from app.repositories.session_repository import PracticeSessionRepository
from app.services.typing_engine import compute_metrics, diff_words, is_finished
from app.ui.widgets.highlight_text_edit import HighlightTextEdit


class TypingTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._docs = DocumentRepository()
        self._sessions = PracticeSessionRepository()
        self._passage: Passage | None = None
        self._start_time: float | None = None
        self._finished = False
        self._metrics_animation: QPropertyAnimation | None = None

        self.new_btn = QPushButton("New passage")
        self.new_btn.clicked.connect(self._load_passage)
        self.original = HighlightTextEdit()
        self.input = QPlainTextEdit()
        self.input.textChanged.connect(self._on_text_changed)
        self.metrics_label = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(self.new_btn)
        layout.addWidget(self.original, stretch=1)
        layout.addWidget(self.input, stretch=1)
        layout.addWidget(self.metrics_label)
        self._load_passage()

    def _load_passage(self) -> None:
        self._passage = self._docs.random_passage("typing")
        self._finished = False
        self._start_time = None
        self.input.clear()
        self.metrics_label.clear()
        if self._passage is None:
            self.original.setPlainText(
                "No passages available. Import a PDF in Settings."
            )
        else:
            self.original.render(
                [TypedWord(word=w, status="pending") for w in self._passage.text.split()]
            )

    def _on_text_changed(self) -> None:
        if self._passage is None or self._finished:
            return
        typed = self.input.toPlainText()
        if self._start_time is None and typed.strip():
            self._start_time = time.monotonic()
        self.original.render(diff_words(self._passage.text, typed))
        if self._start_time is not None and is_finished(self._passage.text, typed):
            self._finished = True
            elapsed = time.monotonic() - self._start_time
            metrics = compute_metrics(self._passage.text, typed, elapsed)
            self._sessions.save_typing_session(self._passage.id, metrics)
            self.metrics_label.setText(
                f"WPM: {metrics.wpm}    Accuracy: {metrics.accuracy}%    "
                f"Time: {metrics.elapsed_seconds}s"
            )
            self._metrics_animation = fade_in(self.metrics_label)
