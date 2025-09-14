import os, time, subprocess, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = Path(os.environ.get("VIRTUAL_ENV", ROOT)).joinpath("Scripts", "python.exe")
if not PY.exists():
    PY = Path(sys.executable)  # Fallback: aktueller Python

BASE_URL = os.environ.get("BOT_BASE_URL", "http://127.0.0.1:8000")
APPLY = ROOT / "apply_draft.py"
SMOKE_PS = ROOT / "scripts" / "run_smoke.ps1"
SPEC = os.environ.get(
    "SELF_WORK_SPEC", str(ROOT / "prompts" / "specs" / "hello_self.json")
)
TARGET = os.environ.get("SELF_WORK_TARGET", "generated_module.py")
INTERVAL = int(os.environ.get("SELF_WORK_INTERVAL", "60"))


def rest_generate(prompt: str) -> dict:
    import urllib.request, json

    req = urllib.request.Request(
        f"{BASE_URL}/generate",
        data=json.dumps({"prompt": prompt, "target": TARGET, "lang": "py"}).encode(
            "utf-8"
        ),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run(cmd: list[str]) -> int:
    print(">>", " ".join(str(x) for x in cmd), flush=True)
    return subprocess.call(cmd)


def main():
    spec_path = Path(SPEC)
    if not spec_path.exists():
        # Minimal-Default
        prompt = (
            "Bitte schreibe eine handler() Funktion, die 'hi from botfarm' zurückgibt."
        )
    else:
        prompt = spec_path.read_text(encoding="utf-8")

    while True:
        try:
            draft = rest_generate(prompt)
        except Exception as e:
            print(f"[ERR] generate failed: {e}")
            time.sleep(INTERVAL)
            continue

        draft_path = Path(draft.get("draft_path") or "")
        print(f"Draft: {draft_path}")
        if not draft_path.exists():
            print("[ERR] draft_path fehlt/ungültig")
            time.sleep(INTERVAL)
            continue

        # WHAT-IF
        rc = run([str(PY), str(APPLY), "--draft", str(draft_path), "--whatif"])
        if rc != 0:
            print("What-If failed")
            time.sleep(INTERVAL)
            continue

        critic = (draft.get("critic") or {}).get("level", "Green")
        if critic == "Red":
            print("[SKIP] Critic=Red")
            time.sleep(INTERVAL)
            continue

        if critic == "Yellow":
            # nur mit Secret erlauben (wenn gesetzt)
            sec = os.environ.get("APPROVAL_SECRET", "")
            if not sec:
                print("[WAIT] Yellow ohne Secret → übersprungen")
                time.sleep(INTERVAL)
                continue
            rc = run(
                [
                    str(PY),
                    str(APPLY),
                    "--draft",
                    str(draft_path),
                    "--approve",
                    "--approve-secret",
                    sec,
                ]
            )
        else:
            # Green: direkt schreiben
            rc = run([str(PY), str(APPLY), "--draft", str(draft_path), "--approve"])

        if rc != 0:
            print("Approve failed")
            time.sleep(INTERVAL)
            continue

        # Smoke
        if SMOKE_PS.exists():
            rc = run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(SMOKE_PS),
                ]
            )
            if rc != 0:
                print("SMOKE=FAIL")
            else:
                print("SMOKE=GREEN")
        else:
            print("[WARN] Smoke-Script fehlt")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
