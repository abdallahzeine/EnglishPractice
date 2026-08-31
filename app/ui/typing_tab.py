import re
import time
from pathlib import Path

from PyQt6.QtCore import QPropertyAnimation, Qt, QUrl
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QTextEdit,
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
from app.services.tts_service import TTSService
from app.services.typing_engine import compute_metrics, diff_words, is_finished
from app.ui.widgets.busy_indicator import BusyIndicator
from app.ui.widgets.highlight_text_edit import COLORS, HighlightTextEdit
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
        # ponytail: dedupe by (word_index, word_text) so a retype re-checks and
        # distinct positions never collide. Don't shrink to wrong-words-only:
        # grammar errors live in correctly-spelled words the local diff misses.
        self._checked_words: set[tuple[int, str]] = set()
        self._bubble_animations: list[QPropertyAnimation] = []

        self.new_btn = QPushButton("New passage")
        self.new_btn.clicked.connect(self._load_passage)
        self.sound_toggle = QCheckBox("Sound mode (listen instead of read)")
        self.sound_toggle.toggled.connect(self._on_sound_toggled)
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.5, 2.0)
        self.speed.setSingleStep(0.1)
        self.speed.setValue(1.0)
        self.speed.setPrefix("Speed ")
        self.speed.valueChanged.connect(self._on_speed_changed)
        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._play_pause)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setEnabled(False)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(80)
        self.volume.setFixedWidth(100)
        self.audio_busy = BusyIndicator("Preparing audio…")
        self.original = HighlightTextEdit()
        self.input = QPlainTextEdit()
        self.input.textChanged.connect(self._on_text_changed)
        self.check_btn = QPushButton("Check my text")
        self.check_btn.clicked.connect(self._highlight_input)
        self.metrics_label = QLabel("")
        self.busy = BusyIndicator("Checking words…")
        self.feedback_container = QWidget()
        self.feedback_layout = QVBoxLayout(self.feedback_container)
        self.feedback_layout.setContentsMargins(0, 0, 0, 0)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(0.8)
        self._player.positionChanged.connect(self.seek.setValue)
        self._player.durationChanged.connect(self.seek.setMaximum)
        self._player.playbackStateChanged.connect(self._sync_play_btn)
        self.seek.sliderMoved.connect(self._player.setPosition)
        self.volume.valueChanged.connect(
            lambda v: self._audio_output.setVolume(v / 100)
        )
        self._audio_path: Path | None = None

        top_row = QHBoxLayout()
        top_row.addWidget(self.new_btn)
        top_row.addWidget(self.sound_toggle)
        top_row.addWidget(self.speed)
        top_row.addWidget(self.check_btn)
        top_row.addStretch(1)

        player_row = QHBoxLayout()
        player_row.addWidget(self.play_btn)
        player_row.addWidget(self.seek, stretch=1)
        player_row.addWidget(QLabel("Vol"))
        player_row.addWidget(self.volume)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addLayout(player_row)
        layout.addWidget(self.audio_busy)
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
        self._player.stop()
        self._audio_path = None
        self.play_btn.setEnabled(False)
        self.seek.setEnabled(False)
        self.input.setEnabled(self._passage is not None)
        self.check_btn.setEnabled(self._passage is not None)
        if self._passage is None:
            self.original.show()
            self.original.setPlainText(
                "No passages available. Import a PDF in Settings."
            )
        else:
            self.original.render(
                [TypedWord(word=w, status="pending") for w in self._passage.text.split()]
            )
            self._apply_sound_mode()

    def _on_sound_toggled(self, _checked: bool) -> None:
        self._apply_sound_mode()

    def _apply_sound_mode(self) -> None:
        if self._passage is None:
            return
        if self.sound_toggle.isChecked():
            self.original.hide()
            if self._audio_path is None and not self.audio_busy.isVisible():
                self._prepare_audio()
        else:
            self.original.show()

    def _prepare_audio(self) -> None:
        assert self._passage is not None
        text = self._passage.text
        speed = self.speed.value()
        self.audio_busy.show()
        self._runner.start(
            lambda: TTSService(SettingsRepository().load()).generate(text, speed),
            self._audio_ready,
            self._audio_failed,
        )

    def _audio_ready(self, path: Path) -> None:
        self.audio_busy.hide()
        self._audio_path = path
        self.play_btn.setEnabled(True)
        self.seek.setEnabled(True)
        self._player.setSource(QUrl.fromLocalFile(str(path)))
        self._player.play()

    def _audio_failed(self, message: str) -> None:
        self.audio_busy.hide()
        self.sound_toggle.setChecked(False)
        QMessageBox.warning(self, "Audio generation failed", message)

    def _play_pause(self) -> None:
        if self._audio_path is None:
            return
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _sync_play_btn(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_btn.setText(
            "Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "Play"
        )

    def _on_speed_changed(self, _value: float) -> None:
        if self.sound_toggle.isChecked() and self._passage is not None:
            self._player.stop()
            self._audio_path = None
            self.play_btn.setEnabled(False)
            self.seek.setEnabled(False)
            self._prepare_audio()

    def _on_text_changed(self) -> None:
        self.input.setExtraSelections([])  # input highlighting is on-request only
        if self._passage is None or self._finished:
            return
        typed = self.input.toPlainText()
        if self._start_time is None and typed.strip():
            self._start_time = time.monotonic()
        statuses = diff_words(self._passage.text, typed)
        self.original.render(statuses)

        if self._settings.word_check_mode == "immediate":
            # A word is "closed" once it's followed by a non-alphanumeric char
            # (space, punctuation, newline). The last word still being typed
            # is excluded; it's caught below when the run finishes.
            new_words: list[str] = []
            for i, m in enumerate(re.finditer(r"\w+", typed)):
                if m.end() < len(typed) and not typed[m.end()].isalnum():
                    key = (i, m.group())
                    if key not in self._checked_words:
                        self._checked_words.add(key)
                        new_words.append(m.group())
            if new_words:
                self._check_words(new_words)

        if self._start_time is not None and is_finished(self._passage.text, typed):
            self._finished = True
            if self.sound_toggle.isChecked():
                self.original.show()  # reveal mistakes after sound-mode run
            elapsed = time.monotonic() - self._start_time
            metrics = compute_metrics(self._passage.text, typed, elapsed)
            self._sessions.save_typing_session(self._passage.id, metrics)
            self.metrics_label.setText(
                f"WPM: {metrics.wpm}    Accuracy: {metrics.accuracy}%    "
                f"Time: {metrics.elapsed_seconds}s"
            )
            self._metrics_animation = fade_in(self.metrics_label)
            # Final sweep: check any words not yet seen by the AI. In `on_finish`
            # mode that's everything; in `immediate` mode it's the last word that
            # had no trailing space. `off` skips entirely.
            if self._settings.word_check_mode != "off":
                pending: list[str] = []
                for i, m in enumerate(re.finditer(r"\w+", typed)):
                    key = (i, m.group())
                    if key not in self._checked_words:
                        self._checked_words.add(key)
                        pending.append(m.group())
                if pending:
                    self._check_words(pending)

    def _highlight_input(self) -> None:
        if self._passage is None:
            return
        typed = self.input.toPlainText()
        original_words = self._passage.text.split()
        selections: list[QTextEdit.ExtraSelection] = []
        for index, match in enumerate(re.finditer(r"\S+", typed)):
            correct = (
                index < len(original_words) and match.group() == original_words[index]
            )
            cursor = QTextCursor(self.input.document())
            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format.setForeground(
                QColor(COLORS["correct" if correct else "incorrect"])
            )
            selections.append(selection)
        self.input.setExtraSelections(selections)

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
