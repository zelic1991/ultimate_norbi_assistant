"""
config.py – Lädt Richtlinien aus der YAML‑Datei in POLICIES.

Dieses Modul stellt Funktionen bereit, um Konfigurationsdaten aus
`POLICIES/policy.yaml` zu laden. Die Richtlinien sind zentraler
Bestandteil des Pilot‑Agenten und werden von den Tasks genutzt.

Laufzeit: O(1) zum Laden, da nur eine Datei geparst wird.
"""

import yaml
from pathlib import Path


def load_policy(path: Path = None) -> dict:
    """
    Lädt die YAML‑Konfigurationsdatei und gibt sie als Dictionary zurück.

    Args:
        path (Path): Pfad zur YAML‑Datei. Wenn None, wird der Standardpfad
            `POLICIES/policy.yaml` relativ zu diesem Modul verwendet.

    Returns:
        dict: Konfigurationsdaten.
    """
    if path is None:
        # Setze Standardpfad zum policy.yaml relativ zu diesem Modul.
        path = Path(__file__).parent / "POLICIES" / "policy.yaml"
    with path.open("r", encoding="utf-8") as f:
        policy_data = yaml.safe_load(f)
    return policy_data


def get_allowed_directories() -> list:
    """
    Gibt die Liste der zulässigen Verzeichnisse zurück.

    Returns:
        list: Verzeichnisnamen.
    """
    policy = load_policy()
    return policy.get("directories", {}).get("allow", [])


def should_compress_after_days() -> int:
    """
    Liefert die Anzahl der Tage, nach denen Dateien in RAW komprimiert werden sollen.

    Returns:
        int: Tage als Ganzzahl.
    """
    policy = load_policy()
    return policy.get("retention", {}).get("raw_days_before_compress", 1)


def get_notification_settings() -> dict:
    """
    Liefert die Benachrichtigungseinstellungen.

    Returns:
        dict: Einstellungen für Benachrichtigungen.
    """
    policy = load_policy()
    return policy.get("notification", {})


if __name__ == "__main__":  # pragma: no cover
    # Wenn das Modul direkt ausgeführt wird, gib die geladene Konfiguration aus.
    from pprint import pprint

    print("Geladene Richtlinien:")
    pprint(load_policy())