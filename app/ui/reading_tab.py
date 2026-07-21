import random

from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.animations import fade_in
from app.core.workers import TaskRunner
from app.domain.models import Passage, Question
from app.repositories.document_repository import DocumentRepository
from app.repositories.session_repository import (
    PracticeSessionRepository,
    SettingsRepository,
)
from app.services.ai_service import AIService
from app.ui.widgets.busy_indicator import BusyIndicator


class ReadingTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._docs = DocumentRepository()
        self._sessions = PracticeSessionRepository()
        self._runner = TaskRunner()
        self._passage: Passage | None = None
        self._question: Question | None = None
        self._question_animation: QPropertyAnimation | None = None
        self._answered = False
        self._mcq_buttons: list[QRadioButton] = []
        self._matching_rows: list[tuple[str, QComboBox]] = []
        self._answer_input: QLineEdit | None = None

        self.new_btn = QPushButton("New passage")
        self.new_btn.clicked.connect(self._load_passage)
        self.passage_view = QTextEdit()
        self.passage_view.setReadOnly(True)
        self.busy = BusyIndicator("Generating question…")
        self.question_container = QWidget()
        self.question_layout = QVBoxLayout(self.question_container)
        self.question_layout.setContentsMargins(0, 0, 0, 0)
        self.result_label = QLabel("")
        self.stats_label = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(self.new_btn)
        layout.addWidget(self.passage_view, stretch=1)
        layout.addWidget(self.busy)
        layout.addWidget(self.question_container)
        layout.addWidget(self.result_label)
        layout.addWidget(self.stats_label)
        self._load_passage()

    def _load_passage(self) -> None:
        self._passage = self._docs.random_passage("reading")
        self._question = None
        self._answered = False
        self.result_label.clear()
        self._clear_question()
        self._refresh_stats()
        if self._passage is None:
            self.passage_view.setPlainText(
                "No passages available. Import a PDF in Settings."
            )
            return
        self.passage_view.setPlainText(self._passage.text)
        self.busy.show()
        text = self._passage.text
        self._runner.start(
            lambda: AIService(SettingsRepository().load()).generate_question(text),
            self._show_question,
            self._question_failed,
        )

    def _clear_question(self) -> None:
        self._mcq_buttons = []
        self._matching_rows = []
        self._answer_input = None
        while self.question_layout.count():
            item = self.question_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def _show_question(self, question: Question) -> None:
        self.busy.hide()
        self._question = question
        self.question_layout.addWidget(QLabel(f"<b>{question.prompt}</b>"))
        if question.kind == "mcq":
            for option in question.options:
                button = QRadioButton(option)
                self._mcq_buttons.append(button)
                self.question_layout.addWidget(button)
        elif question.kind == "matching":
            pairs = [o.split("|", 1) for o in question.options if "|" in o]
            rights = [right for _, right in pairs]
            random.shuffle(rights)
            for left, _ in pairs:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addWidget(QLabel(left), stretch=1)
                combo = QComboBox()
                combo.addItems([""] + rights)
                row_layout.addWidget(combo, stretch=1)
                self.question_layout.addWidget(row)
                self._matching_rows.append((left, combo))
        else:  # simple / fill_blank
            self._answer_input = QLineEdit()
            self.question_layout.addWidget(self._answer_input)
        submit = QPushButton("Submit answer")
        submit.clicked.connect(self._submit)
        self.question_layout.addWidget(submit)
        self._question_animation = fade_in(self.question_container)

    def _submit(self) -> None:
        if self._question is None or self._answered or self._passage is None:
            return
        self._answered = True
        correct = self._evaluate()
        self._sessions.save_reading_session(
            self._passage.id, self._question.kind, correct
        )
        if correct:
            self.result_label.setText("Correct!")
        else:
            self.result_label.setText(f"Wrong. Answer: {self._question.answer}")
        self._refresh_stats()

    def _evaluate(self) -> bool:
        question = self._question
        assert question is not None
        if question.kind == "mcq":
            chosen = next(
                (b.text() for b in self._mcq_buttons if b.isChecked()), ""
            )
            return _norm(chosen) == _norm(question.answer)
        if question.kind == "matching":
            pairs = {
                left: right
                for left, right in (
                    o.split("|", 1) for o in question.options if "|" in o
                )
            }
            return all(
                _norm(combo.currentText()) == _norm(pairs.get(left, ""))
                for left, combo in self._matching_rows
            )
        assert self._answer_input is not None
        user = _norm(self._answer_input.text())
        answer = _norm(question.answer)
        return bool(user) and (user == answer or user in answer or answer in user)

    def _refresh_stats(self) -> None:
        correct, total = self._sessions.reading_stats()
        rate = f"{correct / total * 100:.0f}%" if total else "—"
        self.stats_label.setText(f"Correct answers: {correct}/{total} ({rate})")

    def _question_failed(self, message: str) -> None:
        self.busy.hide()
        QMessageBox.warning(self, "Question generation failed", message)


def _norm(value: str) -> str:
    return " ".join(value.lower().split())
