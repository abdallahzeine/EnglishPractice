from PyQt6.QtWidgets import QLabel

from app.domain.models import WordFeedback


class MessageBubble(QLabel):
    def __init__(self, feedback: WordFeedback) -> None:
        super().__init__(
            f"<b>{feedback.word}</b>: {feedback.issue}"
            f"<br><i>{feedback.suggestion}</i>"
        )
        self.setWordWrap(True)
        self.setStyleSheet(
            "QLabel { background: #fff8e1; border: 1px solid #e0c97f; "
            "border-radius: 8px; padding: 8px; }"
        )
