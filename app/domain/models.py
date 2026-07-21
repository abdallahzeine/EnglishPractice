from typing import Literal

from pydantic import BaseModel

WordCheckMode = Literal["off", "immediate", "on_finish"]


class AppSettings(BaseModel):
    openrouter_api_key: str = ""
    ai_model: str = "anthropic/claude-sonnet-4.5"
    word_check_mode: WordCheckMode = "on_finish"
    tts_device: Literal["cuda", "cpu"] = "cuda"
