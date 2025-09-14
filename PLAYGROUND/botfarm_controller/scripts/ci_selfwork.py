#!/usr/bin/env python3
from __future__ import annotations
import os, json, difflib, datetime
from pathlib import Path


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


def render_stub(spec_text: str) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'''# Generated STUB ({ts})
"""SPEC:
{spec_text.strip()}
"""
def handler():
    return "OK"
'''


def try_openai_code(
    spec_text: str, lang="py", target="generated_module.py"
) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        system = (
            "Du bist ein Code-Generator für einen Preview-first Assistant. "
            "Gib ausschließlich den finalen Code aus (keine Erklärungen). "
            "Keine destruktiven Operationen. Für Python muss handler() existieren."
        )
        user = f"Ziel-Datei: {target}\nSprache: {lang}\n\nAufgabe:\n{spec_text}"
        resp = client.responses.create(
            model=os.getenv("DEFAULT_MODEL", "gpt-5-mini"),
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_output_tokens=1200,
        )
        return getattr(resp, "output_text", None) or ""
    except Exception:
        return None


def main():
    root = Path(__file__).resolve().parents[1]
    previews = root / "PREVIEWS"
    drafts = root / "OPS" / "drafts"
    previews.mkdir(exist_ok=True, parents=True)
    drafts.mkdir(exist_ok=True, parents=True)

    spec_path = Path(os.getenv("SPEC_PATH", "prompts/specs/hello_self.json"))
    if not spec_path.is_absolute():
        spec_path = (root / spec_path).resolve()
    spec_text = (
        spec_path.read_text(encoding="utf-8") if spec_path.exists() else "hello world"
    )

    target_rel = os.getenv("TARGET", "generated_module.py")
    target = (root / target_rel).resolve()
    old_text = target.read_text(encoding="utf-8") if target.exists() else ""

    code = try_openai_code(spec_text, lang="py", target=target_rel) or render_stub(
        spec_text
    )
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    preview = (previews / f"gen_{ts}.py").resolve()
    preview.write_text(code, encoding="utf-8")

    adds, rems = count_changes(old_text, code)

    # simple critic
    files = 1
    level = "Green"
    reasons: list[str] = []
    if adds + rems > 400:
        level, reasons = "Red", ["size"]
    elif adds + rems > 150:
        level, reasons = "Yellow", ["large"]

    draft = {
        "status": "PREVIEW_ONLY",
        "ts": ts,
        "model": os.getenv("DEFAULT_MODEL", "gpt-5-mini"),
        "target": str(target),
        "preview_path": str(preview),
        "adds": adds,
        "rems": rems,
        "tokens": "n/a",
        "rationale": "ci-selfwork",
        "risk_note": "n/a",
        "critic": {"level": level, "reasons": reasons},
        "patch": [{"path": str(target), "text": code}],
    }
    draft_path = (drafts / f"draft_{ts}.json").resolve()
    draft["draft_path"] = str(draft_path)
    draft_path.write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # CI outputs
    print(f"Draft:   {draft_path}")
    print(f"Preview: {preview}")
    print(f"Critic:  {level} (+{adds}/-{rems})")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            # Write outputs in the exact order and keys required by the workflow
            print(f"draft_path={str(draft_path)}", file=f)
            print(f"preview_path={str(preview)}", file=f)
            print(f"critic_level={level}", file=f)
            print(f"ts={ts}", file=f)
            print(f"adds={adds}", file=f)
            print(f"rems={rems}", file=f)


if __name__ == "__main__":
    main()
