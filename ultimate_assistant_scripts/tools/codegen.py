# codegen.py — Preview-first Generator (Draft JSON + Preview file) v0.4
from __future__ import annotations

import os, sys, argparse, json, datetime, difflib
from pathlib import Path

# Optional imports (tolerant)
try:
    import orjson  # nicer logging
except Exception:
    orjson = None  # type: ignore
try:
    import yaml
except Exception:
    yaml = None  # type: ignore
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # type: ignore

# OpenAI (Responses API)
try:
    from openai import OpenAI as OpenAIClient
except Exception:
    OpenAIClient = None  # type: ignore


# ---------- Helpers ----------
def load_env():
    if load_dotenv:
        try:
            load_dotenv(override=True)
        except Exception:
            pass


def now_ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(p: Path, default: str = "") -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return default


def dump_json(obj: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return text


def count_changes(old: str, new: str) -> tuple[int, int]:
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


def to_rel(p: Path, project_root: Path) -> str:
    try:
        return str(p.resolve().relative_to(project_root.resolve())).replace("\\", "/")
    except Exception:
        return p.name.replace("\\", "/")


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key or OpenAIClient is None:
        return None
    try:
        return OpenAIClient(api_key=api_key, base_url=base_url)
    except Exception:
        return None


def ojson_dump(entry: dict) -> str:
    if orjson:
        try:
            return orjson.dumps(entry).decode("utf-8")
        except Exception:
            pass
    return json.dumps(entry, ensure_ascii=False)


# ---------- Core generation ----------
def generate_code_with_openai(
    client,
    model: str,
    system: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1400,
) -> tuple[str, dict]:
    """
    Returns (code_text, usage_dict). Falls back to "", {} on any error.
    """
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        # Best-effort extract
        text = getattr(resp, "output_text", None)
        if not text:
            try:
                text = "".join(
                    c.text
                    for o in getattr(resp, "output", [])
                    for c in getattr(o, "content", [])
                    if getattr(c, "type", "") == "text"
                )
            except Exception:
                text = ""
        usage = {}
        try:
            u = getattr(resp, "usage", None)
            if u:
                usage = dict(u)
        except Exception:
            pass
        return text or "", usage
    except Exception:
        return "", {}


def ask_rationale(client, model: str, spec_text: str) -> str:
    if not client:
        return "fallback: no OpenAI"
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": "Gib eine sehr kurze Begründung (1 Satz) für den Entwurf.",
                },
                {"role": "user", "content": spec_text},
            ],
            temperature=0.0,
            max_output_tokens=120,
        )
        txt = getattr(resp, "output_text", "") or ""
        return txt.strip() or "n/a"
    except Exception:
        return "n/a"


