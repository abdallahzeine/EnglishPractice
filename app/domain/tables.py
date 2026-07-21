from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SettingsRow(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    openrouter_api_key: Mapped[str] = mapped_column(default="")
    ai_model: Mapped[str] = mapped_column(default="anthropic/claude-sonnet-4.5")
    word_check_mode: Mapped[str] = mapped_column(default="on_finish")
    tts_device: Mapped[str] = mapped_column(default="cuda")
