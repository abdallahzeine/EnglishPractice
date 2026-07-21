from typing import Literal

from pydantic import BaseModel

WordCheckMode = Literal["off", "immediate", "on_finish"]
Practice = Literal["typing", "reading"]
WordStatus = Literal["correct", "incorrect", "pending"]


class AppSettings(BaseModel):
    openrouter_api_key: str = ""
    ai_model: str = "anthropic/claude-sonnet-4.5"
    word_check_mode: WordCheckMode = "on_finish"
    tts_device: Literal["cuda", "cpu"] = "cuda"


class ContextDocument(BaseModel):
    id: int
    filename: str
    use_for_typing: bool
    use_for_reading: bool


class Passage(BaseModel):
    id: int
    text: str
    document_id: int


class TypedWord(BaseModel):
    word: str
    status: WordStatus


class TypingMetrics(BaseModel):
    wpm: float
    accuracy: float
    elapsed_seconds: float
