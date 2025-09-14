"""
intent_engine.py – Rudimentäre Intent‑Erkennung.

Dieses Modul enthält eine einfache Klasse `IntentEngine`, die den Text einer
Benutzeranfrage analysiert und daraus eine interne Aufgabenbeschreibung ableitet.
Die Implementierung kann durch anspruchsvollere Sprachverarbeitung ersetzt werden.

Laufzeit: O(1) pro Anfrage, da nur keyword‑basierte Regeln angewendet werden.
"""

from typing import Tuple


class IntentEngine:
    """Einfache Intent‑Engine zur Umwandlung von Freitext in Befehle."""

    def __init__(self) -> None:
        # Definiere Schlüsselwörter und zugehörige Aktionen.
        self.rules = {
            "komprimieren": "compress",
            "compress": "compress",
            "cleanup": "dedupe",
            "dedupe": "dedupe",
            "duplikate": "dedupe",
            "prüfen": "validate",
            "validieren": "validate",
            "analyse": "validate",
        }

    def parse_intent(self, text: str) -> Tuple[str, str]:
        """
        Versucht, anhand von Schlüsselwörtern die Absicht der Anfrage zu erkennen.

        Args:
            text (str): Eingabetext des Benutzers.

        Returns:
            Tuple[str, str]: (action, explanation) – die erkannte Aktion und eine kurze Erklärung.
        """
        normalized = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        for keyword, action in self.rules.items():
            if keyword in normalized:
                explanation = f"Erkannte Aktion: {action} (basierend auf dem Schlüsselwort '{keyword}')."
                return action, explanation
        return "unknown", "Keine passende Aktion gefunden. Bitte präzisieren."