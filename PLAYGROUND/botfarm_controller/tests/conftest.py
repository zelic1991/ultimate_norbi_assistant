from pathlib import Path
import sys

# Resolve the project root. Prefer the workspace copy under the PLAYGROUND folder
# if it exists (developer workstation), otherwise keep the current layout.
candidate_workspace = (
    Path(__file__).resolve().parents[4] / "PLAYGROUND" / "botfarm_controller"
)
if candidate_workspace.exists():
    ROOT = candidate_workspace
else:
    ROOT = Path(__file__).resolve().parents[1]

    sys.path.insert(0, str(ROOT))
    print(f"[conftest] inserting ROOT into sys.path: {ROOT}")
