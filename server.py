import os
import json
import shutil
import sys
import webbrowser
import threading
import time
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from config.settings import settings, OUTPUT_DIR
from core.source_parser import SourceParser
from core.rag_summarizer import RAGSummarizer
from core.style_matrix_engine import StyleMatrixEngine
from core.audio_generator import AudioGenerator
from core.image_generator import ImageGenerator
from core.script_writer import ScriptWriter
from core.video_assembler import VideoAssembler

app = FastAPI(title="Skytech Content Engine Dashboard", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory render status
render_state = {
    "status": "idle", # idle, processing, complete, error
    "progress": 0,
    "current_step": "",
    "log": [],
    "outputs": {}
}

# Mount static directories
WEB_DIR = Path(__file__).parent / "web"
WEB_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

class TextIngestRequest(BaseModel):
    text: str

class StoryboardRequest(BaseModel):
    text: str
    target_platform: str = "all"

class RenderRequest(BaseModel):
    storyboard: Dict[str, Any]

@app.get("/api/health")
def health_check():
    # Check Ollama
    ollama_ok = False
    try:
        r = requests.get(f"{settings.ollama_url}/api/tags", timeout=1)
        ollama_ok = r.status_code == 200
    except Exception:
        pass

    # Check ComfyUI
    comfy_ok = False
    try:
        r = requests.get(f"{settings.comfyui_url}/system_stats", timeout=1)
        comfy_ok = r.status_code == 200
    except Exception:
        pass

    matrix_engine = StyleMatrixEngine()

    return {
        "status": "online",
        "rig": "Skytech Rig (Ryzen 7 7800X3D + RTX 5060 Ti 16GB VRAM)",
        "output_folder": str(OUTPUT_DIR),
        "services": {
            "ollama": {"url": settings.ollama_url, "online": ollama_ok, "model": settings.ollama_model},
            "comfyui": {"url": settings.comfyui_url, "online": comfy_ok},
            "tts": {"engine": settings.default_tts_engine, "voice": settings.default_voice_es}
        },
        "style_archetypes": matrix_engine.archetypes,
        "camera_shots": matrix_engine.camera_shots
    }

@app.post("/api/open-folder")
def open_output_folder():
    """Opens the local output folder directly in Windows File Explorer."""
    try:
        os.startfile(str(OUTPUT_DIR))
        return {"status": "success", "message": f"Opened folder: {OUTPUT_DIR}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parse-file")
async def parse_uploaded_file(file: UploadFile = File(...)):
    temp_path = OUTPUT_DIR / f"uploaded_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        raw_text = SourceParser.parse_file(temp_path)
        clean_text = SourceParser.clean_text(raw_text)
        
        return {
            "filename": file.filename,
            "char_count": len(clean_text),
            "word_count": len(clean_text.split()),
            "clean_text": clean_text
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

@app.post("/api/generate-storyboard")
def generate_storyboard(req: StoryboardRequest):
    try:
        summarizer = RAGSummarizer()
        storyboard = summarizer.generate_storyboard(req.text, target_platform=req.target_platform)
        
        matrix_engine = StyleMatrixEngine()
        scenes = storyboard.get("scenes", [])
        for scene in scenes:
            visual_text = scene.get("visual_prompt", scene.get("visual_concept", "Silicon microchip processor"))
            prompt_cfg = matrix_engine.get_diverse_prompt(scene["scene_id"], visual_text)
            scene.update(prompt_cfg)
        
        storyboard["scenes"] = scenes
        return storyboard
    except Exception as e:
        print(f"[Error generate_storyboard]: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating storyboard: {str(e)}")

def _execute_render_job(storyboard: Dict[str, Any]):
    global render_state
    render_state["status"] = "processing"
    render_state["progress"] = 10
    render_state["log"] = ["Starting multi-platform render job..."]

    try:
        matrix_engine = StyleMatrixEngine()
        audio_gen = AudioGenerator()
        image_gen = ImageGenerator()
        assembler = VideoAssembler()

        scenes = storyboard.get("scenes", [])
        compiled_items = []

        total_scenes = len(scenes)
        for idx, scene in enumerate(scenes, start=1):
            scene_id = scene["scene_id"]
            render_state["current_step"] = f"Processing Scene #{scene_id} ({idx}/{total_scenes})"
            render_state["log"].append(f"Scene #{scene_id}: Synthesizing voiceover & motion keyframe...")

            audio_path = OUTPUT_DIR / f"audio_scene_{scene_id:02d}.mp3"
            image_path = OUTPUT_DIR / f"frame_scene_{scene_id:02d}.png"

            audio_gen.generate_audio(scene["narration_text"], audio_path)
            image_gen.generate_image(scene, image_path, resolution=settings.res_youtube)

            compiled_items.append({
                "scene_id": scene_id,
                "audio_path": audio_path,
                "image_path": image_path
            })
            
            pct = 10 + int((idx / total_scenes) * 50)
            render_state["progress"] = pct

        # Scripts
        render_state["current_step"] = "Formatting scripts & blog post..."
        yt_script = ScriptWriter.format_for_youtube(storyboard)
        shorts_script = ScriptWriter.format_for_shortform(storyboard)
        blog_post = ScriptWriter.format_for_blog(storyboard)

        with open(OUTPUT_DIR / "youtube_script.md", "w", encoding="utf-8") as f:
            f.write(yt_script)
        with open(OUTPUT_DIR / "shorts_script.md", "w", encoding="utf-8") as f:
            f.write(shorts_script)
        with open(OUTPUT_DIR / "goslen_blog_post.md", "w", encoding="utf-8") as f:
            f.write(blog_post)

        render_state["progress"] = 70
        render_state["current_step"] = "Rendering YouTube 16:9 video..."
        render_state["log"].append("Rendering 16:9 YouTube video with Ken Burns motion graphics...")
        
        yt_path = OUTPUT_DIR / "final_youtube_16x9.mp4"
        assembler.compile_video(compiled_items, yt_path, resolution=settings.res_youtube)

        render_state["progress"] = 85
        render_state["current_step"] = "Rendering Shorts 9:16 video..."
        render_state["log"].append("Rendering 9:16 Shorts/Reels video with Ken Burns motion graphics...")
        
        shorts_path = OUTPUT_DIR / "final_shorts_9x16.mp4"
        assembler.compile_video(compiled_items, shorts_path, resolution=settings.res_vertical)

        render_state["progress"] = 100
        render_state["status"] = "complete"
        render_state["current_step"] = "Pipeline completed successfully!"
        render_state["log"].append("Render complete! Video files ready in ./output/")

        render_state["outputs"] = {
            "youtube_mp4": "/output/final_youtube_16x9.mp4",
            "shorts_mp4": "/output/final_shorts_9x16.mp4",
            "blog_md": blog_post,
            "youtube_script": yt_script,
            "shorts_script": shorts_script,
            "folder_path": str(OUTPUT_DIR)
        }

    except Exception as e:
        render_state["status"] = "error"
        render_state["current_step"] = f"Error: {str(e)}"
        render_state["log"].append(f"EXCEPTION: {str(e)}")

@app.post("/api/render")
def trigger_render(req: RenderRequest, bg_tasks: BackgroundTasks):
    global render_state
    if render_state["status"] == "processing":
        raise HTTPException(status_code=400, detail="A render job is already running.")

    bg_tasks.add_task(_execute_render_job, req.storyboard)
    return {"message": "Render job started in background."}

@app.get("/api/render-status")
def get_render_status():
    return render_state

# Serve Web UI SPA
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

def _auto_open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{settings.dashboard_port}")

if __name__ == "__main__":
    import uvicorn
    print(f"Skytech Content Engine Dashboard running at http://localhost:{settings.dashboard_port}")
    threading.Thread(target=_auto_open_browser, daemon=True).start()
    uvicorn.run("server:app", host=settings.dashboard_host, port=settings.dashboard_port)
