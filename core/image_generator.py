import os
import io
import gc
import urllib.parse
import requests
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List
from config.settings import settings

class LocalImageGenerator:
    """Renders visual keyframes via GPU Diffusers (with VRAM memory clearing) and dynamic semantic fallbacks."""

    def __init__(self, device: str = "cuda", model_id: str | None = None):
        self.device = device if self._is_cuda_available() else "cpu"
        self.model_id = model_id or settings.diffusion_model_id
        self.pipe = None

    def _is_cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _unload_vram(self):
        """Frees PyTorch CUDA cache and executes Python garbage collection to avoid OOM."""
        if self._is_cuda_available():
            try:
                import torch
                gc.collect()
                torch.cuda.empty_cache()
            except Exception:
                pass

    def _load_pipeline(self):
        """Initializes PyTorch Diffusers pipeline with CPU model offload to keep VRAM < 6GB."""
        if self.pipe is None and self.device == "cuda":
            try:
                import torch
                from diffusers import AutoPipelineForText2Image

                self._unload_vram()
                print(f"⚡ [GPU VRAM Management] Loading '{self.model_id}' onto RTX 5060 Ti GPU...")
                
                self.pipe = AutoPipelineForText2Image.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16,
                    variant="fp16"
                )

                if settings.enable_cuda_offload and hasattr(self.pipe, "enable_model_cpu_offload"):
                    self.pipe.enable_model_cpu_offload()
                else:
                    self.pipe.to("cuda")

            except Exception as e:
                print(f"[WARN] Failed loading PyTorch diffusers pipeline: {e}")
                self.pipe = None

    def generate_image(self, prompt_config: Dict[str, Any], output_path: str | Path, resolution: tuple[int, int] = (1920, 1080)) -> Path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        visual_prompt = prompt_config.get("visual_prompt", prompt_config.get("visual_concept", "Silicon microchip processor"))
        keywords = prompt_config.get("visual_keywords", ["technology", "processor", "hardware"])
        scene_id = prompt_config.get("scene_id", 1)

        # 1. Inferencia Local GPU con PyTorch Diffusers
        if self._is_cuda_available():
            try:
                self._load_pipeline()
                if self.pipe is not None:
                    self._unload_vram()
                    image = self.pipe(
                        prompt=visual_prompt[:250],
                        num_inference_steps=4,
                        guidance_scale=0.0
                    ).images[0]
                    
                    image = image.resize(resolution, Image.Resampling.LANCZOS)
                    image.save(out_path, quality=95)
                    print(f"✅ [100% Local GPU] SDXL-Turbo generated image for Scene #{scene_id} -> {out_path.name}")
                    return out_path
            except Exception as e:
                print(f"[WARN] GPU Local Inference Error ({e}). Executing Dynamic Semantic Fallback...")

        # 2. Dynamic Semantic Fallback Pipeline
        return self._dynamic_semantic_fallback(keywords, visual_prompt, scene_id, out_path, resolution)

    def _dynamic_semantic_fallback(self, keywords: List[str], visual_prompt: str, scene_id: int, output_path: Path, resolution: tuple[int, int]) -> Path:
        width, height = resolution

        # Intento 1: Fast AI Diffusion API (Pollinations AI) with 45s timeout
        try:
            clean_prompt = visual_prompt.split(".")[0][:140]
            encoded_prompt = urllib.parse.quote(f"{clean_prompt}, photorealistic 8k, cinematic, no text")
            seed = (scene_id * 777) + random.randint(10, 999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
            
            response = requests.get(url, timeout=settings.api_timeout_seconds)
            if response.status_code == 200 and len(response.content) > 10000:
                image = Image.open(io.BytesIO(response.content))
                image = image.resize(resolution, Image.Resampling.LANCZOS)
                image.save(output_path, quality=95)
                print(f"✅ [Semantic Fallback 1] AI Diffusion API generated image for Scene #{scene_id} -> {output_path.name}")
                return output_path
        except Exception as e:
            print(f"[WARN] Fallback 1 AI API skipped ({e}). Trying B-roll keyword fetcher...")

        # Intento 2: Dynamic B-Roll Stock Photo Matcher
        try:
            search_keyword = keywords[0] if keywords else "technology"
            unsplash_url = f"https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w={width}&h={height}&q=80"
            if "network" in search_keyword or "brics" in search_keyword or "global" in search_keyword:
                unsplash_url = f"https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w={width}&h={height}&q=80"
            elif "server" in search_keyword or "datacenter" in search_keyword:
                unsplash_url = f"https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w={width}&h={height}&q=80"

            response = requests.get(unsplash_url, timeout=12)
            if response.status_code == 200 and len(response.content) > 10000:
                image = Image.open(io.BytesIO(response.content))
                image = image.resize(resolution, Image.Resampling.LANCZOS)
                image.save(output_path, quality=95)
                print(f"✅ [Semantic Fallback 2] Stock B-Roll fetched photo ({search_keyword}) -> {output_path.name}")
                return output_path
        except Exception as e:
            print(f"[WARN] Fallback 2 B-Roll skipped ({e}).")

        # Intento 3: Adaptive Procedural Canvas by Technical Category
        print(f"✅ [Semantic Fallback 3] Rendering Categorized Adaptive Canvas for Scene #{scene_id}")
        return self._generate_adaptive_procedural_canvas(keywords, scene_id, output_path, resolution)

    def _generate_adaptive_procedural_canvas(self, keywords: List[str], scene_id: int, output_path: Path, resolution: tuple[int, int]) -> Path:
        width, height = resolution
        primary_key = keywords[0].lower() if keywords else "default"

        theme_palettes = {
            "processor": ((15, 23, 42), (218, 165, 32), "CPU / SILICON DIE"),
            "microprocessor": ((15, 23, 42), (218, 165, 32), "HARDWARE ARCHITECTURE"),
            "gpu": ((15, 23, 42), (0, 200, 83), "GRAPHICS ACCELERATION"),
            "network": ((10, 25, 47), (0, 212, 255), "GLOBAL NETWORK INFRASTRUCTURE"),
            "server": ((20, 20, 20), (255, 61, 0), "DATA CENTER RACK"),
            "default": ((18, 18, 24), (100, 108, 255), "SYSTEM INFRASTRUCTURE")
        }

        bg_color, accent_color, label_text = theme_palettes["default"]
        for key in theme_palettes:
            if key in primary_key:
                bg_color, accent_color, label_text = theme_palettes[key]
                break

        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Background grid
        for x in range(0, width, 50):
            draw.line([(x, 0), (x, height)], fill=(bg_color[0]+12, bg_color[1]+12, bg_color[2]+12), width=1)
        for y in range(0, height, 50):
            draw.line([(0, y), (width, y)], fill=(bg_color[0]+12, bg_color[1]+12, bg_color[2]+12), width=1)

        # Central HUD Frame
        margin_x = int(width * 0.2)
        margin_y = int(height * 0.25)
        draw.rectangle([margin_x, margin_y, width - margin_x, height - margin_y], outline=accent_color, width=4)
        
        # Draw category badges
        draw.text((margin_x + 30, margin_y + 30), f"CATEGORY: {label_text}", fill=accent_color)
        draw.text((margin_x + 30, margin_y + 70), f"KEYWORD: {primary_key.upper()}  |  SCENE #{scene_id:02d}", fill=(200, 200, 200))

        img.save(output_path, quality=95)
        return output_path

# Alias for backward compatibility
ImageGenerator = LocalImageGenerator
