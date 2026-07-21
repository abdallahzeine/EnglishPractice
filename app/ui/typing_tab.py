import time

from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.animations import fade_in
from app.core.workers import TaskRunner
from app.domain.models import AppSettings, Passage, TypedWord, WordFeedback
from app.repositories.document_repository import DocumentRepository
from app.repositories.session_repository import (
    PracticeSessionRepository,
    SettingsRepository,
)
from app.services.ai_service import AIService
from app.services.typing_engine import compute_metrics, diff_words, is_finished
from app.ui.widgets.busy_indicator import BusyIndicator
from app.ui.widgets.highlight_text_edit import HighlightTextEdit
from app.ui.widgets.message_bubble import MessageBubble


class TypingTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._docs = DocumentRepository()
        self._sessions = PracticeSessionRepository()
        self._runner = TaskRunner()
        self._settings = AppSettings()
        self._passage: Passage | None = None
        self._start_time: float | None = None
        self._finished = False
        self._checked_words: set[str] = set()
        self._bubble_animations: list[QPropertyAnimation] = []

        self.new_btn = QPushButton("New passage")
        self.new_btn.clicked.connect(self._load_passage)
        self.original = HighlightTextEdit()
        self.input = QPlainTextEdit()
        self.input.textChanged.connect(self._on_text_changed)
        self.metrics_label = QLabel("")
        self.busy = BusyIndicator("Checking words…")
        self.feedback_container = QWidget()
        self.feedback_layout = QVBoxLayout(self.feedback_container)
        self.feedback_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.new_btn)
        layout.addWidget(self.original, stretch=1)
        layout.addWidget(self.input, stretch=1)
        layout.addWidget(self.metrics_label)
        layout.addWidget(self.busy)
        layout.addWidget(self.feedback_container)
        self._load_passage()

    def _load_passage(self) -> None:
        self._settings = SettingsRepository().load()
        self._passage = self._docs.random_passage("typing")
        self._finished = False
        self._start_time = None
        self._checked_words.clear()
        self.input.clear()
        self.metrics_label.clear()
        self.busy.hide()
        while self.feedback_layout.count():
            item = self.feedback_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
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
        statuses = diff_words(self._passage.text, typed)
        self.original.render(statuses)

        if self._settings.word_check_mode == "immediate" and typed.endswith(" "):
            words = typed.split()
            index = len(words) - 1
            if (
                words
                and index < len(statuses)
                and statuses[index].status == "incorrect"
                and words[index] not in self._checked_words
            ):
                self._checked_words.add(words[index])
                self._check_words([words[index]])

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
            if self._settings.word_check_mode == "on_finish":
                wrong = [w.word for w in statuses if w.status == "incorrect"]
                self._check_words(wrong)

    def _check_words(self, words: list[str]) -> None:
        if not words:
            return
        context = self._passage.text if self._passage else ""
        self.busy.show()
        self._runner.start(
            lambda: AIService(SettingsRepository().load()).check_words(words, context),
            self._show_feedback,
            self._check_failed,
        )

    def _show_feedback(self, feedback: list[WordFeedback]) -> None:
        self.busy.hide()
        for item in feedback:
            bubble = MessageBubble(item)
            self.feedback_layout.addWidget(bubble)
            self._bubble_animations.append(fade_in(bubble))

    def _check_failed(self, message: str) -> None:
        self.busy.hide()
        QMessageBox.warning(self, "Word check failed", message)
