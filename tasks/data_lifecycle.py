"""
data_lifecycle.py – Funktionen für Datenhygiene.

Dieses Modul implementiert grundlegende Aufgaben für den Lifecycle von Dateien:
Komprimieren von Rohdaten, Duplikaterkennung, Validierung und mehr. Die
Operationen werden so gestaltet, dass sie effizient sind und sich an den
Richtlinien aus `POLICIES/policy.yaml` orientieren.
"""

import os
import hashlib
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from config import should_compress_after_days, load_policy


def compress_raw_files(raw_dir: Path) -> List[Path]:
    """
    Komprimiert alle Dateien im angegebenen RAW‑Verzeichnis, die älter
    sind als `raw_days_before_compress` (siehe Konfiguration). Die
    Originaldateien werden nach erfolgreicher Kompression gelöscht.

    Laufzeit: O(n) – Es wird über alle Dateien iteriert.

    Args:
        raw_dir (Path): Pfad zum RAW‑Verzeichnis.

    Returns:
        List[Path]: Liste der erzeugten .gz‑Dateien.
    """
    created_files = []
    threshold_days = should_compress_after_days()
    threshold_date = datetime.now() - timedelta(days=threshold_days)

    for file_path in raw_dir.iterdir():
        if file_path.is_file() and not file_path.suffix == ".gz":
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < threshold_date:
                # Komprimiere die Datei
                compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
                with file_path.open("rb") as f_in:
                    with gzip.open(compressed_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                # Entferne Originaldatei
                file_path.unlink()
                created_files.append(compressed_path)
    return created_files


def _file_checksum(path: Path, algorithm: str = "sha256") -> str:
    """
    Berechnet die Prüfsumme einer Datei mit dem angegebenen Algorithmus.

    Args:
        path (Path): Pfad zur Datei.
        algorithm (str): Hash‑Algorithmus ("sha256" oder "md5").

    Returns:
        str: Hexadezimale Prüfsumme.
    """
    if algorithm not in {"sha256", "md5"}:
        raise ValueError("Unsupported hash algorithm")
    h = hashlib.sha256() if algorithm == "sha256" else hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):  # Lesen in 8KB‑Chunks
            h.update(chunk)
    return h.hexdigest()


def dedupe_current(current_dir: Path, dry_run: bool = True) -> List[Tuple[Path, Path]]:
    """
    Identifiziert doppelte Dateien im CURRENT‑Verzeichnis anhand ihrer Prüfsumme.
    Bei Duplikaten wird die später modifizierte Datei zum Löschen vorgeschlagen.

    Laufzeit: O(n) zum Scannen der Dateien und O(n log n) zum Sortieren.

    Args:
        current_dir (Path): Pfad zum CURRENT‑Verzeichnis.
        dry_run (bool): Wenn True, nur anzeigen welche Dateien gelöscht würden.

    Returns:
        List[Tuple[Path, Path]]: Liste von Duplikaten als (behaltene, zu löschende) Pfade.
    """
    checksums: Dict[str, Path] = {}
    duplicates: List[Tuple[Path, Path]] = []
    for file_path in sorted(current_dir.iterdir(), key=lambda p: p.stat().st_mtime):
        if file_path.is_file():
            chksum = _file_checksum(file_path)
            if chksum in checksums:
                # Existiert schon: wir behalten die frühere Datei
                duplicates.append((checksums[chksum], file_path))
            else:
                checksums[chksum] = file_path

    # Falls dry_run false ist, lösche die duplikate
    if not dry_run:
        for kept, to_delete in duplicates:
            to_delete.unlink()  # Unwiderrufliches Löschen
    return duplicates


def validate_current_files(current_dir: Path) -> List[Tuple[Path, List[str]]]:
    """
    Überprüft rudimentär, ob alle CSV‑Dateien im CURRENT‑Verzeichnis dieselbe
    Header‑Struktur haben. Gibt die Datei und die gefundenen Spalten zurück.

    Laufzeit: O(n) zum Lesen der ersten Zeile jeder Datei.

    Args:
        current_dir (Path): Pfad zum CURRENT‑Verzeichnis.

    Returns:
        List[Tuple[Path, List[str]]]: Liste mit Dateien und ihren Spalten.
    """
    results = []
    for file_path in current_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".csv":
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                header_line = f.readline().strip()
                columns = [col.strip() for col in header_line.split(",") if col]
            results.append((file_path, columns))
    return results