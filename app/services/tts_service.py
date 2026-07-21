import hashlib
from pathlib import Path

from app.core.config import DATA_DIR, ensure_data_dir
from app.domain.models import AppSettings


class TTSService:
    """Chatterbox TTS wrapper. The model (~500M params) is imported and
    loaded lazily on first use — call generate() from a worker thread,
    never the GUI thread. First run downloads model weights."""

    def __init__(self, settings: AppSettings) -> None:
        self._device = settings.tts_device
        self._model = None

    def _load(self) -> None:
        if self._model is None:
            from chatterbox.tts import ChatterboxTTS  # deferred: pulls torch

            self._model = ChatterboxTTS.from_pretrained(device=self._device)

    def generate(self, text: str) -> Path:
        """Generates audio for text, returns a cached WAV path."""
        self._load()
        assert self._model is not None
        import torchaudio  # deferred: part of the torch stack

        wav = self._model.generate(text)
        ensure_data_dir()
        cache_dir = DATA_DIR / "tts_cache"
        cache_dir.mkdir(exist_ok=True)
        path = cache_dir / f"{hashlib.md5(text.encode()).hexdigest()}.wav"
        if not path.exists():
            torchaudio.save(str(path), wav, self._model.sr)
        return path
