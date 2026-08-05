# 🚀 Skytech Content Engine (NotebookLM-Style Local AI Video Pipeline)

Un motor local de producción de video y contenido multi-plataforma inspirado en la arquitectura de **NotebookLM**, optimizado para tu rig **Skytech** (Ryzen 7 7800X3D + RTX 5060 Ti 16GB VRAM + 32GB RAM).

Transforma artículos, PDFs y notas en:
1. **Videos para YouTube** (16:9 1920x1080)
2. **TikTok / Instagram Reels / Shorts** (9:16 1080x1920)
3. **LinkedIn & Redes Sociales** (Guiones formateados)
4. **Blog de Marca Personal** ([goslen.com](https://goslen.com)) (Post SEO Markdown listo para publicar)

---

## 🎨 Solución al Problema de Imágenes Repetitivas (Style Matrix)

El motor incluye **StyleMatrixEngine** (`core/style_matrix_engine.py`) que previene la monotonía visual rotando dinámicamente entre 6+ arquetipos estéticos y 5 encuadres de cámara por cada escena:

- **Tech Minimalist Vector** (Ilustración suiza, isométrica, paleta sobria)
- **Cinematic 35mm Photography** (Lente anamórfica, iluminación dramática)
- **Dark Mode Tech Network** (HUD, red de nodos 3D en Neón)
- **Editorial Ink & Watercolor** (Tinta fina y acuarela sobre papel crema)
- **3D Isometric Glassmorphism** (Paneles de vidrio esmerilado pastel)
- **Hardware & Macro Tech** (Planos detalle de circuitos y fibra óptica)

---

## 📦 Instalación

```bash
cd "Video Create Platgform"
pip install -r requirements.txt
```

---

## ⚡ Ejecución

### 1. Ejecución de Prueba Rápida
```bash
python cli.py
```

### 2. Procesar un Archivo (PDF, Markdown, HTML, TXT)
```bash
python cli.py --file path/to/articulo.md
```

### 3. Procesar Texto Directo desde la Línea de Comandos
```bash
python cli.py --text "Tu artículo o notas aquí..."
```

---

## 🛠️ Conexión con Modelos Locales

### LLM Local (Ollama)
Por defecto se conecta a `http://localhost:11434` usando `qwen2.5:14b` o `llama3.1:8b`.
Si Ollama no está activo, el sistema utiliza un *fallback* automático.

### Generación de Imágenes (ComfyUI / SD WebUI)
Configurable en `config/settings.py`. Si ComfyUI o SD WebUI están activos en los puertos `8188` o `7860`, enviará los prompts del Style Matrix. En caso contrario, renderizará diapositivas gráficas de alta estética utilizando Pillow.

### Síntesis de Voz (Edge-TTS / Kokoro)
Utiliza la voz ultra-natural en español `es-MX-JorgeNeural` (personalizable en `settings.py`).
