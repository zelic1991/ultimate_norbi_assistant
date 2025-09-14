# codegen.py — strukturierte Draft-Erzeugung + Run-Log (OPS/logs/codegen_runs.log)
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import os, json, difflib, shutil
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent
PREVIEWS = ROOT / "PREVIEWS"
LOGS = ROOT / "OPS" / "logs"
DRAFTS = ROOT / "OPS" / "drafts"
for d in (PREVIEWS, LOGS, DRAFTS):
    d.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS / "codegen_runs.log"

# --- OpenAI (optional, fällt robust auf Stub zurück) ---
try:
    from openai import OpenAI as OpenAIClient
except Exception:
    OpenAIClient = None  # type: ignore[assignment]


def _get_openai_client() -> Any | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key or OpenAIClient is None:
        return None
    return OpenAIClient(
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), api_key=key
    )


def _count_changes(old: str, new: str) -> tuple[int, int]:
    sm = difflib.SequenceMatcher(a=old.splitlines(), b=new.splitlines())
    adds = sum(
        j2 - j1
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag in ("insert", "replace")
    )
    rems = sum(
        i2 - i1
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag in ("delete", "replace")
    )
    return adds, rems


def _stub_code(prompt: str, lang: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if lang == "ts":
        return f"""// Generated STUB ({ts})
export function handler() {{
  return "OK";
}}
"""
    return f"""# Generated STUB ({ts})
\"\"\"SPEC:
{prompt}
\"\"\"
def handler():
    return "OK"
"""


def _model_code(prompt: str, lang: str, model: str) -> tuple[str, str, str]:
    """
    Versucht strukturiertes JSON vom Modell zu holen:
    { "code": "<string>", "rationale": "<string>", "risk_note": "<string>" }
    Fällt bei Fehlern auf Stub zurück.
    """
    client = _get_openai_client()
    if client is None:
        return _stub_code(prompt, lang), "fallback: no OpenAI", "n/a"

    system = (
        "Du bist ein strikter Code-Generator. Antworte NUR mit JSON:\n"
        '{ "code": string, "rationale": string, "risk_note": string }\n'
        "Kein Markdown, keine Erklärtexte, nur dieses JSON."
    )
    user = f"Sprache={lang}\nZiel: handler() muss direkt aufrufbar sein.\nAufgabe:\n{prompt}"

    try:
        resp = client.responses.create(
            model=model,
            temperature=0.2,
            max_output_tokens=1200,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        raw = getattr(resp, "output_text", None)
        if raw is None:
            # Fallback-Extraktion
            raw = ""
            for out in getattr(resp, "output", []):
                for c in getattr(out, "content", []):
                    if getattr(c, "type", "") == "text":
                        raw += c.text
        data = json.loads(raw)
        code = str(data.get("code", "")).strip()
        rationale = str(data.get("rationale", "")).strip()
        risk = str(data.get("risk_note", "")).strip()
        if not code:
            raise ValueError("empty code")
        return code, rationale, risk
    except Exception:
        return _stub_code(prompt, lang), "fallback: parse/error", "n/a"


def _ensure_lang(lang: str | None) -> str:
    l = (lang or "py").lower()
    return "ts" if l in ("ts", "typescript") else "py"


def generate_draft(
    prompt: str,
    target: str = "generated_module.py",
    lang: str | None = "py",
    model: str | None = None,
) -> Dict[str, Any]:
    lang = _ensure_lang(lang)
    model_used = (
        model or os.getenv("DEFAULT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5-mini"
    ).strip()

    # Code erzeugen (Modell oder Stub)
    code, rationale, risk_note = _model_code(prompt, lang, model_used)

    target_path = (ROOT / target).resolve()
    old = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    adds, rems = _count_changes(old, code)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".ts" if lang == "ts" else ".py"
    preview_path = (PREVIEWS / f"gen_{ts}{ext}").resolve()
    preview_path.write_text(code, encoding="utf-8")

    draft = {
        "status": "PREVIEW_ONLY",
        "ts": ts,
        "model": model_used,
        "target": str(target_path),
        "preview_path": str(preview_path),
        "adds": adds,
        "rems": rems,
        "rationale": rationale,
        "risk_note": risk_note,
        "patch": [{"path": str(target_path), "text": code}],
    }

    # Run-Log (eine Zeile, robust)
    line = f"[{ts}] status={draft['status']} model={model_used} tokens=n/a target={target_path} adds={adds} rems={rems}"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

    # Draft auch als JSON ablegen (für Tasks / What-If)
    draft_path = DRAFTS / f"draft_{ts}.json"
    draft_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    draft["draft_path"] = str(draft_path)
    return draft
