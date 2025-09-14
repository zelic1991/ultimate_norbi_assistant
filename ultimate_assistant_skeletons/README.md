# Ultimate Assistant Skeletons

Dieses Paket enthält Skelettdateien für noch nicht implementierte Komponenten deines Programmier-Assistenten.

## Struktur

- `scripts/critic.py` – Basismodul für die Critic‑Schleife, prüft Plan & Code auf offensichtliche Fehler.
- `templates/fastapi_app.py` – Minimaler FastAPI‑Server mit `/health`‑Route.
- `templates/react_component.tsx` – Einfache React-Komponente mit TypeScript.
- `scripts/audit_runner.py` – Rahmen zum Ausführen und Loggen von Audit‑Skripten.
- `scripts/telemetry_logger.py` – Hilfsfunktionen zum Protokollieren von Start/Ende, Laufzeiten und Status.
- `glossary.yaml` – Vorlage für dein Glossar (Begriffe, Abkürzungen, Definitionen).
- `tasks.json` – Beispiel für VS‑Code‑Tasks (Preview/Write für Codegen).
- `scripts/telegram_bot.py` – Beispiel eines Telegram‑Bots für Approval‑Flows.

## Nutzung
1. Passe Pfade und Umgebungsvariablen (`.env`) in den Skripten an deine Projektstruktur an.
2. Importiere `telemetry_logger.timed_event` oder `log_event` in deinen Hauptprogrammen, um Telemetrie zu sammeln.
3. Ergänze `critic.py` um weitere Prüfungen (Linting, Typprüfung, Richtlinien).
4. Ergänze `audit_runner.py` mit den Pfaden deiner Audit‑Skripte.
5. Lege dein persönliches Glossar in `glossary.yaml` an.
6. Richte `telegram_bot.py` ein (Bot‑Token in .env), damit du Aktionen per Chat freigeben oder ablehnen kannst.
7. Integriere `tasks.json` in `.vscode/` deines Projekts, um Codegen über VS Code zu steuern.

Diese Skeletons sind bewusst schlank gehalten und sollen dir als Ausgangspunkt dienen.
