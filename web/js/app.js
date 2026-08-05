// Global Dashboard State
let currentStoryboard = null;
let pollTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  checkHealth();
  initIngestion();
  initStoryboardEvents();
});

// Open Output Folder in Windows Explorer
async function openFolderInExplorer() {
  try {
    const res = await fetch("/api/open-folder", { method: "POST" });
    const data = await res.json();
    console.log("Opened folder:", data);
  } catch (err) {
    alert("Error al abrir carpeta: " + err.message);
  }
}

// Tab Switcher
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      
      btn.classList.add("active");
      const panelId = btn.getAttribute("data-tab");
      document.getElementById(panelId).classList.add("active");
    });
  });
}

// Health Check API
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    
    // Ollama badge
    const ollamaDot = document.getElementById("ollamaDot");
    const ollamaStatus = document.getElementById("ollamaStatus");
    if (data.services.ollama.online) {
      ollamaDot.classList.add("online");
      ollamaStatus.textContent = `Ollama (${data.services.ollama.model})`;
    } else {
      ollamaStatus.textContent = "Ollama (Offline - Fallback)";
    }

    // ComfyUI badge
    const comfyDot = document.getElementById("comfyDot");
    const comfyStatus = document.getElementById("comfyStatus");
    if (data.services.comfyui.online) {
      comfyDot.classList.add("online");
      comfyStatus.textContent = "ComfyUI (Online)";
    } else {
      comfyStatus.textContent = "ComfyUI (Offline - Dynamic Graphic Slide)";
    }

  } catch (err) {
    console.error("Health check error:", err);
  }
}

// Ingestion Handlers
function initIngestion() {
  const fileInput = document.getElementById("fileInput");
  const textInput = document.getElementById("rawTextInput");
  const textStats = document.getElementById("textStats");
  const btnGenerate = document.getElementById("btnGenerateStoryboard");

  fileInput.addEventListener("change", async (e) => {
    if (!e.target.files.length) return;
    const file = e.target.files[0];
    document.getElementById("fileNameDisplay").textContent = `📄 ${file.name}`;

    const formData = new FormData();
    formData.append("file", file);

    try {
      btnGenerate.disabled = true;
      btnGenerate.textContent = "⌛ Procesando archivo...";
      const res = await fetch("/api/parse-file", { method: "POST", body: formData });
      const data = await res.json();

      textInput.value = data.clean_text;
      textStats.textContent = `${data.char_count} caracteres | ${data.word_count} palabras`;
    } catch (err) {
      alert("Error al leer el archivo: " + err.message);
    } finally {
      btnGenerate.disabled = false;
      btnGenerate.textContent = "🧠 Generar Storyboard RAG";
    }
  });

  textInput.addEventListener("input", () => {
    const text = textInput.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    textStats.textContent = `${text.length} caracteres | ${words} palabras`;
  });

  btnGenerate.addEventListener("click", async () => {
    const text = textInput.value.trim();
    if (!text) {
      alert("Por favor ingresa o carga un texto primero.");
      return;
    }

    try {
      btnGenerate.disabled = true;
      btnGenerate.textContent = "🧠 Generando Escenas RAG con Ollama...";

      const res = await fetch("/api/generate-storyboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, target_platform: "all" })
      });

      currentStoryboard = await res.json();
      renderSceneCards(currentStoryboard.scenes);

      // Switch to tab 2
      document.querySelector('[data-tab="tab-storyboard"]').click();

    } catch (err) {
      alert("Error al generar storyboard: " + err.message);
    } finally {
      btnGenerate.disabled = false;
      btnGenerate.textContent = "🧠 Generar Storyboard RAG";
    }
  });
}

