from typing import Dict, Any, List

class ScriptWriter:
    """Adapts raw storyboards into target platform formats (YouTube, TikTok/Reels, LinkedIn, Blog)."""

    @staticmethod
    def format_for_youtube(storyboard: Dict[str, Any]) -> str:
        output = [f"# {storyboard.get('title', 'Video Title')}\n"]
        output.append(f"**Resumen Executivo:** {storyboard.get('summary', '')}\n")
        output.append("## Capítulos y Guión de Escenas\n")
        
        timestamp = 0.0
        for scene in storyboard.get("scenes", []):
            mins, secs = divmod(int(timestamp), 60)
            time_str = f"{mins:02d}:{secs:02d}"
            output.append(f"### Escena {scene['scene_id']} [{time_str}]")
            output.append(f"- **Voz en Off (TTS):** {scene['narration_text']}")
            output.append(f"- **Visual:** {scene['visual_concept']}")
            output.append(f"- **Prompt Generado:** {scene.get('positive_prompt', 'N/A')}\n")
            timestamp += scene.get("estimated_duration_sec", 5.0)

        return "\n".join(output)

    @staticmethod
    def format_for_shortform(storyboard: Dict[str, Any]) -> str:
        """High-retention 9:16 TikTok/Reels script with punchy hook."""
        scenes = storyboard.get("scenes", [])
        output = [f"# SHORTS/REELS SCRIPT: {storyboard.get('title', 'Shorts Title')}\n"]
        
        if scenes:
            output.append(f"⚡ **HOOK INICIAL (0-3s):** {scenes[0]['narration_text']}\n")
        
        output.append("## Ritmo de Escenas (Cambio cada 2.5s - 5s):\n")
        for scene in scenes:
            output.append(f"[{scene['scene_id']}] 🗣️ {scene['narration_text']}")
            output.append(f"    🎨 Visual: {scene['visual_concept']}\n")

        return "\n".join(output)

    @staticmethod
    def format_for_blog(storyboard: Dict[str, Any]) -> str:
        """Formats an SEO Markdown post ready for goslen.com personal blog."""
        title = storyboard.get("title", "Artículo de Marca Personal")
        summary = storyboard.get("summary", "")
        scenes = storyboard.get("scenes", [])

        md = [
            f"# {title}",
            f"\n*{summary}*\n",
            "---",
            "\n## Puntos Clave del Análisis\n"
        ]

        for idx, scene in enumerate(scenes, start=1):
            md.append(f"### {idx}. {scene['narration_text'][:60]}...")
            md.append(f"\n{scene['narration_text']}\n")
            md.append(f"![{scene['visual_concept']}](./images/scene_{idx}.webp)\n")

        md.append("---\n*Publicado automáticamente vía Skytech Content Engine en goslen.com*")
        return "\n".join(md)
