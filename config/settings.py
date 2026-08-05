import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

class Settings(BaseModel):
    # Dashboard Web Server Config
    dashboard_host: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    dashboard_port: int = int(os.getenv("DASHBOARD_PORT", "8500"))

    # Ollama Local Configuration
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
    
    # Image Generator API
    comfyui_url: str = os.getenv("COMFYUI_URL", "http://localhost:8188")
    sd_webui_url: str = os.getenv("SD_WEBUI_URL", "http://localhost:7860")
    default_image_engine: str = os.getenv("DEFAULT_IMAGE_ENGINE", "comfyui") # options: comfyui, sd_webui, pillow_canvas
    
    # TTS Settings
    default_tts_engine: str = os.getenv("DEFAULT_TTS_ENGINE", "edge-tts") # options: edge-tts, kokoro
    default_voice_es: str = os.getenv("DEFAULT_VOICE_ES", "es-MX-JorgeNeural")
    default_voice_en: str = os.getenv("DEFAULT_VOICE_EN", "en-US-ChristopherNeural")
    
    # Platform Resolutions
    res_youtube: tuple[int, int] = (1920, 1080)
    res_vertical: tuple[int, int] = (1080, 1920)
    res_square: tuple[int, int] = (1080, 1080)

settings = Settings()
