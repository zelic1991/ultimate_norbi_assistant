"""
telemetry_logger.py – Basis für Telemetrie‑Aufzeichnungen

Dieses Modul stellt Hilfsfunktionen zur Verfügung, um Start‑/Endzeitpunkte und
Laufzeiten von Operationen (z. B. Codegen, Audit, Datenverarbeitung) zu
protokollieren. Die Logs können später in Dashboards oder Digests eingespielt werden.
"""
import datetime
import json
from pathlib import Path
from contextlib import contextmanager

LOG_FILE = Path("logs/progress.jsonl")


def log_event(event: str, status: str, details: dict | None = None) -> None:
    """Loggt ein Ereignis mit Zeitstempel, Status und optionalen Details."""
    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "event": event,
        "status": status,
        "details": details or {},
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@contextmanager
def timed_event(event_name: str, details: dict | None = None):
    """Context‑Manager, um die Laufzeit eines Ereignisses zu messen und zu loggen."""
    start = datetime.datetime.now()
    log_event(event_name, "start", details)
    try:
        yield
        log_event(event_name, "success", {"duration": (datetime.datetime.now() - start).total_seconds()})
    except Exception as e:
        log_event(event_name, "error", {"error": str(e), "duration": (datetime.datetime.now() - start).total_seconds()})
        raise
