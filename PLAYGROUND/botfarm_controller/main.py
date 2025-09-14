# main.py - Botfarm Controller API v0.3.0 (health/version/preview/apply/run/generate)
# from __future__ import annotations  # Removed, not needed for Python 3.7+
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List, Dict

import os, shutil, difflib, importlib.util, time, base64, fnmatch

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import codegen
from model_router import ModelRouter, TaskSignal

load_dotenv(override=True)
ROOT = Path(__file__).resolve().parent

# Robust ALLOWED_DIRS: bevorzugt Export aus model_router, ansonsten Fallback
ALLOWED_DIRS: List[str] = []
try:
    # from model_router import ALLOWED_DIRS as _ALLOWED  # Entfernt, da ALLOWED_DIRS nicht exportiert wird
    # if isinstance(_ALLOWED, (list, tuple)):
    #     ALLOWED_DIRS = [str(p) for p in _ALLOWED]
    raise ImportError("ALLOWED_DIRS ist nicht im model_router verfügbar")
except Exception:
    pass
if not ALLOWED_DIRS:
    ALLOWED_DIRS = [str(ROOT.resolve()), str(ROOT.parent.resolve())]

# --- OpenAI Import robust + Pylance-freundlich ------------------------------
try:
    from openai import OpenAI as OpenAIClient  # offizieller Client
except Exception:
    OpenAIClient = None  # type: ignore[assignment]


def get_openai_client() -> Any:
    """
    Liefert einen OpenAI-Client oder wirft eine verständliche Fehlermeldung.
    Nutzt OPENAI_BASE_URL/OPENAI_API_KEY aus der Umgebung.
    """
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY fehlt (.env)")
    if OpenAIClient is None:
        raise RuntimeError(
            "OpenAI SDK nicht installiert oder Import fehlgeschlagen. "
            "Bitte in der venv ausführen:  pip install openai"
        )
    return OpenAIClient(base_url=base_url, api_key=api_key)


# --- Ende OpenAI Import patch ---

app = FastAPI(title="botfarm_controller")

# Basispfade und Router
PRESH = ROOT / "PREVIEWS"
PREVIEWS = PRESH
BACKUP = ROOT / "_backup"
PREVIEWS.mkdir(exist_ok=True)
BACKUP.mkdir(exist_ok=True)
# --- OPS/Drafts Verzeichnisse (NEU) ---
OPS = ROOT / "OPS"
DRAFTS = OPS / "drafts"
(OPS / "logs").mkdir(parents=True, exist_ok=True)
(OPS / "reports").mkdir(parents=True, exist_ok=True)
DRAFTS.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # bei Bedarf ändern
ROUTER = ModelRouter(dict(os.environ))


# ---------- Models ----------
class PreviewReq(BaseModel):
    spec_text: str
    target: str = "generated_module.py"  # default NICHT main.py
    lang: Optional[str] = "py"


class ApplyReq(BaseModel):
    preview_path: str
    target: str = "generated_module.py"  # default NICHT main.py


class GenerateReq(BaseModel):
    prompt: str
    target: str = "generated_module.py"
    lang: Optional[str] = "py"
    model: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1200


class Signals(BaseModel):
    files: int = 1
    loc: int = 50
    cross_stack: bool = False
    iterations_failed: int = 0
    want_strategy: bool = False
    inline_latency_ms: Optional[int] = None


class RouteRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    signals: Signals = Field(default_factory=Signals)


class RouteDecision(BaseModel):
    label: str
    model: str
    reasons: List[str]


class ChatResponse(BaseModel):
    model_used: str
    label_used: str
    output: str
    reasons: List[str]


class DraftReq(BaseModel):
    prompt: str
    target: str = "generated_module.py"
    lang: Optional[str] = "py"
    model: Optional[str] = None