// Scene Card Renderer
function renderSceneCards(scenes) {
  const container = document.getElementById("scenesContainer");
  container.innerHTML = "";

  if (!scenes || !scenes.length) {
    container.innerHTML = `<div style="color: var(--text-muted);">No hay escenas disponibles.</div>`;
    return;
  }

  scenes.forEach((scene) => {
    const card = document.createElement("div");
    card.className = "scene-card";

    card.innerHTML = `
      <div class="scene-header">
        <span class="scene-badge">Escena #${scene.scene_id}</span>
        <span style="font-size: 0.8rem; color: var(--text-muted);">${scene.estimated_duration_sec}s</span>
      </div>

      <div>
        <label style="font-size: 0.75rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Voz en Off (Narration):</label>
        <textarea style="height: 70px; font-size: 0.85rem;" onchange="updateSceneText(${scene.scene_id}, this.value)">${scene.narration_text}</textarea>
      </div>

      <div>
        <label style="font-size: 0.75rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Arquetipo Estético (Style Matrix):</label>
        <select onchange="updateSceneStyle(${scene.scene_id}, this.value)">
          <option value="tech_minimalist" ${scene.archetype_key === 'tech_minimalist' ? 'selected' : ''}>Tech Minimalist Vector</option>
          <option value="cinematic_photo" ${scene.archetype_key === 'cinematic_photo' ? 'selected' : ''}>Cinematic 35mm Photography</option>
          <option value="dark_ui_blueprint" ${scene.archetype_key === 'dark_ui_blueprint' ? 'selected' : ''}>Dark Mode UI Network</option>
          <option value="editorial_watercolor" ${scene.archetype_key === 'editorial_watercolor' ? 'selected' : ''}>Editorial Ink & Watercolor</option>
          <option value="isometric_glassmorphism" ${scene.archetype_key === 'isometric_glassmorphism' ? 'selected' : ''}>3D Isometric Glassmorphism</option>
          <option value="cyberpunk_macro" ${scene.archetype_key === 'cyberpunk_macro' ? 'selected' : ''}>Cyberpunk Hardware Macro</option>
        </select>
      </div>

      <div>
        <label style="font-size: 0.75rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Encuadre de Cámara:</label>
        <input type="text" value="${scene.camera_shot}" onchange="updateSceneCamera(${scene.scene_id}, this.value)">
      </div>
    `;

    container.appendChild(card);
  });
}

function updateSceneText(sceneId, text) {
  const sc = currentStoryboard.scenes.find(s => s.scene_id === sceneId);
  if (sc) sc.narration_text = text;
}

function updateSceneStyle(sceneId, styleKey) {
  const sc = currentStoryboard.scenes.find(s => s.scene_id === sceneId);
  if (sc) sc.archetype_key = styleKey;
}

function updateSceneCamera(sceneId, camText) {
  const sc = currentStoryboard.scenes.find(s => s.scene_id === sceneId);
  if (sc) sc.camera_shot = camText;
}

// Storyboard & Render Execution
function initStoryboardEvents() {
  const btnRender = document.getElementById("btnTriggerRender");
  btnRender.addEventListener("click", async () => {
    if (!currentStoryboard) {
      alert("Genera primero el storyboard.");
      return;
    }

    try {
      btnRender.disabled = true;
      const res = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ storyboard: currentStoryboard })
      });
      await res.json();

      // Switch to studio tab & start polling progress
      document.querySelector('[data-tab="tab-studio"]').click();
      startPollingProgress();

    } catch (err) {
      alert("Error al iniciar render: " + err.message);
    } finally {
      btnRender.disabled = false;
    }
  });
}

function startPollingProgress() {
  if (pollTimer) clearInterval(pollTimer);

  pollTimer = setInterval(async () => {
    try {
      const res = await fetch("/api/render-status");
      const status = await res.json();

      document.getElementById("renderStepText").textContent = status.current_step;
      document.getElementById("renderProgressPct").textContent = `${status.progress}%`;
      document.getElementById("progressBar").style.width = `${status.progress}%`;

      const term = document.getElementById("terminalLog");
      term.innerHTML = status.log.map(l => `> ${l}`).join("<br>");
      term.scrollTop = term.scrollHeight;

      if (status.status === "complete") {
        clearInterval(pollTimer);
        document.getElementById("blogMarkdownOutput").value = status.outputs.blog_md || "";
        
        // Reload video players
        document.getElementById("srcYoutube").src = status.outputs.youtube_mp4 + "?t=" + Date.now();
        document.getElementById("srcShorts").src = status.outputs.shorts_mp4 + "?t=" + Date.now();

        document.getElementById("playerYoutube").load();
        document.getElementById("playerShorts").load();
      } else if (status.status === "error") {
        clearInterval(pollTimer);
      }

    } catch (err) {
      console.error("Polling error:", err);
    }
  }, 1500);
}

function copyBlogMarkdown() {
  const txt = document.getElementById("blogMarkdownOutput");
  txt.select();
  document.execCommand("copy");
  alert("¡Markdown del post para goslen.com copiado al portapapeles!");
}
