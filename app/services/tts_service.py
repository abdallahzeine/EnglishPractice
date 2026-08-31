import hashlib
import warnings
from pathlib import Path

from app.core.config import DATA_DIR, ensure_data_dir
from app.domain.models import AppSettings

SAMPLE_RATE = 24000
VOICE = "af_heart"

# ponytail: kokoro 0.9.4 builds its model with torch.nn.utils.weight_norm,
# deprecated upstream but present in the locked torch 2.6. Drop this filter
# if kokoro switches to torch.nn.utils.parametrizations.weight_norm.
warnings.filterwarnings(
    "ignore", message=".*torch.nn.utils.weight_norm.*", category=FutureWarning
)


class TTSService:
    """Kokoro-82M wrapper. The model is downloaded and loaded lazily on
    first use — call generate() from a worker thread, never the GUI thread."""

    def __init__(self, settings: AppSettings) -> None:
        self._device = settings.tts_device
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is None:
            from kokoro import KPipeline  # deferred: pulls torch

            self._pipeline = KPipeline(
                lang_code="a", repo_id="hexgrad/Kokoro-82M", device=self._device
            )

    def generate(self, text: str, speed: float = 1.0) -> Path:
        """Generates audio for text at the given speed, returns a cached WAV path."""
        ensure_data_dir()
        cache_dir = DATA_DIR / "tts_cache"
        cache_dir.mkdir(exist_ok=True)
        digest = hashlib.md5(f"kokoro:{speed}:{text}".encode()).hexdigest()
        path = cache_dir / f"{digest}.wav"
        if path.exists():
            return path

        self._load()
        assert self._pipeline is not None
        import numpy as np  # deferred: part of the kokoro stack
        import soundfile as sf

        chunks = [
            audio for _, _, audio in self._pipeline(text, voice=VOICE, speed=speed)
        ]
        if not chunks:
            raise ValueError("Kokoro produced no audio for this text.")
        audio = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
        sf.write(str(path), audio, SAMPLE_RATE)
        return path
