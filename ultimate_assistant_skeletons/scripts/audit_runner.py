"""
audit_runner.py – Skeleton zum Ausführen von Audit‑Skripten

Dieses Skript zeigt, wie Audit‑Skripte (z. B. Duplikat‑Finder oder Repo‑Analyse) programmatisch
aufgerufen werden können. Es sammelt Ergebnisse, loggt Start/Ende und speichert das Summary.

Erweitere die Liste `AUDITS` um weitere Skripte. Stelle sicher, dass jedes Skript
einen CLI‑Entrypoint besitzt oder als Python‑Modul importiert werden kann.
"""
import argparse
import datetime
import json
import subprocess
from pathlib import Path

# Liste der Audit‑Skripte, die ausgeführt werden sollen
AUDITS = [
    "scripts/duplicate_finder.py",
    "scripts/audit_repo.py",
]



def run_audit(script_path: str) -> dict:
    start = datetime.datetime.now()
    try:
        result = subprocess.run(["python", script_path], capture_output=True, text=True, check=False)
        output = result.stdout
        error  = result.stderr
        status = result.returncode
    except Exception as e:
        output = ""
        error  = str(e)
        status = -1
    end   = datetime.datetime.now()
    duration = (end - start).total_seconds()
    return {
        "script": script_path,
        "status": status,
        "duration": duration,
        "stdout": output[:1000],  # nur die ersten 1000 Zeichen sichern
        "stderr": error[:1000],
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="logs/audit_report.json", help="Pfad für das JSON‑Report")
    args = ap.parse_args()

    summary = []
    for script in AUDITS:
        if not Path(script).exists():
            summary.append({"script": script, "status": -1, "error": "not found"})
            continue
        summary.append(run_audit(script))

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Audit-Report geschrieben: {report_path}")


if __name__ == "__main__":
    main()
