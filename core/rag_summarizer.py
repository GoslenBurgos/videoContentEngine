import json
import requests
from typing import Dict, Any, List
from config.settings import settings

RAG_SYSTEM_PROMPT = """
You are an expert AI Visual Director specializing in tech hardware and computer science content.
Analyze the provided text script and segment it into logical narrative scenes.

For each scene, you MUST return a strict JSON object with the following fields:
1. "scene_id": Integer identifier.
2. "narration_text": The spoken voiceover text in Spanish.
3. "visual_keywords": Array of 3 specific technical English terms (e.g., ["microprocessor", "silicon_wafer", "cleanroom"]).
4. "visual_prompt": A highly detailed, concrete physical visual description IN ENGLISH suitable for Stable Diffusion / SDXL.
   - DO NOT use abstract terms like "data sovereignty", "AI power", "technology transformation".
   - DO describe tangible physical objects, lighting, textures, camera shots, and background settings.
   - Example GOOD prompt: "A macro photographic close-up shot of a modern CPU silicon die with glowing gold circuit pathways, dark background, cinematic blue volumetric lighting, 8k resolution, highly detailed."
   - Example BAD prompt: "Una imagen conceptual sobre la inteligencia artificial local y el software."

OUTPUT FORMAT:
Return ONLY a valid JSON object with "title", "summary", and a "scenes" array. Do not wrap in extra markdown text outside the JSON block.
"""

class RAGSummarizer:
    """Interfaces with local Ollama LLM to extract narrative scenes with concrete English visual prompts and keywords."""

    def __init__(self, ollama_url: str | None = None, model: str | None = None):
        self.ollama_url = ollama_url or settings.ollama_url
        self.model = model or settings.ollama_model

    def generate_storyboard(self, source_text: str, target_platform: str = "youtube") -> Dict[str, Any]:
        user_prompt = f"""
Plataforma Objetivo: {target_platform}
Texto Fuente:
---
{source_text[:6000]}
---

Genera un JSON con esta estructura exacta:
{{
  "title": "Título del video",
  "summary": "Resumen en 2 oraciones",
  "scenes": [
    {{
      "scene_id": 1,
      "estimated_duration_sec": 6.0,
      "narration_text": "Texto a narrar en español",
      "visual_keywords": ["processor", "silicon", "hardware"],
      "visual_prompt": "A macro photographic close-up shot of a modern CPU silicon die with glowing gold circuit pathways, dark background, cinematic blue volumetric lighting, 8k resolution, highly detailed."
    }}
  ]
}}
"""

        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": RAG_SYSTEM_PROMPT,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=90)
            response.raise_for_status()
            res_data = response.json()
            raw_response = res_data.get("response", "{}")
            return json.loads(raw_response)
        except Exception as e:
            print(f"[Warning] Ollama connection error at {self.ollama_url} ({e}). Using semantic fallback storyboard.")
            return self._fallback_storyboard(source_text)

    def _fallback_storyboard(self, text: str) -> Dict[str, Any]:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [text[:300]]

        scene_configs = [
            {
                "keywords": ["processor", "silicon", "hardware"],
                "prompt": "A macro photographic close-up shot of a modern CPU silicon die with glowing gold circuit pathways, dark background, cinematic blue volumetric lighting, 8k resolution, highly detailed."
            },
            {
                "keywords": ["network", "brics", "global"],
                "prompt": "A global digital network map connecting continents with illuminated fiber optic lines, dark blue background, high-tech graphic artwork, 8k resolution."
            },
            {
                "keywords": ["server", "datacenter", "infrastructure"],
                "prompt": "High-tech server room data center with glowing green and blue LED racks, dark futuristic aesthetic, cinematic perspective, highly detailed."
            },
            {
                "keywords": ["ai_core", "neural_network", "quantum"],
                "prompt": "A glowing futuristic artificial intelligence neural network core, sleek dark technology background, blue and cyan neon lights, cinematic shot."
            }
        ]

        scenes = []
        for i, p in enumerate(paragraphs[:5], start=1):
            cfg = scene_configs[(i - 1) % len(scene_configs)]
            scenes.append({
                "scene_id": i,
                "estimated_duration_sec": 6.0,
                "narration_text": p[:220],
                "visual_keywords": cfg["keywords"],
                "visual_prompt": cfg["prompt"]
            })

        return {
            "title": "Análisis Tecnológico y Estratégico Local",
            "summary": "Desglose semántico por escenas con prompts físicos en inglés.",
            "scenes": scenes
        }
