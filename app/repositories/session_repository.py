from typing import Literal, cast

from app.core.database import SessionFactory
from app.domain.models import AppSettings, TypingMetrics, WordCheckMode
from app.domain.tables import ReadingSessionRow, SettingsRow, TypingSessionRow


class SettingsRepository:
    def load(self) -> AppSettings:
        with SessionFactory() as session:
            row = session.get(SettingsRow, 1)
            if row is None:
                return AppSettings()
            return AppSettings(
                openrouter_api_key=row.openrouter_api_key,
                ai_model=row.ai_model,
                word_check_mode=cast(WordCheckMode, row.word_check_mode),
                tts_device=cast(Literal["cuda", "cpu"], row.tts_device),
            )

    def save(self, settings: AppSettings) -> None:
        with SessionFactory() as session:
            row = session.get(SettingsRow, 1) or SettingsRow(id=1)
            row.openrouter_api_key = settings.openrouter_api_key
            row.ai_model = settings.ai_model
            row.word_check_mode = settings.word_check_mode
            row.tts_device = settings.tts_device
            session.add(row)
            session.commit()


class PracticeSessionRepository:
    def save_typing_session(self, passage_id: int, metrics: TypingMetrics) -> None:
        with SessionFactory() as session:
            session.add(
                TypingSessionRow(
                    passage_id=passage_id,
                    wpm=metrics.wpm,
                    accuracy=metrics.accuracy,
                    elapsed_seconds=metrics.elapsed_seconds,
                )
            )
            session.commit()

    def save_reading_session(self, passage_id: int, kind: str, correct: bool) -> None:
        with SessionFactory() as session:
            session.add(
                ReadingSessionRow(
                    passage_id=passage_id, question_kind=kind, correct=correct
                )
            )
            session.commit()

    def reading_stats(self) -> tuple[int, int]:
        """Returns (correct answers, total answers)."""
        with SessionFactory() as session:
            rows = session.query(ReadingSessionRow).all()
            return sum(1 for r in rows if r.correct), len(rows)
