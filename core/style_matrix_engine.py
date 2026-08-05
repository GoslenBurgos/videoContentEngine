import json
import random
from pathlib import Path
from typing import Dict, Any, List

class StyleMatrixEngine:
    """Anti-Monotony Prompt Builder that rotates visual styles, camera angles, and lighting per scene."""

    def __init__(self, matrix_path: Path | str | None = None):
        if matrix_path is None:
            matrix_path = Path(__file__).parent.parent / "config" / "style_matrix.json"
        
        with open(matrix_path, "r", encoding="utf-8") as f:
            self.matrix_data = json.load(f)
        
        self.archetypes = self.matrix_data.get("visual_archetypes", {})
        self.archetype_keys = list(self.archetypes.keys())
        self.camera_shots = self.matrix_data.get("camera_shots", [])
        self.default_negative = self.matrix_data.get("default_negative_prompt", "")
        self._last_archetype_key = None

    def get_diverse_prompt(self, scene_id: int, core_concept: str, explicit_style: str | None = None) -> Dict[str, Any]:
        """Generates a unique, non-repetitive prompt configuration for a given scene concept."""
        # 1. Pick an archetype ensuring no consecutive duplication
        if explicit_style and explicit_style in self.archetypes:
            key = explicit_style
        else:
            available_keys = [k for k in self.archetype_keys if k != self._last_archetype_key]
            key = random.choice(available_keys) if available_keys else random.choice(self.archetype_keys)
        
        self._last_archetype_key = key
        archetype = self.archetypes[key]

        # 2. Pick camera shot
        camera_shot = self.camera_shots[(scene_id - 1) % len(self.camera_shots)]

        # 3. Construct positive prompt
        positive_prompt = (
            f"{core_concept}, {camera_shot}. "
            f"Style: {archetype['style_prompt']}. "
            f"Lighting: {archetype['lighting']}. "
            f"Colors: {archetype['color_harmony']}."
        )

        # 4. Construct negative prompt
        negative_prompt = f"{self.default_negative}, {archetype['negative_prompt']}"

        return {
            "scene_id": scene_id,
            "archetype_key": key,
            "archetype_name": archetype["name"],
            "camera_shot": camera_shot,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "core_concept": core_concept
        }
