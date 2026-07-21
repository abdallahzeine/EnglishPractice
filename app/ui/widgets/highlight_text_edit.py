import html

from PyQt6.QtWidgets import QTextEdit

from app.domain.models import TypedWord

COLORS = {"correct": "#2e7d32", "incorrect": "#c62828", "pending": ""}


class HighlightTextEdit(QTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)

    def render(self, words: list[TypedWord]) -> None:
        parts: list[str] = []
        for word in words:
            color = COLORS[word.status]
            escaped = html.escape(word.word)
            if color:
                parts.append(f'<span style="color:{color};">{escaped}</span>')
            else:
                parts.append(escaped)
        self.setHtml(f'<p style="font-size:16px;">{" ".join(parts)}</p>')
