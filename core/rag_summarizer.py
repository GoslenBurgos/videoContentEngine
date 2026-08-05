import json
import requests
from typing import Dict, Any, List
from config.settings import settings

class RAGSummarizer:
    """Interfaces with local Ollama LLM to extract key narrative scenes with highly descriptive visual prompts."""

    def __init__(self, ollama_url: str | None = None, model: str | None = None):
        self.ollama_url = ollama_url or settings.ollama_url
        self.model = model or settings.ollama_model

    def generate_storyboard(self, source_text: str, target_platform: str = "youtube") -> Dict[str, Any]:
        system_prompt = (
            "Eres un director de arte y productor de video experto. "
            "Tu objetivo es convertir el texto en un guión por escenas. "
            "IMPORTANTE: El campo 'visual_concept' DEBE estar escrito en INGLÉS detallado y ser una descripción gráfica "
            "concreta de lo que se debe mostrar visualmente (ej: 'A glowing silicon microchip processor with blue neon circuit lines, dark metallic background, cinematic macro photo'). "
            "NO uses descripciones abstractas o vagas. "
            "DEBES responder EXCLUSIVAMENTE en formato JSON válido."
        )

        user_prompt = f"""
Plataforma Objetivo: {target_platform}
Texto Fuente:
---
{source_text[:6000]}
---

Genera un JSON con esta estructura exacta:
{{
  "title": "Título llamativo del video",
  "summary": "Resumen ejecutivo en 2 oraciones",
  "scenes": [
    {{
      "scene_id": 1,
      "estimated_duration_sec": 6.0,
      "narration_text": "Texto exacto a narrar en voz alta en español",
      "visual_concept": "Detailed English image prompt describing concrete objects, locations, microchips, servers, maps, or people (NO text on screen)"
    }}
  ]
}}
"""

        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
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
            print(f"[Warning] No se pudo conectar con Ollama en {self.ollama_url} ({e}). Usando fallback offline semántico.")
            return self._fallback_storyboard(source_text)

    def _fallback_storyboard(self, text: str) -> Dict[str, Any]:
        """Semantic fallback storyboard with concrete English visual prompts for testing offline."""
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [text[:300]]

        scenes = []
        visual_prompts_library = [
            "A glowing futuristic artificial intelligence neural network core, sleek dark technology background, blue and cyan neon lights, cinematic shot",
            "A global digital network map connecting continents with illuminated fiber optic lines, dark blue background, high-tech graphic",
            "Macro close-up shot of a silicon microchip processor with glowing circuit pathways, dark gold and blue illumination, high detail",
            "A split concept artwork showing futuristic servers on two sides connected by glowing data streams, abstract corporate tech background",
            "High-tech server room data center with glowing green and blue LED racks, dark futuristic aesthetic"
        ]

        for i, p in enumerate(paragraphs[:5], start=1):
            prompt = visual_prompts_library[(i - 1) % len(visual_prompts_library)]
            scenes.append({
                "scene_id": i,
                "estimated_duration_sec": 6.0,
                "narration_text": p[:220],
                "visual_concept": prompt
            })

        return {
            "title": "Análisis Tecnológico y Estratégico",
            "summary": "Desglose semántico por escenas con prompts visuales concretos.",
            "scenes": scenes
        }
