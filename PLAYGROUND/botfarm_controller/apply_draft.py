# apply_draft.py — v0.3 (Python-Ersatz für apply_draft.ps1)
from __future__ import annotations
import argparse, json, os, sys, shutil, fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parent
OPS = ROOT / "OPS"
LOGS = OPS / "logs"
REPORTS = OPS / "reports"
BACKUP = ROOT / "_backup"
for d in (LOGS, REPORTS, BACKUP):
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS / "codegen_runs.log"


def log_line(**kv: Any) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    parts = [f"{k}={kv[k]}" for k in sorted(kv.keys())]
    line = f"[{ts}] " + " ".join(parts)
    if LOG_FILE.exists():
        LOG_FILE.write_text(
            LOG_FILE.read_text(encoding="utf-8") + line + "\n", encoding="utf-8"
        )
    else:
        LOG_FILE.write_text(line + "\n", encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_under(child: Path, base: Path) -> bool:
    try:
        child.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def like_any(rel: str, globs: List[str]) -> bool:
    n = rel.replace("\\", "/").lower()
    for g in globs:
        pat = g.replace("\\", "/").lower().replace("**/", "*")
        if fnmatch.fnmatch(n, pat):
            return True
    return False


def count_adds_rems(old: str, new: str) -> tuple[int, int]:
    import difflib

    sm = difflib.SequenceMatcher(a=old.splitlines(), b=new.splitlines())
    adds = sum(
        j2 - j1
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag in ("insert", "replace")
    )
    rems = sum(
        i2 - i1
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag in ("delete", "replace")
    )
    return adds, rems


def resolve_policy() -> Dict[str, Any]:
    pol_path = OPS / "self_edit.policy.json"
    if pol_path.exists():
        try:
            return read_json(pol_path)
        except Exception:
            pass
    return {
        "allow_dirs": [str(ROOT)],
        "deny_globs": [
            "**/apply_preview.ps1",
            "**/policy*.json",
            "**/.git/**",
            "**/.secrets/**",
            "**/secrets/**",
        ],
        "limits": {"max_files": 7, "max_lines_changed": 400},
        "approval": {"red_blocks_write": True, "yellow_needs_approval": True},
    }


def critic_level(
    draft: Dict[str, Any], policy: Dict[str, Any]
) -> tuple[str, List[str]]:
    reasons: List[str] = []
    patch = draft.get("patch") or []
    files_count = len(patch)
    adds = int(draft.get("adds") or 0)
    rems = int(draft.get("rems") or 0)
    total = adds + rems
    if total > int(policy["limits"]["max_lines_changed"]) or files_count > int(
        policy["limits"]["max_files"]
    ):
        reasons.append("size")
        return "Red", reasons
    for ch in patch:
        p = Path(ch.get("path") or "")
        rel = str(p).replace("\\", "/")
        if like_any(rel, policy.get("deny_globs", [])):
            reasons.append(f"forbidden:{rel}")
            return "Red", reasons
    if total > 150:
        reasons.append("large")
        return "Yellow", reasons
    return "Green", reasons


def main():
    ap = argparse.ArgumentParser(description="Apply a draft JSON (preview-first).")
    ap.add_argument("--draft", required=True, help="Path to draft JSON")
    ap.add_argument("--whatif", action="store_true", help="Dry run only")
    ap.add_argument("--approve", action="store_true", help="Apply changes")
    ap.add_argument(
        "--force-yellow", action="store_true", help="Override yellow approval gate"
    )
    ap.add_argument(
        "--approve-secret",
        default=None,
        help="Secret for yellow approval (or env APPROVAL_SECRET)",
    )
    args = ap.parse_args()

    draft_path = Path(args.draft).resolve()
    if not draft_path.exists():
        print(f"Draft not found: {draft_path}", file=sys.stderr)
        sys.exit(2)

    draft = read_json(draft_path)
    patch = draft.get("patch") or []
    if not isinstance(patch, list) or not patch:
        print("Patch ist leer.", file=sys.stderr)
        sys.exit(2)

    adds = int(draft.get("adds") or 0)
    rems = int(draft.get("rems") or 0)
    model = draft.get("model") or "n/a"
    tokens = draft.get("tokens") or "n/a"
    target = draft.get("target") or (patch[0].get("path") if patch else "")
    preview = draft.get("preview_path") or "(n/a)"
    status0 = draft.get("status") or "PREVIEW_ONLY"

    policy = resolve_policy()
    allow_roots = [Path(p).resolve() for p in policy.get("allow_dirs", [str(ROOT)])]

    level, reasons = critic_level(draft, policy)

    print("--- WHAT-IF ---")
    print(f"Status   : {status0}")
    print(f"Target   : {Path(target).resolve() if target else '(n/a)'}")
    print(f"Preview  : {preview}")
    print(f"Changes  : +{adds} / -{rems}")
    print(f"Critic   : {level} ({', '.join(reasons) if reasons else '-'})")
    print("---")

    for ch in patch:
        tgt = Path(ch.get("path") or "")
        txt = ch.get("text")
        if not tgt or txt is None:
            continue
        out = tgt if tgt.is_absolute() else (ROOT / tgt)
        print(f"[WHAT-IF] {out}")
        old = ""
        if out.exists():
            try:
                old = out.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                old = ""
        a, r = count_adds_rems(old, txt)
        print(f"  adds={a} rems={r}")

    if args.whatif and not args.approve:
        log_line(
            status="PREVIEW_ONLY",
            model=model,
            tokens=tokens,
            target=str(Path(target).resolve()),
            adds=adds,
            rems=rems,
            critic=level,
        )
        print("[INFO] Dry run only.")
        return

    if args.approve:
        if level == "Red" and policy.get("approval", {}).get("red_blocks_write", True):
            log_line(
                status="BLOCKED_RED",
                model=model,
                target=str(Path(target).resolve()),
                adds=adds,
                rems=rems,
                critic=level,
            )
            print("[BLOCK] Critic=Red -> write blocked.", file=sys.stderr)
            sys.exit(3)

        if (
            level == "Yellow"
            and policy.get("approval", {}).get("yellow_needs_approval", True)
            and not args.force_yellow
        ):
            sec_env = os.getenv("APPROVAL_SECRET") or ""
            sec_in = (args.approve_secret or "").strip()
            if not sec_env and not sec_in:
                log_line(
                    status="DENIED_YELLOW",
                    model=model,
                    target=str(Path(target).resolve()),
                    adds=adds,
                    rems=rems,
                    critic=level,
                )
                print(
                    "[DENY] Yellow needs approval (set --approve-secret or env APPROVAL_SECRET, or --force-yellow).",
                    file=sys.stderr,
                )
                sys.exit(4)
            if sec_env and sec_in and sec_env != sec_in:
                log_line(
                    status="DENIED_YELLOW",
                    model=model,
                    target=str(Path(target).resolve()),
                    adds=adds,
                    rems=rems,
                    critic=level,
                )
                print(
                    "[DENY] Provided secret mismatches env APPROVAL_SECRET.",
                    file=sys.stderr,
                )
                sys.exit(4)

        for ch in patch:
            rel = ch.get("path")
            txt = ch.get("text")
            b64 = ch.get("content_b64")
            if not rel:
                print("Patch-Eintrag ohne 'path' ignoriert.", file=sys.stderr)
                continue
            if txt is None and b64 is None:
                print(
                    "Patch ohne 'text' oder 'content_b64' ignoriert.", file=sys.stderr
                )
                continue
            out = Path(rel)
            if not out.is_absolute():
                out = (ROOT / out).resolve()

            if not any(is_under(out, base) for base in allow_roots):
                print(f"Target außerhalb allow_dirs: {out}", file=sys.stderr)
                sys.exit(5)

            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                bak = BACKUP / f"{out.name}.{ts}.bak"
                shutil.copy2(out, bak)
                print(f"[Backup] {bak}")

            if txt is not None:
                out.write_text(txt, encoding="utf-8")
            else:
                import base64

                out.write_bytes(base64.b64decode(b64))
            print(f"[WRITE]  {out}")

        log_line(
            status="APPROVED",
            model=model,
            target=str(Path(target).resolve()),
            adds=adds,
            rems=rems,
            critic=level,
        )
        print("[OK] Applied.")
        return

    print("[INFO] Nothing done. Use --whatif or --approve.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)