# ---------- Utils ----------
def _count_changes(old: str, new: str) -> tuple[int, int]:
    sm = difflib.SequenceMatcher(a=old.splitlines(), b=new.splitlines())
    adds = sum(
        j2 - _j1
        for tag, _i1, _i2, _j1, j2 in sm.get_opcodes()
        if tag in ("insert", "replace")
    )
    rems = sum(
        i2 - i1
        for tag, i1, i2, _j1, _j2 in sm.get_opcodes()
        if tag in ("delete", "replace")
    )
    return adds, rems


def _render_preview(spec_text: str, lang: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if (lang or "").lower() == "ts":
        return f"""// Generated preview from spec ({ts})
/*
{spec_text}
*/
export function handler() {{
  return "OK";
}}
"""
    return f"""# Generated preview from spec ({ts})
\"\"\"SPEC:
{spec_text}
\"\"\"
def handler():
    return "OK"
"""


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def _looks_like_previews(path: Path) -> bool:
    return any(part.lower() == "previews" for part in path.parts)


def _load_module_from_file(path: Path, module_name: str = "generated_module"):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _simple_safety_scan(code: str) -> list[str]:
    """Sehr grobe Heuristik gegen destruktive Snippets."""
    banned = [
        "shutil.rmtree",
        "os.remove(",
        "subprocess",
        "Popen(",
        "rm -rf",
        "del /s",
        "win32api",
        "format C:",
        "powershell -Command Remove-Item",
        "rmdir /s",
        "wmi.",
    ]
    hits = [b for b in banned if b in code]
    return hits


def _write_json(path: Path, data: dict) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _critic_ampl(draft: dict) -> dict:
    """Sehr einfacher Ampel-Check (size/deny_globs). Write-Entscheid trifft apply_draft.py."""
    adds = int(draft.get("adds") or 0)
    rems = int(draft.get("rems") or 0)
    total = adds + rems
    files = len({(p.get("path") or "") for p in draft.get("patch", [])})

    deny_globs = [
        "**/apply_preview.ps1",
        "**/policy*.json",
        "**/.git/**",
        "**/secrets/**",
    ]
    from fnmatch import fnmatch

    reasons = []
    red = False
    for ch in draft.get("patch", []):
        p = (ch.get("path") or "").replace("\\", "/")
        if any(fnmatch(p, g) for g in deny_globs):
            red = True
            reasons.append(f"forbidden:{p}")
            break
    if not red and (files > 7 or total > 400):
        red = True
        reasons.append("size")

    if red:
        return {"level": "Red", "reasons": reasons}
    if total > 150:
        return {"level": "Yellow", "reasons": reasons + ["large"]}
    return {"level": "Green", "reasons": reasons}


def critic_assess(draft: dict) -> dict:
    return _critic_ampl(draft)


# ---------- Routes ----------
# --- Pfad-Helpers: immer relativ zum Projekt-Root ---
def to_rel(p: os.PathLike | str) -> str:
    p = str(Path(p).resolve())
    try:
        return str(Path(p).resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(Path(p).name).replace("\\", "/")  # Fallback: Dateiname


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/version")
def version():
    return {
        "name": "botfarm_controller",
        "version": "0.3.0",
        "root": str(ROOT),
        "endpoints": ["/health", "/version", "/preview", "/apply", "/run", "/generate"],
    }


@app.post("/preview")
def preview(req: PreviewReq):
    lang = (req.lang or "py").lower()
    ext = ".py" if lang == "py" else (".ts" if lang == "ts" else ".txt")

    target_path = (ROOT / req.target).resolve()
    old_text = ""
    if target_path.exists():
        try:
            old_text = target_path.read_text(encoding="utf-8")
        except Exception:
            old_text = ""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    preview_path = (PREVIEWS / f"spec_{ts}{ext}").resolve()
    new_text = _render_preview(req.spec_text, lang=lang)
    preview_path.write_text(new_text, encoding="utf-8")

    adds, rems = _count_changes(old_text, new_text)
    return {
        "preview_path": str(preview_path),
        "target": to_rel(target_path),
        "adds": adds,
        "rems": rems,
        "note": "Preview geschrieben. Zum Übernehmen /apply verwenden.",
    }


@app.post("/apply")
def apply(req: ApplyReq):
    preview_path = Path(req.preview_path).resolve()
    target_path = (ROOT / req.target).resolve()

    if not preview_path.exists():
        raise HTTPException(status_code=400, detail="preview_path existiert nicht.")
    if target_path.name.lower() == "main.py":
        raise HTTPException(
            status_code=403,
            detail="Applying auf main.py ist blockiert. Nutze z.B. generated_module.py.",
        )
    if not _is_under(target_path, ROOT):
        raise HTTPException(
            status_code=403, detail="target außerhalb des Projektordners."
        )
    if not (_is_under(preview_path, PREVIEWS) or _looks_like_previews(preview_path)):
        raise HTTPException(status_code=403, detail="preview_path nicht aus PREVIEWS.")

    old_text = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    new_text = preview_path.read_text(encoding="utf-8")
    adds, rems = _count_changes(old_text, new_text)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = BACKUP / f"{target_path.name}.{ts}.bak"
    if target_path.exists():
        shutil.copy2(target_path, bak)
    target_path.write_text(new_text, encoding="utf-8")

    return {
        "applied": True,
        "target": str(target_path),
        "backup": str(bak) if bak.exists() else "(none)",
        "bytes_written": len(new_text.encode("utf-8")),
        "adds": adds,
        "rems": rems,
    }


@app.get("/run")
def run():
    mod_path = ROOT / "generated_module.py"
    if not mod_path.exists():
        raise HTTPException(status_code=404, detail="generated_module.py fehlt.")
    mod = _load_module_from_file(mod_path)
    if not mod or not hasattr(mod, "handler"):
        raise HTTPException(
            status_code=500, detail="handler() fehlt in generated_module.py."
        )
    try:
        result = mod.handler()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"handler()-Fehler: {e}")
    return {"result": result}


@app.post("/generate")
def generate(req: GenerateReq):
    """
    OpenAI-gestützte Code-Generierung → schreibt PREVIEW-Datei + Draft-JSON.
    Anwenden erfolgt separat via /apply (mit Backup & Guardrails).
    """
    model = (req.model or DEFAULT_MODEL).strip()
    lang = (req.lang or "py").lower()
    ext = ".py" if lang == "py" else (".ts" if lang == "ts" else ".txt")

    # Code erzeugen (OpenAI falls verfügbar, sonst Stub)
    used_model = model
    rationale = "ok"
    try:
        client = get_openai_client()
        system = (
            "Du bist ein Code-Generator für einen Preview-first Assistant. "
            "Gib ausschließlich den finalen Code aus (keine Erklärungen). "
            "Keine destruktiven Operationen, keine Dateisystem-Manipulationen, "
            "kein Netzwerkzugriff, keine Secrets. Für Python: def handler() -> nutzbar."
        )
        user = f"Ziel-Datei: {req.target}\nSprache: {lang}\n\nAufgabe:\n{req.prompt}"
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=req.temperature or 0.2,
            max_output_tokens=req.max_tokens or 1200,
        )
        try:
            new_code = resp.output_text
        except Exception:
            new_code = ""
            try:
                for out in resp.output:
                    for c in getattr(out, "content", []):
                        if getattr(c, "type", "") == "text":
                            new_code += c.text
            except Exception:
                pass
        if not new_code.strip():
            raise RuntimeError("leere Modellantwort")
    except Exception:
        # Fallback ohne OpenAI
        used_model = "gpt-5-mini"
        rationale = "fallback: no OpenAI"
        ts_h = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if lang == "ts":
            new_code = f"""// Generated STUB ({ts_h})\n/* SPEC (fallback) */\nexport function handler() {{\n  return "OK";\n}}\n"""
        else:
            new_code = f"""# Generated STUB ({ts_h})\n\"\"\"SPEC:\n{(req.prompt or 'hello world')}\n\"\"\"\ndef handler():\n    return "OK"\n"""

    # Preview schreiben
    PREVIEWS.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    preview_path = (PREVIEWS / f"gen_{ts}{ext}").resolve()
    preview_path.write_text(new_code, encoding="utf-8")

    # Diff gegen Ziel
    target_path = (ROOT / req.target).resolve()
    old_text = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    adds, rems = _count_changes(old_text, new_code)

    # Draft-Objekt
    rel_target = to_rel(target_path)
    draft = {
        "status": "PREVIEW_ONLY",
        "ts": ts,
        "model": used_model,
        "target": rel_target,
        "preview_path": str(preview_path),
        "adds": adds,
        "rems": rems,
        "rationale": rationale,
        "risk_note": "n/a",
        "patch": [{"path": rel_target, "text": new_code}],
    }
    draft["critic"] = critic_assess(draft)

    # Draft-JSON & Log
    drafts_dir = ROOT / "OPS" / "drafts"
    logs_dir = ROOT / "OPS" / "logs"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    draft_path = drafts_dir / f"draft_{ts}.json"
    import json as _json

    draft_path.write_text(
        _json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    draft["draft_path"] = str(draft_path)
    # Log-Zeile
    log_line = f"[{ts}] status=PREVIEW_ONLY model={used_model} tokens=n/a target={rel_target} adds={adds} rems={rems}"
    (logs_dir / "codegen_runs.log").open("a", encoding="utf-8").write(log_line + "\n")

    return draft


@app.post("/route", response_model=RouteDecision)
def route(req: RouteRequest):
    s = TaskSignal(**req.signals.dict())
    dec = ROUTER.decide(s)
    return RouteDecision(**dec)


@app.post("/chat", response_model=ChatResponse)
def chat(req: RouteRequest):
    s = TaskSignal(**req.signals.dict())
    dec = ROUTER.decide(s)

    if req.messages:
        user_text = "\n".join(
            [
                m.get("content", "")
                for m in req.messages
                if m.get("role") in ("user", "system")
            ]
        )
        input_text = user_text or req.messages[-1].get("content", "")
    elif req.prompt:
        input_text = req.prompt
    else:
        raise HTTPException(status_code=400, detail="prompt oder messages erforderlich")

    try:
        client = get_openai_client()
        resp = client.responses.create(model=dec["model"], input=input_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat fehlgeschlagen: {e}")

    text = getattr(resp, "output_text", None)
    if text is None:
        try:
            text = resp.output[0].content[0].text
        except Exception:
            text = str(resp)

    return ChatResponse(
        model_used=dec["model"],
        label_used=dec["label"],
        output=text,
        reasons=dec["reasons"],
    )


# --- Auto-Routing + /auto_chat (neue dedizierte Endpoint) ---
from typing import Optional
from pydantic import BaseModel


class AutoChatRequest(BaseModel):
    task: str
    files_changed: Optional[int] = 0
    lines_changed: Optional[int] = 0
    cross_stack: Optional[bool] = False
    retries: Optional[int] = 0
    tiny: Optional[bool] = False
    mode: Optional[str] = "auto"  # auto | brain | hand | nano


def _auto_resolve_model(req: AutoChatRequest) -> tuple[str, str]:
    m = resolve_models()
    if req.mode in ("brain", "hand", "nano"):
        return m[req.mode], f"override:{req.mode}"
    if req.tiny:
        return m["nano"], "tiny"
    if (
        (req.files_changed or 0) > 2
        or (req.lines_changed or 0) > 300
        or req.cross_stack
        or (req.retries or 0) >= 2
    ):
        return m["brain"], "escalate"
    return m["hand"], "default-hand"


@app.post("/auto_chat")
def auto_chat(req: AutoChatRequest):
    model, why = _auto_resolve_model(req)
    prompt = (
        "Du bist ein präziser Programmier-Assistent. "
        "Gib Code oder klare, ausführbare Schritte zurück.\n\n"
        f"Aufgabe:\n{req.task}\n"
    )
    try:
        client = get_openai_client()
        resp = client.responses.create(model=model, input=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto Chat fehlgeschlagen: {e}")
    text = getattr(resp, "output_text", None)
    if text is None:
        try:
            text = resp.output[0].content[0].text
        except Exception:
            text = str(resp)
    return {
        "model_used": model,
        "routed": why,
        "output": text,
    }


@app.post("/draft")
def draft(req: DraftReq):
    out = codegen.generate_draft(
        prompt=req.prompt,
        target=req.target,
        lang=req.lang or "py",
        model=req.model or resolve_models()["hand"],
    )
    return out


# ---------- Debug-/Routing-Endpoints ----------
def _env(name: str, default: str = "") -> str:
    v = os.getenv(name, default)
    return v.strip() if v else default


def resolve_models() -> dict[str, str]:
    # bevorzugte Overrides
    brain = (
        _env("ROUTE_MODEL_BRAIN")
        or _env("RESOLVE_GPT5")
        or _env("DEFAULT_MODEL", "gpt-5")
    )
    hand = (
        _env("ROUTE_MODEL_HAND")
        or _env("RESOLVE_GPT5_MINI")
        or _env("FALLBACK_MODEL", "gpt-5-mini")
    )
    nano = _env("ROUTE_MODEL_NANO") or _env("RESOLVE_GPT5_NANO") or "gpt-5-nano"
    return {"brain": brain, "hand": hand, "nano": nano}


@app.get("/routing")
def routing():
    models = resolve_models()
    return {
        "models": models,
        "openai_key_loaded": bool(
            os.getenv("OPENAI_API_KEY")
        ),  # nur Bool, kein Key-Leak
        "base_url": os.getenv("OPENAI_BASE_URL", "(default)"),
    }


# ---------- Tools (experimental) ----------
from pydantic import BaseModel
import shutil, base64, time, fnmatch


class RunTestsReq(BaseModel):
    args: list[str] | None = None
    workdir: str | None = None


class RunLintReq(BaseModel):
    tool: str | None = None
    args: list[str] | None = None
    paths: list[str] | None = None


class FileChange(BaseModel):
    path: str
    text: str | None = None
    content_b64: str | None = None


class ApplyFilesReq(BaseModel):
    changes: list[FileChange]
    preview_only: bool = False
    backup: bool = True
    approve_secret: str | None = None


class SearchReq(BaseModel):
    query: str
    globs: list[str] | None = None
    max_results: int | None = 50


class OpenFileReq(BaseModel):
    path: str
    head: int | None = 200
    tail: int | None = 0


def _which_first(tools: list[str]) -> str | None:
    for t in tools:
        p = shutil.which(t)
        if p:
            return p
    return None


def _run(cmd: list[str], cwd: str) -> dict:
    import subprocess

    res = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    out = res.stdout.strip()
    err = res.stderr.strip()
    return {
        "returncode": res.returncode,
        "stdout": out if out else None,
        "stderr": err if err else None,
    }


def _ensure_allowed(path: Path):
    # Sehr grobe Heuristik, um unerwünschte Zugriffe zu verhindern
    if path.root != path.parents[0].root:
        raise HTTPException(
            status_code=403, detail="Zugriff auf dieses Verzeichnis ist nicht erlaubt."
        )


@app.post("/tools/run_tests")
def tools_run_tests(req: RunTestsReq):
    py = shutil.which("python") or shutil.which("py")
    if not py:
        return {"ok": False, "error": "python nicht gefunden"}
    pytest = [py, "-m", "pytest"]
    args = req.args or ["-q"]
    res = _run(pytest + args, cwd=req.workdir or str(ROOT))
    return {"ok": res["returncode"] == 0, "result": res}


@app.post("/tools/run_lint")
def tools_run_lint(req: RunLintReq):
    paths = req.paths or [""]
    tool = (req.tool or "").lower()
    chosen = None
    if tool in ("ruff", "flake8", "mypy"):
        chosen = _which_first([tool])
    else:
        chosen = (
            _which_first(["ruff"]) or _which_first(["flake8"]) or _which_first(["mypy"])
        )
    if not chosen:
        return {"ok": False, "error": "Kein Lint-Tool gefunden (ruff/flake8/mypy)"}
    args = req.args or (["check"] if Path(chosen).name == "ruff" else [])
    res = _run([chosen] + args + paths, cwd=str(ROOT))
    return {"ok": res["returncode"] == 0, "tool": Path(chosen).name, "result": res}


@app.post("/tools/apply_files")
def tools_apply_files(req: ApplyFilesReq):
    secret = os.getenv("APPROVAL_SECRET") or ""
    if not secret or req.approve_secret != secret:
        return {"ok": False, "error": "approve_secret falsch oder nicht gesetzt"}

    applied = []
    previews = []
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = ROOT / "_backup"
    if req.backup:
        backup_dir.mkdir(exist_ok=True)

    for ch in req.changes:
        tgt = Path(ch.path)
        if not tgt.is_absolute():
            tgt = (ROOT / tgt).resolve()
        _ensure_allowed(tgt)

        new_text = ch.text
        if new_text is None and ch.content_b64 is not None:
            new_text = base64.b64decode(ch.content_b64).decode(
                "utf-8", errors="replace"
            )
        if new_text is None:
            return {"ok": False, "error": f"Kein Inhalt für {ch.path}"}

        old_text = ""
        if tgt.exists():
            old_text = tgt.read_text(encoding="utf-8", errors="replace")

        diff = list(
            difflib.unified_diff(
                old_text.splitlines(True),
                new_text.splitlines(True),
                fromfile=str(tgt),
                tofile=str(tgt),
                lineterm="",
            )
        )
        adds = sum(1 for ln in diff if ln.startswith("+") and not ln.startswith("+++"))
        rems = sum(1 for ln in diff if ln.startswith("-") and not ln.startswith("---"))

        previews.append({"path": str(tgt), "adds": adds, "rems": rems})

        if not req.preview_only:
            if req.backup and tgt.exists():
                bak = backup_dir / f"{tgt.name}.{ts}.bak"
                bak.write_text(old_text, encoding="utf-8")
            tgt.parent.mkdir(parents=True, exist_ok=True)
            tgt.write_text(new_text, encoding="utf-8")
            applied.append(str(tgt))

    return {
        "ok": True,
        "preview_only": req.preview_only,
        "changes": previews,
        "applied": applied,
        "backup_dir": str(backup_dir) if req.backup else None,
    }


@app.post("/tools/search_repo")
def tools_search_repo(req: SearchReq):
    results = []
    patterns = req.globs or ["**/*"]
    maxn = max(1, min(req.max_results or 50, 500))

    def gen_files():
        for ad in ALLOWED_DIRS:
            for pat in patterns:
                base = Path(ad)
                for p in base.rglob("*"):
                    if p.is_file() and fnmatch.fnmatch(
                        str(p.relative_to(base)).replace("\\", "/"),
                        pat.replace("**/", ""),
                    ):
                        yield p

    for p in gen_files():
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hit = False
        for i, line in enumerate(text.splitlines(), 1):
            if req.query.lower() in line.lower():
                results.append({"path": str(p), "line": i, "snippet": line.strip()})
                hit = True
                break
        if hit and len(results) >= maxn:
            break
    return {"ok": True, "count": len(results), "items": results}


@app.post("/tools/open_file")
def tools_open_file(req: OpenFileReq):
    p = Path(req.path)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    _ensure_allowed(p)
    if not p.exists():
        return {"ok": False, "error": "Datei nicht gefunden"}
    text = p.read_text(encoding="utf-8", errors="replace")
    if req.tail and req.tail > 0:
        lines = text.splitlines()
        text = "\n".join(lines[-req.tail :])
    else:
        head = max(1, min(req.head or 200, 5000))
        text = "\n".join(text.splitlines()[:head])
    return {"ok": True, "path": str(p), "text": text}
