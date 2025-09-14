import json
import sys
import difflib

try:
    import yaml
except Exception:
    print("[HINT] PyYAML fehlt? pip install pyyaml", file=sys.stderr)
    raise

json_path, yaml_path, apply_flag, source = sys.argv[1:5]
with open(json_path, "r", encoding="utf-8") as f:
    j = json.load(f)
with open(yaml_path, "r", encoding="utf-8") as f:
    y = yaml.safe_load(f) or {}

keys = ("mode", "allow_dirs", "guardrails", "style", "approvals", "scoring_weights")


def subset(d):
    return {k: d.get(k) for k in keys}


sj = json.dumps(subset(j), ensure_ascii=False, indent=2, sort_keys=True)
sy = json.dumps(subset(y), ensure_ascii=False, indent=2, sort_keys=True)

print("=== POLICY CHECK ===")
print("JSON :", json_path)
print("YAML :", yaml_path)

equal = sj == sy
print("Deckungsgleich:", "JA" if equal else "NEIN")

if not equal:
    print("\n--- Diff (YAML → JSON) ---")
    diff = difflib.unified_diff(
        sy.splitlines(), sj.splitlines(), fromfile="YAML", tofile="JSON", lineterm=""
    )
    for line in diff:
        print(line)

if str(apply_flag).lower() in ("1", "true", "yes"):
    if str(source).lower() == "yaml":
        for k in keys:
            j[k] = y.get(k, j.get(k))
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=2)
        print("\n[APPLY] YAML -> JSON synchronisiert.")
    else:
        for k in keys:
            y[k] = j.get(k, y.get(k))
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(y, f, allow_unicode=True, sort_keys=False)
        print("\n[APPLY] JSON -> YAML synchronisiert.")
else:
    if not equal:
        print("\n[WHAT-IF] Unterschiede vorhanden. Mit -Apply anwenden.")
