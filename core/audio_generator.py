import asyncio
import edge_tts
from pathlib import Path
from config.settings import settings

class AudioGenerator:
    """TTS engine generating WAV/MP3 voiceover clips per scene segment using Edge-TTS or Kokoro."""

    def __init__(self, voice: str | None = None):
        self.voice = voice or settings.default_voice_es

    def generate_audio(self, text: str, output_path: str | Path) -> Path:
        """Synchronous wrapper for TTS audio synthesis."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            asyncio.run(self._synth_edge_tts(text, path))
        except Exception as e:
            print(f"[AudioGenerator Error] Failed TTS synthesis ({e}). Outputting fallback silent audio.")
            self._create_silent_fallback(path, duration_sec=5.0)

        return path

    async def _synth_edge_tts(self, text: str, path: Path):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(path))

    def _create_silent_fallback(self, path: Path, duration_sec: float = 5.0):
        """Creates a dummy audio file using Python standard wave library if TTS fails."""
        import wave
        import struct

        sample_rate = 44100
        num_samples = int(sample_rate * duration_sec)
        with wave.open(str(path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for _ in range(num_samples):
                wav_file.writeframes(struct.pack("<h", 0))
