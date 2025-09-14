# botfarm_controller (Preview-first)

## Quickstart
- Terminal in diesem Ordner öffnen:
  - `python main.py plan`
  - `python main.py options`
  - `python main.py whatif`
  - `python main.py approve`

## Policy/Guardrails
- Keine Writes außerhalb `ALLOW_DIRS`
- Erst What-If, dann Approve (später: echte Apply-Phase)
