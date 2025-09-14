# scripts/self_work.py  —  v0.2 (robust subprocess, no os.system)
import os, sys, json, time, subprocess
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("BOTFARM_BASE", "http://127.0.0.1:8000")

OPS = ROOT / "OPS"
DRAFTS = OPS / "drafts"
FLAGS = OPS / "flags"
PREVIEWS = ROOT / "PREVIEWS"
SPECS_Q = ROOT / "prompts" / "specs" / "queue"
SPECS_DONE = ROOT / "prompts" / "specs" / "done"

for d in (DRAFTS, FLAGS, PREVIEWS, SPECS_Q, SPECS_DONE):
    d.mkdir(parents=True, exist_ok=True)


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def find_next_spec() -> Path | None:
    exts = (".json", ".md", ".txt")
    specs = sorted(
        [p for p in SPECS_Q.glob("*") if p.suffix.lower() in exts],
        key=lambda p: p.stat().st_mtime,
    )
    return specs[0] if specs else None


def read_spec(p: Path) -> tuple[str, str, str, str | None]:
    if p.suffix.lower() == ".json":
        j = json.loads(p.read_text(encoding="utf-8"))
        prompt = j.get("prompt") or j.get("spec") or ""
        target = j.get("target") or "generated_module.py"
        lang = j.get("lang") or "py"
        model = j.get("model")
        return prompt, target, lang, model
    else:
        return p.read_text(encoding="utf-8"), "generated_module.py", "py", None


def build_draft(prev: dict, code: str, model: str | None, target: str) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    draft = {
        "status": "PREVIEW_ONLY",
        "ts": ts,
        "model": model or prev.get("model") or "n/a",
        "target": str((ROOT / target).resolve()),
        "preview_path": prev.get("preview_path"),
        "adds": prev.get("adds", 0),
        "rems": prev.get("rems", 0),
        "rationale": "self_work",
        "risk_note": "n/a",
        "patch": [{"path": str((ROOT / target).resolve()), "text": code}],
    }
    out = DRAFTS / f"draft_{ts}.json"
    draft["draft_path"] = str(out)
    out.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def run_py(args: list[str]) -> int:
    # Robust: kein Shell-Parsing, explizite Argumentliste
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    print(">>", " ".join(f'"{a}"' if " " in a else a for a in args))
    res = subprocess.run(args, cwd=str(ROOT), env=env)
    return res.returncode


def main() -> int:
    # Freeze?
    if (FLAGS / "freeze.txt").exists():
        print("FREEZE flag present -> exit")
        return 0

    spec_path = find_next_spec()
    if not spec_path:
        print("No specs in queue.")
        return 0

    prompt, target, lang, model = read_spec(spec_path)
    print(f"Spec: {spec_path.name} → target={target}")

    # 1) generate preview
    try:
        payload = {"prompt": prompt, "target": target, "lang": lang}
        if model:
            payload["model"] = model
        prev = post_json(f"{BASE}/generate", payload)
    except error.HTTPError as e:
        print("ERROR /generate:", e.read().decode("utf-8", "ignore"))
        return 10
    except Exception as e:
        print("ERROR /generate:", e)
        return 11

    prev_path = Path(prev["preview_path"])
    code = prev_path.read_text(encoding="utf-8")

    # 2) build draft json
    draft_path = build_draft(prev, code, model, target)
    print(f"Draft: {draft_path}")

    # 3) what-if + approve via apply_draft.py
    py = sys.executable
    apply = str(ROOT / "apply_draft.py")

    rc = run_py([py, apply, "--draft", str(draft_path), "--whatif"])
    if rc != 0:
        print("What-If failed")
        return 2

    rc = run_py([py, apply, "--draft", str(draft_path), "--approve"])
    if rc != 0:
        print("Approve failed")
        return 3

    # 4) optional smoke tests
    smoke_ps1 = ROOT / "scripts" / "run_smoke.ps1"
    if smoke_ps1.exists():
        print(">> powershell run_smoke.ps1")
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(smoke_ps1),
            ],
            cwd=str(ROOT),
        )

    # 5) move spec → done
    try:
        spec_path.rename(SPECS_DONE / spec_path.name)
    except Exception:
        # Falls Verschieben über Laufwerksgrenzen: copy+unlink
        (SPECS_DONE / spec_path.name).write_text(
            spec_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec_path.unlink(missing_ok=True)

    print("OK self-work step done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
