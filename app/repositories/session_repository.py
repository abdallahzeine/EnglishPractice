from typing import Literal, cast

from app.core.database import SessionFactory
from app.domain.models import AppSettings, WordCheckMode
from app.domain.tables import SettingsRow


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
