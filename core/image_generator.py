import os
import io
import urllib.parse
import requests
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any
from config.settings import settings

class ImageGenerator:
    """Generates unique, topic-specific AI illustrations and HD B-roll matching scene narrative concepts."""

    def __init__(self, engine: str | None = None):
        self.engine = engine or settings.default_image_engine
        self.comfy_url = settings.comfyui_url
        self.webui_url = settings.sd_webui_url

        # Curated collection of high-resolution tech stock images keyed by topic
        self.stock_library = {
            "microchip": [
                "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1920&h=1080&q=80",
                "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=1920&h=1080&q=80",
                "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1920&h=1080&q=80"
            ],
            "network": [
                "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&h=1080&q=80",
                "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1920&h=1080&q=80",
                "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1920&h=1080&q=80"
            ],
            "server": [
                "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1920&h=1080&q=80",
                "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=1920&h=1080&q=80"
            ],
            "ai": [
                "https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=1920&h=1080&q=80",
                "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1920&h=1080&q=80"
            ]
        }

    def generate_image(self, prompt_config: Dict[str, Any], output_path: str | Path, resolution: tuple[int, int] = (1920, 1080)) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        raw_concept = prompt_config.get("visual_concept", prompt_config.get("core_concept", "Artificial Intelligence Technology"))
        scene_id = prompt_config.get("scene_id", 1)

        # Extract concise clean visual prompt (max 120 chars)
        clean_concept = raw_concept.split(".")[0]
        clean_concept = clean_concept.replace("Style:", "").replace("Lighting:", "").replace("Colors:", "").strip()
        clean_concept = clean_concept[:120]

        # 1. Try Local PyTorch + Diffusers GPU Engine
        if self._try_local_diffusers(clean_concept, path, resolution):
            return path

        # 2. Try Local SD WebUI API
        if self._try_sd_webui(clean_concept, path, resolution):
            return path

        # 3. AI Diffusion Image API (Pollinations AI with seed & 20s timeout)
        if self._try_pollinations_ai(clean_concept, scene_id, path, resolution):
            return path

        # 4. Topic-Matched HD Stock B-Roll Fetcher
        if self._try_stock_broll(clean_concept, scene_id, path, resolution):
            return path

        # 5. Scene-Specific Dynamic Graphic Fallback
        print(f"[ImageGenerator] Rendering Scene-Specific Graphic for Scene #{scene_id}")
        self._render_scene_specific_graphic(prompt_config, path, resolution)
        return path

    def _try_local_diffusers(self, prompt: str, output_path: Path, resolution: tuple[int, int]) -> bool:
        try:
            import torch
            from diffusers import AutoPipelineForText2Image

            pipe = AutoPipelineForText2Image.from_pretrained(
                "stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16"
            ).to("cuda")

            image = pipe(prompt=f"{prompt}, 8k, cinematic", num_inference_steps=2, guidance_scale=0.0).images[0]
            image = image.resize(resolution, Image.Resampling.LANCZOS)
            image.save(output_path, quality=95)
            print(f"✅ [Local GPU] Generated image -> {output_path.name}")
            return True
        except Exception:
            return False

    def _try_sd_webui(self, prompt: str, output_path: Path, resolution: tuple[int, int]) -> bool:
        try:
            payload = {
                "prompt": f"{prompt}, photorealistic, 8k",
                "negative_prompt": "text, words, blurry",
                "width": resolution[0],
                "height": resolution[1],
                "steps": 20,
                "cfg_scale": 7.0
            }
            res = requests.post(f"{self.webui_url}/sdapi/v1/txt2img", json=payload, timeout=4)
            if res.status_code == 200:
                import base64
                data = res.json()
                img_bytes = base64.b64decode(data['images'][0])
                image = Image.open(io.BytesIO(img_bytes))
                image.save(output_path)
                print(f"✅ [Local SD WebUI] Generated image -> {output_path.name}")
                return True
        except Exception:
            pass
        return False

    def _try_pollinations_ai(self, prompt: str, scene_id: int, output_path: Path, resolution: tuple[int, int]) -> bool:
        try:
            width, height = resolution
            seed = (scene_id * 1337) + random.randint(1, 999)
            encoded_prompt = urllib.parse.quote(f"{prompt}, photorealistic 8k, cinematic lighting, no text")
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
            
            print(f"⌛ [AI Diffusion Engine] Scene #{scene_id} -> Generating: '{prompt[:45]}...'")
            res = requests.get(url, timeout=20)
            if res.status_code == 200 and len(res.content) > 15000 and res.headers.get("content-type", "").startswith("image"):
                image = Image.open(io.BytesIO(res.content))
                image = image.resize(resolution, Image.Resampling.LANCZOS)
                image.save(output_path, quality=95)
                print(f"✅ [AI Diffusion Engine] Generated image for Scene #{scene_id} -> {output_path.name}")
                return True
            else:
                print(f"[AI Diffusion] Non-image response: status {res.status_code}, len {len(res.content)}")
        except Exception as e:
            print(f"[Warning] AI Diffusion timeout or error ({e}). Using topic-matched stock B-roll.")
        return False

    def _try_stock_broll(self, prompt: str, scene_id: int, output_path: Path, resolution: tuple[int, int]) -> bool:
        """Selects a topic-matched HD photo from curated stock library based on scene prompt keywords."""
        try:
            prompt_lower = prompt.lower()
            category = "ai"
            if any(k in prompt_lower for k in ["chip", "processor", "silicon", "hardware", "cpu", "gpu"]):
                category = "microchip"
            elif any(k in prompt_lower for k in ["map", "network", "global", "internet", "fiber", "earth", "brics"]):
                category = "network"
            elif any(k in prompt_lower for k in ["server", "data", "cloud", "center", "rack"]):
                category = "server"

            urls = self.stock_library.get(category, self.stock_library["ai"])
            selected_url = urls[(scene_id - 1) % len(urls)]

            res = requests.get(selected_url, timeout=8)
            if res.status_code == 200 and len(res.content) > 15000:
                image = Image.open(io.BytesIO(res.content))
                image = image.resize(resolution, Image.Resampling.LANCZOS)
                image.save(output_path, quality=95)
                print(f"✅ [Topic B-Roll: {category.upper()}] Fetched photo for Scene #{scene_id} -> {output_path.name}")
                return True
        except Exception as e:
            print(f"[Warning] Stock B-Roll fetch failed ({e}).")
        return False

    def _render_scene_specific_graphic(self, prompt_config: Dict[str, Any], output_path: Path, resolution: tuple[int, int]):
        width, height = resolution
        scene_id = prompt_config.get("scene_id", 1)

        img = Image.new("RGB", (width, height), (10, 15, 30))
        draw = ImageDraw.Draw(img)

        # Gradient background
        for y in range(height):
            ratio = y / height
            r = int(10 + (25 - 10) * ratio)
            g = int(15 + (45 - 15) * ratio)
            b = int(30 + (80 - 30) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        cx, cy = width // 2, height // 2

        if scene_id % 3 == 1:
            draw.rectangle([cx - 200, cy - 200, cx + 200, cy + 200], outline=(56, 189, 248), width=6, fill=(15, 23, 42))
            draw.rectangle([cx - 140, cy - 140, cx + 140, cy + 140], outline=(245, 158, 11), width=4, fill=(30, 41, 59))
            for i in range(-180, 200, 30):
                draw.line([(cx + i, cy - 200), (cx + i, cy - 260)], fill=(245, 158, 11), width=3)
                draw.line([(cx + i, cy + 200), (cx + i, cy + 260)], fill=(245, 158, 11), width=3)
                draw.line([(cx - 200, cy + i), (cx - 260, cy + i)], fill=(245, 158, 11), width=3)
                draw.line([(cx + 200, cy + i), (cx + 260, cy + i)], fill=(245, 158, 11), width=3)
        elif scene_id % 3 == 2:
            for rx in range(cx - 350, cx + 400, 250):
                draw.rectangle([rx - 90, cy - 300, rx + 90, cy + 300], outline=(139, 92, 246), width=4, fill=(5, 8, 20))
                for ry in range(cy - 260, cy + 280, 40):
                    draw.rectangle([rx - 70, ry, rx + 70, ry + 20], fill=(15, 23, 42))
                    draw.ellipse([rx + 40, ry + 6, rx + 52, ry + 14], fill=(16, 185, 129))
        else:
            import math
            draw.ellipse([cx - 280, cy - 280, cx + 280, cy + 280], outline=(56, 189, 248), width=3)
            for angle_deg in range(0, 360, 30):
                rad = math.radians(angle_deg)
                nx = int(cx + 280 * math.cos(rad))
                ny = int(cy + 280 * math.sin(rad))
                draw.line([(cx, cy), (nx, ny)], fill=(139, 92, 246), width=2)
                draw.ellipse([nx - 10, ny - 10, nx + 10, ny + 10], fill=(56, 189, 248))

        img.save(output_path, quality=95)
