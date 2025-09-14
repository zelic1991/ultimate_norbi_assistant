#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse, os
from pathlib import Path
from bot_ai import draft_from_spec

ROOT = Path(__file__).resolve().parent
PREVIEWS = ROOT / "PREVIEWS"

def main():
    ap = argparse.ArgumentParser(description="Draft (Preview) – erzeugt Code-Entwürfe ohne Apply.")
    ap.add_argument("--spec", "-s", required=True, help="Pfad zur Markdown/Spec")
    ap.add_argument("--lang", "-l", choices=["py","ts"], default="py")
    args = ap.parse_args()

    PREVIEWS.mkdir(parents=True, exist_ok=True)
    out_name, code = draft_from_spec(args.spec, args.lang)
    out_path = PREVIEWS / out_name
    out_path.write_text(code, encoding="utf-8")
    print(f"[DRAFT] geschrieben: {out_path}")

if __name__ == "__main__":
    main()
