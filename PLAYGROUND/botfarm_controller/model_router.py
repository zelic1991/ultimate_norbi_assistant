# model_router.py — Routing ohne GPT-4 Defaults
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, Mapping, List


@dataclass
class TaskSignal:
    files: int = 1  # betroffene Dateien
    loc: int = 50  # betroffene Zeilen
    cross_stack: bool = False  # z.B. API + Frontend + CI
    iterations_failed: int = 0  # fehlgeschlagene Test-Iterationen
    want_strategy: bool = False  # Begründungen/Strategie gewünscht
    inline_latency_ms: Optional[int] = None  # ultra-kurz im Editor?


class ModelRouter:
    """
    Entscheidet zwischen:
      - Brain:  GPT-5
      - Hand:   GPT-5-mini
      - Nano:   GPT-5-nano
    und mappt Labels auf echte Modell-IDs per ENV.
    """

    def __init__(self, env: Mapping[str, str]):
        # Menschliche Labels (UI/Logs)
        self.label_brain = (env.get("ROUTE_LABEL_BRAIN") or "gpt-5").strip()
        self.label_hand = (env.get("ROUTE_LABEL_HAND") or "gpt-5-mini").strip()
        self.label_nano = (env.get("ROUTE_LABEL_NANO") or "gpt-5-nano").strip()

        # Tatsächliche API-Modellnamen – KEINE GPT-4 Defaults
        self.model_brain = self._first(
            env, ["ROUTE_MODEL_BRAIN", "RESOLVE_GPT5"], default="gpt-5"
        )
        self.model_hand = self._first(
            env, ["ROUTE_MODEL_HAND", "RESOLVE_GPT5_MINI"], default="gpt-5-mini"
        )
        self.model_nano = self._first(
            env, ["ROUTE_MODEL_NANO", "RESOLVE_GPT5_NANO"], default="gpt-5-nano"
        )

    @staticmethod
    def _first(env: Mapping[str, str], keys: List[str], default: str) -> str:
        for k in keys:
            v = env.get(k)
            if v and v.strip():
                return v.strip()
        return default

    def decide(self, s: TaskSignal) -> Dict[str, Any]:
        reasons: List[str] = []
        label = self.label_hand
        model = self.model_hand

        # Escalation zur „Brain“
        if s.files >= 2 or s.loc >= 300:
            reasons.append(">=2 Dateien oder >=300 LoC")
            label, model = self.label_brain, self.model_brain
        if s.cross_stack:
            reasons.append("Cross-Stack-Thema")
            label, model = self.label_brain, self.model_brain
        if s.iterations_failed >= 2:
            reasons.append("Tests 2× fehlgeschlagen")
            label, model = self.label_brain, self.model_brain
        if s.want_strategy:
            reasons.append("Strategie/Begründung gefordert")
            label, model = self.label_brain, self.model_brain

        # Nano für ultra-kurz im Editor
        if not reasons and (
            s.inline_latency_ms is not None
            and s.inline_latency_ms < 150
            and s.loc <= 30
            and not s.cross_stack
            and s.files == 1
        ):
            reasons = ["Low-latency Inline Mini-Task"]
            label, model = self.label_nano, self.model_nano

        if not reasons:
            reasons = ["Standard: klarer Auftrag → Hand"]

        return {"label": label, "model": model, "reasons": reasons}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "labels": {
                "brain": self.label_brain,
                "hand": self.label_hand,
                "nano": self.label_nano,
            },
            "models": {
                "brain": self.model_brain,
                "hand": self.model_hand,
                "nano": self.model_nano,
            },
        }


__all__ = ["TaskSignal", "ModelRouter"]
