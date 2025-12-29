"""FastAPI web UI for OSINT Hunter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..agent import OSINTAgent
from ..config import load_config
from ..models import ProblemInput

app = FastAPI(title="OSINT Hunter", version="0.1.0")

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

static_dir = TEMPLATES_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB safety limit


async def _save_uploads(files: List[UploadFile]) -> List[str]:
    saved: List[str] = []
    for f in files:
        if not f.filename:
            continue
        if not (f.content_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are allowed")
        data = await f.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Uploaded file too large (max 5MB)")
        suffix = Path(f.filename).suffix[:10]
        with NamedTemporaryFile(delete=False, suffix=suffix, prefix="upload_", dir="/tmp") as tmp:
            tmp.write(data)
            saved.append(tmp.name)
    return saved

def _cleanup(paths: List[str]) -> None:
    for p in paths:
        try:
            Path(p).unlink(missing_ok=True)
        except Exception:
            pass


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}




@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/run", response_class=HTMLResponse)
async def run_job(
    request: Request,
    prompt: str = Form(""),
    urls: str = Form(""),
    images: str = Form(""),
    upload: List[UploadFile] = File(default_factory=list),
):
    config = load_config()
    agent = OSINTAgent(config=config)

    url_list: List[str] = [u.strip() for u in urls.splitlines() if u.strip()]
    image_list: List[str] = [i.strip() for i in images.splitlines() if i.strip()]
    uploaded_names: List[str] = [f.filename for f in upload if f.filename]

    uploaded_paths: List[str] = []
    try:
        uploaded_paths = await _save_uploads(upload)
        combined_images = image_list + uploaded_paths
        problem = ProblemInput(text=prompt, urls=url_list, image_paths=combined_images)
        result = agent.run(problem)
    except HTTPException as exc:
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "prompt": prompt,
                "urls": url_list,
                "images": image_list + uploaded_names,
                "error": exc.detail,
                "result": None,
            },
            status_code=exc.status_code,
        )
    finally:
        _cleanup(uploaded_paths)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "prompt": prompt,
            "urls": url_list,
            "images": image_list + uploaded_names,
            "result": result,
        },
    )


@app.post("/api/run")
async def api_run(payload: dict):
    config = load_config()
    agent = OSINTAgent(config=config)
    prompt = payload.get("prompt", "")
    urls = payload.get("urls", []) or []
    images = payload.get("images", []) or []
    problem = ProblemInput(text=prompt, urls=urls, image_paths=images)
    result = agent.run(problem)
    return JSONResponse(
        {
            "plan": [step.title for step in result.plan],
            "evidence": [ev.__dict__ for ev in result.evidence],
            "flags": result.flag_candidates,
            "notes": result.notes,
        }
    )


@app.exception_handler(Exception)
async def handle_errors(request: Request, exc: Exception):
    return JSONResponse({"error": str(exc)}, status_code=500)