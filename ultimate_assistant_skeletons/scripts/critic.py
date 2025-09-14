"""
critic.py – Prüf- und Kritikmodule für den Codegen-Prozess.

Dieses Skript bietet eine einfache Critic-Schleife: Es nimmt den vom Agenten
erzeugten Plan und Code sowie die Spezifikation entgegen, prüft auf offensichtliche
Unstimmigkeiten und Risiken und gibt Hinweise zurück. Hier kann man Regeln
erweitern (z. B. PEP8‑Check, Typprüfung, Linting). Die Ausgabe sollte in das
Run-Log geschrieben werden.

Usage (als Modul importieren oder über CLI testen):
```
python critic.py --spec spec.md --plan plan.txt --code code.py
```
"""
import argparse
import json
import re
import sys


def load_text(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def simple_check(spec: str, plan: str, code: str) -> dict:
    """Führt einige einfache Plausibilitätsprüfungen durch."""
    issues = []
    # Prüfe, ob essentielle Begriffe aus der Spez im Plan erwähnt werden
    keywords = re.findall(r"\b[A-Za-z_]{4,}\b", spec)
    for kw in keywords:
        if kw in plan:
            continue
        # Schlüsselbegriffe, die nur einmal auftauchen müssen (z. B. 'fastapi', 'health')
        if kw.lower() in ('input', 'output', 'api'):
            continue
        if kw.lower() not in plan.lower():
            issues.append(f"Warnung: Spezifizierter Begriff '{kw}' erscheint nicht im Plan.")
    # Prüfung: Code enthält TODO
    if 'TODO' in code:
        issues.append("Hinweis: 'TODO' gefunden – entfern oder implementieren Sie TODO-Passagen.")
    return {
        'issues': issues,
        'ok': len(issues) == 0
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--code', required=True)
    args = ap.parse_args()

    spec = load_text(args.spec)
    plan = load_text(args.plan)
    code = load_text(args.code)

    result = simple_check(spec, plan, code)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