# ---------- Main ----------
def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="Preview-first Codegen → schreibt PREVIEW + Draft JSON (kein Write ins Ziel)."
    )
    parser.add_argument("--spec", required=True, help="Pfad zur Spezifikation (txt/md)")
    parser.add_argument(
        "--target",
        required=True,
        help="Zieldatei relativ zum Projekt (z.B. generated_module.py)",
    )
    parser.add_argument("--project", default=".", help="Projekt-Root (default=.)")
    parser.add_argument(
        "--lang",
        default="py",
        choices=["py", "ts", "txt"],
        help="Zielsprache (Dateiendung)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("DEFAULT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5-mini",
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1400)
    args = parser.parse_args()

    proj = Path(args.project).resolve()
    proj.mkdir(parents=True, exist_ok=True)
    previews = proj / "PREVIEWS"
    drafts = proj / "OPS" / "drafts"
    logs_dir = proj / "OPS" / "logs"
    previews.mkdir(exist_ok=True, parents=True)
    drafts.mkdir(exist_ok=True, parents=True)
    logs_dir.mkdir(exist_ok=True, parents=True)

    # Load optional policy/system prompt if present (keep tolerant)
    # These defaults are minimal and won't block if files are missing.
    prompts_dir = proj / "prompts"
    pol_file = proj / "OPS" / "self_edit.policy.json"  # optional (not required here)
    system_codegen = read_text(
        prompts_dir / "system_codegen.md",
        "Du erzeugst NUR finalen Code für eine Preview-Datei. Keine Erklärungen.",
    )
    spec_text = read_text(Path(args.spec))

    # Resolve target & extension
    ext = ".py" if args.lang == "py" else ".ts" if args.lang == "ts" else ".txt"
    target_rel = Path(args.target)
    # normalize: force relative
    if target_rel.is_absolute():
        try:
            target_rel = Path(to_rel(target_rel, proj))
        except Exception:
            target_rel = Path(target_rel.name)
    target_abs = (proj / target_rel).resolve()

    # Old text for delta
    old_text = read_text(target_abs)

    # OpenAI (tolerant)
    client = get_openai_client()
    model = args.model.strip()

    # Build user prompt for codegen
    user_prompt = (
        f"Erzeuge die Zieldatei {target_rel.as_posix()}.\n"
        f"Sprache: {args.lang}\n"
        f"Regeln: Nur Code, keine Kommentare/Erklärungen. Keine I/O, keine destruktiven Aktionen.\n\n"
        f"Spezifikation:\n{spec_text}"
    )

    code_text, usage = generate_code_with_openai(
        client,
        model=model,
        system=system_codegen,
        user_prompt=user_prompt,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    # Fallback stub
    if not code_text.strip():
        ts_h = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if args.lang == "ts":
            code_text = f"""// Generated STUB ({ts_h})
/*
{spec_text}
*/
export function handler() {{
  return "OK";
}}
"""
        elif args.lang == "py":
            code_text = f"""# Generated STUB ({ts_h})
\"\"\"SPEC:
{spec_text}
\"\"\"
def handler():
    return "OK"
"""
        else:
            code_text = f"// Generated STUB ({ts_h})\n{spec_text}\n"
        rationale = "fallback: no OpenAI"
        tokens = "n/a"
    else:
        rationale = ask_rationale(client, model, spec_text)
        tokens = usage.get("output_tokens") if isinstance(usage, dict) else None
        if tokens is None:
            tokens = usage.get("total_tokens") if isinstance(usage, dict) else "n/a"

    # Write PREVIEW file
    ts = now_ts()
    prev_name = f"gen_{ts}{ext}"
    preview_path = (previews / prev_name).resolve()
    preview_path.write_text(code_text, encoding="utf-8")

    # Compute delta
    adds, rems = count_changes(old_text, code_text)

    # Build Draft JSON (structured, Preview-first)
    draft_obj = {
        "status": "PREVIEW_ONLY",
        "ts": ts,
        "model": model,
        "tokens": tokens if tokens is not None else "n/a",
        "target": to_rel(target_abs, proj),  # relative!
        "preview_path": str(preview_path),  # informational; may be absolute
        "adds": adds,
        "rems": rems,
        "rationale": rationale,
        "risk_note": "n/a",
        "patch": [{"path": to_rel(target_abs, proj), "text": code_text}],  # relative!
    }

    draft_path = drafts / f"draft_{ts}.json"
    draft_obj["draft_path"] = str(draft_path.resolve())
    dump_json(draft_obj, draft_path)

    # Log line
    log_line = {
        "event": "codegen",
        "status": "PREVIEW_ONLY",
        "ts": ts,
        "model": model,
        "spec": Path(args.spec).name,
        "target": draft_obj["target"],
        "adds": adds,
        "rems": rems,
        "tokens": tokens if tokens is not None else "n/a",
        "draft": str(draft_path),
        "preview": str(preview_path),
    }
    (logs_dir / "codegen_runs.log").open("a", encoding="utf-8").write(
        f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {ojson_dump(log_line)}\n"
    )

    # Console summary (compact)
    print(f"Draft:   {draft_path}")
    print(f"Preview: {preview_path}")
    print(f"Target:  {draft_obj['target']}")
    print(f"Delta:   +{adds} / -{rems}")
    print("Status:  PREVIEW_ONLY")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        # Best-effort error log (to cwd if project resolution failed)
        try:
            msg = (
                f"[{datetime.datetime.now().isoformat(timespec='seconds')}] "
                f'{{"event":"error","type":"%s","msg":"%s"}}\n'
                % (type(e).__name__, str(e).replace('"', '\\"'))
            )
            sys.stderr.write(msg)
        finally:
            raise
