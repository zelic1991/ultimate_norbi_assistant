"""
main.py – Einstiegspunkt zur Ausführung von Pilot‑Agent‑Tasks.

Dieses Skript bietet eine einfache Kommandozeilenoberfläche zur Ausführung
einzelner Datenhygiene‑Tasks oder zur Verwendung der Intent‑Engine. Es
nutz die Richtlinien aus der Konfiguration, um zu bestimmen, welche
Verzeichnisse zulässig sind und wie Dateien gehandhabt werden.

Laufzeit: Abhängig von der ausgewählten Aktion; in der Regel O(n) über die
Anzahl der Dateien im jeweiligen Ordner.
"""

import argparse
from pathlib import Path
import sys
from typing import Optional

from config import get_allowed_directories
from tasks import compress_raw_files, dedupe_current, validate_current_files, IntentEngine


def _get_directory(name: str) -> Path:
    """
    Gibt den Pfad zu einem der konfigurierten Arbeitsordner zurück.

    Args:
        name (str): Name des Ordners (RAW, CURRENT, ARCHIVE).

    Returns:
        Path: Absoluter Pfad zum Verzeichnis.
    """
    base = Path(__file__).resolve().parent
    return base / name


def run_compress() -> None:
    raw_dir = _get_directory("RAW")
    created = compress_raw_files(raw_dir)
    if created:
        print(f"Folgende Dateien wurden komprimiert:\n" + "\n".join(map(str, created)))
    else:
        print("Keine Dateien zum Komprimieren gefunden.")


def run_dedupe(dry_run: bool = True) -> None:
    current_dir = _get_directory("CURRENT")
    duplicates = dedupe_current(current_dir, dry_run=dry_run)
    if duplicates:
        if dry_run:
            print("Gefundene Duplikate (Original, Duplikat):")
            for original, dup in duplicates:
                print(f"{original} -> {dup}")
            print("Führe erneut mit --confirm aus, um Duplikate zu entfernen.")
        else:
            print(f"Es wurden {len(duplicates)} Duplikate entfernt.")
    else:
        print("Keine Duplikate gefunden.")


def run_validate() -> None:
    current_dir = _get_directory("CURRENT")
    results = validate_current_files(current_dir)
    if not results:
        print("Keine CSV‑Dateien gefunden.")
        return
    reference_cols: Optional[list] = None
    consistent = True
    for path, cols in results:
        if reference_cols is None:
            reference_cols = cols
        elif cols != reference_cols:
            consistent = False
            print(f"Warnung: {path} hat abweichende Spalten: {cols}")
    if consistent:
        print("Alle CSV‑Dateien haben dieselben Spalten. Struktur OK.")


def run_parse_intent(text: str) -> None:
    engine = IntentEngine()
    action, explanation = engine.parse_intent(text)
    print(explanation)
    print(f"Empfohlene Aktion: {action}")


def main(argv) -> int:
    parser = argparse.ArgumentParser(description="Pilot‑Agent Task Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compress
    compress_parser = subparsers.add_parser("compress", help="Komprimiert alte Dateien in RAW/")

    # dedupe
    dedupe_parser = subparsers.add_parser("dedupe", help="Identifiziert und entfernt Duplikate in CURRENT/")
    dedupe_parser.add_argument("--confirm", action="store_true", help="Duplikate wirklich löschen")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Prüft die Struktur von CSV‑Dateien in CURRENT/")

    # parse‑intent
    intent_parser = subparsers.add_parser("parse-intent", help="Analysiert Text und erkennt Absicht")
    intent_parser.add_argument("text", type=str, help="Der zu analysierende Text")

    args = parser.parse_args(argv)
    if args.command == "compress":
        run_compress()
    elif args.command == "dedupe":
        run_dedupe(dry_run=not args.confirm)
    elif args.command == "validate":
        run_validate()
    elif args.command == "parse-intent":
        run_parse_intent(args.text)
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))