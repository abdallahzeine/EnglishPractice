from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SettingsRow(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    openrouter_api_key: Mapped[str] = mapped_column(default="")
    ai_model: Mapped[str] = mapped_column(default="anthropic/claude-sonnet-4.5")
    word_check_mode: Mapped[str] = mapped_column(default="on_finish")
    tts_device: Mapped[str] = mapped_column(default="cuda")


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    use_for_typing: Mapped[bool] = mapped_column(default=True)
    use_for_reading: Mapped[bool] = mapped_column(default=True)

    passages: Mapped[list["PassageRow"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class PassageRow(Base):
    __tablename__ = "passages"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    text: Mapped[str]

    document: Mapped[DocumentRow] = relationship(back_populates="passages")


class TypingSessionRow(Base):
    __tablename__ = "typing_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    passage_id: Mapped[int] = mapped_column(ForeignKey("passages.id"))
    wpm: Mapped[float]
    accuracy: Mapped[float]
    elapsed_seconds: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ReadingSessionRow(Base):
    __tablename__ = "reading_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    passage_id: Mapped[int] = mapped_column(ForeignKey("passages.id"))
    question_kind: Mapped[str]
    correct: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
