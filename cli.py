import argparse
import sys
import os
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.settings import settings, OUTPUT_DIR
from core.source_parser import SourceParser
from core.rag_summarizer import RAGSummarizer
from core.style_matrix_engine import StyleMatrixEngine
from core.audio_generator import AudioGenerator
from core.image_generator import ImageGenerator
from core.script_writer import ScriptWriter
from core.video_assembler import VideoAssembler

def run_pipeline(source_input: str, is_file: bool = False, target_platform: str = "all"):
    print("=" * 60)
    print("[SKYTECH CONTENT ENGINE] NotebookLM-Style Local Pipeline")
    print("=" * 60)

    # 1. Parse Input Text
    if is_file:
        print(f"[1/6] Ingesting file: {source_input}")
        raw_text = SourceParser.parse_file(source_input)
    else:
        raw_text = source_input
    
    clean_text = SourceParser.clean_text(raw_text)
    print(f"-> Text loaded ({len(clean_text)} characters).")

    # 2. Extract Storyboard via Local RAG LLM (Ollama)
    print("\n[2/6] Generating scene breakdown via Local RAG LLM...")
    summarizer = RAGSummarizer()
    storyboard = summarizer.generate_storyboard(clean_text, target_platform=target_platform)
    print(f"-> Storyboard created: '{storyboard.get('title')}' with {len(storyboard.get('scenes', []))} scenes.")

    # 3. Apply Style Matrix (Anti-Monotony Prompting)
    print("\n[3/6] Applying Dynamic Style Matrix (Anti-Monotony Visual Engine)...")
    matrix_engine = StyleMatrixEngine()
    processed_scenes = []

    for scene in storyboard.get("scenes", []):
        scene_id = scene["scene_id"]
        core_concept = scene["visual_concept"]
        prompt_cfg = matrix_engine.get_diverse_prompt(scene_id, core_concept)
        scene.update(prompt_cfg)
        processed_scenes.append(scene)
        print(f"  * Scene #{scene_id}: Archetype -> [{prompt_cfg['archetype_name']}] | Shot -> {prompt_cfg['camera_shot']}")

    storyboard["scenes"] = processed_scenes

    # 4. Generate Audio & Images per Scene
    print("\n[4/6] Synthesizing Voiceover Audio & Visual Frames...")
    audio_gen = AudioGenerator()
    image_gen = ImageGenerator()

    compiled_items = []
    for scene in processed_scenes:
        scene_id = scene["scene_id"]
        narration = scene["narration_text"]
        
        audio_path = OUTPUT_DIR / f"audio_scene_{scene_id:02d}.mp3"
        image_path = OUTPUT_DIR / f"frame_scene_{scene_id:02d}.png"

        print(f"  * Synthesizing Scene #{scene_id} audio...")
        audio_gen.generate_audio(narration, audio_path)

        print(f"  * Rendering Scene #{scene_id} image keyframe...")
        image_gen.generate_image(scene, image_path, resolution=settings.res_youtube)

        compiled_items.append({
            "scene_id": scene_id,
            "audio_path": audio_path,
            "image_path": image_path
        })

    # 5. Format Scripts & Articles
    print("\n[5/6] Writing multi-platform scripts and blog article...")
    yt_script = ScriptWriter.format_for_youtube(storyboard)
    shorts_script = ScriptWriter.format_for_shortform(storyboard)
    blog_post = ScriptWriter.format_for_blog(storyboard)

    with open(OUTPUT_DIR / "youtube_script.md", "w", encoding="utf-8") as f:
        f.write(yt_script)

    with open(OUTPUT_DIR / "shorts_script.md", "w", encoding="utf-8") as f:
        f.write(shorts_script)

    with open(OUTPUT_DIR / "goslen_blog_post.md", "w", encoding="utf-8") as f:
        f.write(blog_post)

    print("-> Scripts saved to output/ (youtube_script.md, shorts_script.md, goslen_blog_post.md).")

    # 6. Assemble Final MP4 Video Outputs
    print("\n[6/6] Rendering final videos with FFmpeg/MoviePy...")
    assembler = VideoAssembler()

    yt_video_path = OUTPUT_DIR / "final_youtube_16x9.mp4"
    shorts_video_path = OUTPUT_DIR / "final_shorts_9x16.mp4"

    print(f"  * Rendering YouTube 16:9 video -> {yt_video_path.name}")
    assembler.compile_video(compiled_items, yt_video_path, resolution=settings.res_youtube)

    print(f"  * Rendering Shorts 9:16 vertical video -> {shorts_video_path.name}")
    assembler.compile_video(compiled_items, shorts_video_path, resolution=settings.res_vertical)

    print("\n" + "=" * 60)
    print(" PIPELINE COMPLETE! All assets generated successfully in ./output/")
    print(f" YouTube Video: {yt_video_path}")
    print(f" Vertical Video: {shorts_video_path}")
    print(f" Blog Post: {OUTPUT_DIR / 'goslen_blog_post.md'}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Skytech Content Engine: NotebookLM-style Video Generator")
    parser.add_argument("--file", "-f", help="Path to input text, markdown, or PDF file")
    parser.add_argument("--text", "-t", help="Raw input text string")
    parser.add_argument("--platform", "-p", default="all", choices=["all", "youtube", "shorts", "blog"], help="Target platform")
    
    args = parser.parse_args()

    if args.file:
        run_pipeline(args.file, is_file=True, target_platform=args.platform)
    elif args.text:
        run_pipeline(args.text, is_file=False, target_platform=args.platform)
    else:
        sample_text = (
            "La inteligencia artificial local ofrece soberanía de datos y menor latencia. "
            "Modelos como Qwen2.5 y Llama 3.1 permiten procesar grandes volúmenes de información en GPUs como la RTX 5060 Ti. "
            "Con la orquestación multi-agente de Antigravity, es posible transformar notas de estudio y artículos en videos automatizados."
        )
        print("No input provided. Running pipeline demonstration with default sample text...")
        run_pipeline(sample_text, is_file=False, target_platform=args.platform)

if __name__ == "__main__":
    main()
