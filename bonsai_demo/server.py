from __future__ import annotations

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import DEFAULT_MODEL_KEY, MODELS, OUTPUTS_DIR, resolve_model_key, validate_size
from .runtime import BonsaiRuntime


OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Bonsai Local Demo")
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")
_runtimes: dict[str, BonsaiRuntime] = {}


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = DEFAULT_MODEL_KEY
    width: int = 512
    height: int = 512
    steps: int = 4
    seed: int | None = None


def runtime_for(model: str) -> BonsaiRuntime:
    key = resolve_model_key(model)
    if key not in _runtimes:
        _runtimes[key] = BonsaiRuntime(key)
    return _runtimes[key]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return HTML


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
def models() -> list[dict[str, str]]:
    return [
        {
            "key": key,
            "display_name": spec.display_name,
            "repo_id": spec.repo_id,
        }
        for key, spec in MODELS.items()
    ]


@app.post("/generate")
async def generate(request: GenerateRequest):
    try:
        width, height = validate_size(request.width, request.height)
        runtime = runtime_for(request.model)
        result = await run_in_threadpool(
            runtime.generate,
            prompt=request.prompt,
            width=width,
            height=height,
            steps=request.steps,
            seed=request.seed,
        )
    except (FileNotFoundError, ValueError) as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
    return result


HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="dark">
  <title>bonsai</title>
  <link rel="icon" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><circle cx='8' cy='8' r='2.6' fill='%2394e0b4'/></svg>">
  <style>
    :root {
      --cream: 245, 240, 224;
      --sage:  148, 224, 180;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { background: #000; color-scheme: dark; }
    body {
      margin: 0;
      min-height: 100vh;
      background: #000;
      color: rgba(var(--cream), 0.92);
      font-family: ui-serif, "New York", "Iowan Old Style", Georgia, "Times New Roman", serif;
      font-weight: 300;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: optimizeLegibility;
      overflow-x: hidden;
    }

    main {
      min-height: 100vh;
      width: 100%;
      max-width: 760px;
      margin: 0 auto;
      padding: 20px 32px 36px;
      display: flex;
      flex-direction: column;
      align-items: stretch;
    }

    /* status whisper */
    .whisper {
      align-self: center;
      display: inline-flex;
      align-items: center;
      gap: 9px;
      min-height: 18px;
      margin-top: 4px;
      font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
      font-size: 10.5px;
      letter-spacing: 0.20em;
      color: rgba(var(--cream), 0.42);
      text-transform: lowercase;
      transition: color 0.4s ease;
    }
    .whisper .dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: rgba(var(--cream), 0.45);
      transition: background 0.3s ease;
    }
    .whisper.active .dot {
      background: rgb(var(--sage));
      animation: breathe 1.4s ease-in-out infinite alternate;
    }
    @keyframes breathe {
      from { transform: scale(0.7); opacity: 0.45; }
      to   { transform: scale(1.45); opacity: 1; }
    }

    /* wordmark */
    h1.title {
      align-self: center;
      margin: 22px 0 0;
      font-family: ui-serif, "New York", Georgia, serif;
      font-style: italic;
      font-weight: 200;
      font-size: clamp(28px, 6vw, 38px);
      letter-spacing: 0.40em;
      text-indent: 0.40em;
      color: rgba(var(--cream), 0.88);
      opacity: 0;
      transform: scale(0.97);
      animation: fadein 1.4s ease-out 0.1s forwards;
      transition: opacity 0.5s ease;
    }
    main.has-image h1.title { opacity: 0.48; }
    @keyframes fadein {
      to { opacity: 0.88; transform: scale(1); }
    }

    /* canvas */
    .canvas {
      flex: 1;
      min-height: 280px;
      width: 100%;
      display: grid;
      place-items: center;
      margin: 28px 0 32px;
    }
    .canvas img {
      grid-area: 1 / 1;
      max-width: 100%;
      max-height: 68vh;
      border-radius: 3px;
      opacity: 0;
      transform: scale(0.94);
      transition: opacity 0.65s ease-out, transform 0.65s ease-out;
    }
    .canvas img.loaded {
      opacity: 1;
      transform: scale(1);
      animation: image-breath 10s ease-in-out infinite alternate 0.65s;
    }
    @keyframes image-breath {
      from { transform: scale(1); }
      to   { transform: scale(1.006); }
    }
    .orbit {
      grid-area: 1 / 1;
      width: 84px;
      height: 84px;
      opacity: 0;
      animation: spin 3.2s linear infinite;
      transition: opacity 0.5s ease;
    }
    .orbit.visible { opacity: 0.72; }
    .orbit circle {
      fill: none;
      stroke: rgb(var(--sage));
      stroke-width: 1.4;
      stroke-linecap: round;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* form */
    form {
      width: 100%;
      max-width: 560px;
      align-self: center;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    /* prompt */
    .prompt-block { position: relative; }
    .prompt-block::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 18px;
      background: linear-gradient(to bottom, #000 0%, transparent 100%);
      pointer-events: none;
      z-index: 1;
    }
    textarea {
      width: 100%;
      background: transparent;
      border: 0;
      outline: 0;
      resize: none;
      padding: 8px 0;
      min-height: 70px;
      max-height: 220px;
      color: rgba(var(--cream), 0.92);
      font-family: ui-serif, "New York", Georgia, serif;
      font-style: italic;
      font-weight: 300;
      font-size: 19px;
      line-height: 1.45;
      caret-color: rgb(var(--sage));
      scrollbar-width: none;
    }
    textarea::-webkit-scrollbar { display: none; }
    textarea::placeholder {
      color: rgba(var(--cream), 0.28);
      font-style: italic;
    }
    .hairline {
      height: 0.5px;
      background: rgba(var(--cream), 0.16);
      transition: background 0.45s ease;
    }
    textarea:focus ~ .hairline {
      background: rgba(var(--cream), 0.32);
    }

    /* params */
    .params {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 22px;
      justify-content: center;
      font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
      font-size: 10.5px;
      letter-spacing: 0.18em;
      color: rgba(var(--cream), 0.40);
      text-transform: lowercase;
      user-select: none;
    }
    .params .group {
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .params input,
    .params select {
      background: transparent;
      border: 0;
      outline: 0;
      color: rgba(var(--sage), 0.85);
      font-family: inherit;
      font-size: inherit;
      letter-spacing: inherit;
      text-transform: lowercase;
      text-align: center;
      width: auto;
      padding: 2px;
      appearance: none;
      -webkit-appearance: none;
      cursor: pointer;
    }
    .params input { cursor: text; }
    .params input[type=number] { width: 54px; }
    .params input[name=seed]   { width: 70px; }
    .params input::placeholder { color: rgba(var(--sage), 0.42); }
    .params input:focus,
    .params select:focus { color: rgb(var(--sage)); }
    .params input::-webkit-outer-spin-button,
    .params input::-webkit-inner-spin-button {
      -webkit-appearance: none; margin: 0;
    }
    .params input[type=number] { -moz-appearance: textfield; }

    /* generate verb */
    button.generate {
      background: transparent;
      border: 0;
      outline: 0;
      color: rgb(var(--sage));
      font-family: ui-serif, "New York", Georgia, serif;
      font-style: italic;
      font-weight: 300;
      font-size: 20px;
      letter-spacing: 0.40em;
      padding: 12px 24px;
      align-self: center;
      cursor: pointer;
      text-transform: lowercase;
      display: inline-flex;
      align-items: center;
      gap: 14px;
      transition: color 0.3s ease, opacity 0.3s ease, transform 0.2s ease;
    }
    button.generate:hover { color: rgb(170, 240, 200); }
    button.generate:active { transform: translateY(1px); }
    button.generate:disabled { color: rgba(var(--cream), 0.32); cursor: default; }
    button.generate .indicator {
      display: none;
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: rgb(var(--sage));
      animation: breathe 1.2s ease-in-out infinite alternate;
    }
    body.generating button.generate .indicator { display: inline-block; }

    @media (max-width: 480px) {
      main { padding: 14px 22px 30px; }
      h1.title { letter-spacing: 0.34em; text-indent: 0.34em; }
    }
  </style>
</head>
<body>
  <main id="main">
    <div class="whisper" id="whisper">
      <span class="dot"></span>
      <span class="message" id="message">ready</span>
    </div>

    <h1 class="title">bonsai</h1>

    <div class="canvas" id="canvas">
      <img id="image" alt="">
      <svg class="orbit" id="orbit" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r="44" stroke-dasharray="80 200"/>
      </svg>
    </div>

    <form id="form">
      <div class="prompt-block">
        <textarea id="prompt" name="prompt" required spellcheck="false" placeholder="what shall we grow?">A bonsai tree in a quiet ceramic studio, soft morning light</textarea>
        <div class="hairline"></div>
      </div>

      <div class="params">
        <span class="group">
          <select id="model" name="model" aria-label="model">
            <option value="binary-mlx">binary</option>
            <option value="ternary-mlx">ternary</option>
          </select>
        </span>
        <span class="group" aria-label="size">
          <input id="width" type="number" name="width" min="256" max="2048" step="32" value="512">
          <span>×</span>
          <input id="height" type="number" name="height" min="256" max="2048" step="32" value="512">
        </span>
        <span class="group">
          <input id="steps" type="number" name="steps" min="2" max="12" value="4">
          <span>steps</span>
        </span>
        <span class="group">
          <span>seed</span>
          <input id="seed" type="number" name="seed" placeholder="↻">
        </span>
      </div>

      <button class="generate" id="submit" type="submit" aria-label="Generate image">
        <span class="indicator" aria-hidden="true"></span>
        <span id="submit-label">generate</span>
      </button>
    </form>
  </main>

  <script>
    const form         = document.getElementById("form");
    const submit       = document.getElementById("submit");
    const submitLabel  = document.getElementById("submit-label");
    const image        = document.getElementById("image");
    const orbit        = document.getElementById("orbit");
    const whisper      = document.getElementById("whisper");
    const messageEl    = document.getElementById("message");
    const main         = document.getElementById("main");
    const prompt       = document.getElementById("prompt");

    let imageEverShown = false;

    function setStatus(message, active) {
      messageEl.textContent = String(message).toLowerCase();
      whisper.classList.toggle("active", Boolean(active));
    }

    function setGenerating(on) {
      document.body.classList.toggle("generating", on);
      submit.disabled = on;
      submitLabel.textContent = on ? "growing" : "generate";
      if (on && !imageEverShown) {
        orbit.classList.add("visible");
      } else {
        orbit.classList.remove("visible");
      }
    }

    function showImage(url) {
      image.classList.remove("loaded");
      const next = new Image();
      next.onload = () => {
        image.src = url;
        requestAnimationFrame(() => {
          image.classList.add("loaded");
          main.classList.add("has-image");
          imageEverShown = true;
          orbit.classList.remove("visible");
        });
      };
      next.onerror = () => setStatus("could not load image", false);
      next.src = url;
    }

    function autosizePrompt() {
      prompt.style.height = "auto";
      const next = Math.min(220, Math.max(70, prompt.scrollHeight));
      prompt.style.height = next + "px";
    }
    prompt.addEventListener("input", autosizePrompt);
    setTimeout(autosizePrompt, 0);

    prompt.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const seedValue = data.get("seed");
      const payload = {
        prompt: String(data.get("prompt") || "").trim(),
        model: data.get("model"),
        width: Number(data.get("width")),
        height: Number(data.get("height")),
        steps: Number(data.get("steps")),
        seed: seedValue ? Number(seedValue) : null
      };
      if (!payload.prompt) return;

      setGenerating(true);
      setStatus("growing", true);

      try {
        const response = await fetch("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "generation failed");
        showImage(`${result.output_url}?t=${Date.now()}`);
        setStatus(`grown · ${payload.width}×${payload.height}`, false);
      } catch (error) {
        setStatus(error.message || "generation failed", false);
      } finally {
        setGenerating(false);
      }
    });
  </script>
</body>
</html>
"""
