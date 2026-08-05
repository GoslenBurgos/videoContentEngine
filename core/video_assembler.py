import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

try:
    from moviepy import ImageClip, AudioFileClip, VideoClip, concatenate_videoclips, CompositeVideoClip
except ImportError:
    from moviepy.editor import ImageClip, AudioFileClip, VideoClip, concatenate_videoclips, CompositeVideoClip

class VideoAssembler:
    """Assembles audio clips and keyframe images with real Ken Burns zoom/pan camera movement into final MP4 video."""

    @staticmethod
    def build_scene_clip(image_path: str | Path, audio_path: str | Path, resolution: tuple[int, int]) -> VideoClip:
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration if hasattr(audio, "duration") and audio.duration > 0 else 5.0
        target_w, target_h = resolution

        # Load base keyframe image with PIL
        base_img = Image.open(str(image_path)).convert("RGB")
        img_w, img_h = base_img.size

        # Fit image to target resolution if needed
        if (img_w, img_h) != resolution:
            base_img = base_img.resize(resolution, Image.Resampling.LANCZOS)
            img_w, img_h = resolution

        def make_frame(t):
            """Generates smooth Ken Burns zoom movement (zooms in from 1.0x to 1.10x)."""
            progress = t / duration if duration > 0 else 0
            zoom = 1.0 + 0.10 * progress  # 10% smooth zoom-in over duration

            w_crop = int(target_w / zoom)
            h_crop = int(target_h / zoom)

            x1 = (target_w - w_crop) // 2
            y1 = (target_h - h_crop) // 2

            cropped = base_img.crop((x1, y1, x1 + w_crop, y1 + h_crop))
            resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            return np.array(resized)

        # Create animated VideoClip using frame generator
        video_clip = VideoClip(make_frame, duration=duration)

        # Attach audio track
        if hasattr(video_clip, "with_audio"):
            final_scene = video_clip.with_audio(audio)
        else:
            final_scene = video_clip.set_audio(audio)

        return final_scene

    def compile_video(self, scene_data_list: List[Dict[str, Any]], output_path: str | Path, resolution: tuple[int, int] = (1920, 1080)) -> Path:
        """Combines animated scene clips into final MP4 video."""
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        clips = []
        for item in scene_data_list:
            clip = self.build_scene_clip(
                image_path=item["image_path"],
                audio_path=item["audio_path"],
                resolution=resolution
            )
            clips.append(clip)

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            str(out_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            logger=None
        )
        
        # Close clips to free memory
        for c in clips:
            c.close()
        final_clip.close()

        return out_path
