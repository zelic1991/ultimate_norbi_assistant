#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, pathlib, datetime, textwrap

def _nowstamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def _maybe_llm(spec_text:str, lang:str):
    # Optional: falls OPENAI_API_KEY gesetzt ist, versuchen wir kurz ein LLM; sonst None.
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return None
        from openai import OpenAI
        client = OpenAI()
        prompt = (
            f"Erzeuge einen KURZEN, lauffähigen {lang}-Skeleton für diesen Spec.\n"
            f"Nur Kernlogik, keine Deko, keine Erklärungen.\n\n=== SPEC ===\n{spec_text}\n"
        )
        resp = client.responses.create(model="gpt-4o-mini", input=prompt)
        return (getattr(resp, "output_text", None) or "").strip() or None
    except Exception:
        return None

def _heuristic_skeleton(spec_text:str, lang:str)->str:
    s = spec_text.lower()
    title = "generated_module"
    if lang == "py":
        if ("api" in s or "fastapi" in s):
            return f"""# Generated from spec
from fastapi import FastAPI

app = FastAPI(title="{title}")

@app.get("/health")
def health():
    return {{"ok": True}}
"""
        else:
            return """# Generated from spec
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--echo", default="ok")
    a = p.parse_args()
    print(a.echo)

if __name__ == "__main__":
    main()
"""
    elif lang == "ts":
        return """// Generated from spec
export function hello(name: string = "world") {
  console.log(`hello ${name}`);
}
"""
    else:
        return "# Generated from spec\n"

def draft_from_spec(spec_path:str, lang:str="py")->tuple[str,str]:
    p = pathlib.Path(spec_path)
    spec = p.read_text(encoding="utf-8", errors="ignore")
    # 1) Optional LLM
    code = _maybe_llm(spec, lang)
    # 2) Offline Fallback
    if not code:
        code = _heuristic_skeleton(spec, lang)
    # Ziel-Dateiname
    ts = _nowstamp()
    ext = ".py" if lang == "py" else ".ts"
    out_name = f"{p.stem}_{ts}{ext}"
    return (out_name, code)
