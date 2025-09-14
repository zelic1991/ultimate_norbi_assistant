# Project: botfarm_controller
## Ziel
VS-Code gesteuerter Programmier-Assistant für Botfarm (OpenAI), der Plan→Explore→Compare→Simulate→Propose→Approve→Execute→Verify→Learn befolgt.

## Artefakte (MVP)
- README.md (Kurz-HowTo, Commands)
- main.py (CLI-Gerüst, Platzhalter für OpenAI-Calls)
- policy_lock.json (Guardrails: ALLOW_DIRS=repo & PLAYGROUND)
- .vscode/tasks.json (Run/Preview), .vscode/launch.json (Debug)

## Guardrails
- Kein Schreiben außerhalb ALLOW_DIRS
- Erst Preview/What-If, dann APPROVE
- Max. 1 Rückfrage

## KPIs
- Time-to-Scaffold ↓, Fehlerquote ≈ 0, klare Diffs

## Nächste Steps (automatisch im Scaffold dokumentieren)
- API-Keys via .env
- Commands: plan/options/whatif/approve
