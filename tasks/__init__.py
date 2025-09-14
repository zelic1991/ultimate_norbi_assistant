"""
tasks/__init__.py – Exporte für Task‑Module.

Dieses Package bündelt die Kernfunktionen für den Pilot‑Agenten.
"""

from .data_lifecycle import (
    compress_raw_files,
    dedupe_current,
    validate_current_files,
)
from .intent_engine import IntentEngine

__all__ = [
    "compress_raw_files",
    "dedupe_current",
    "validate_current_files",
    "IntentEngine",
]