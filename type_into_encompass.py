"""
Read values.json and type the values into Encompass using Ctrl+G (Go to Field).

Workflow:
  1. Open the loan in the Encompass desktop client. Make sure the input form is visible.
  2. Run:  py type_into_encompass.py path/to/contract.values.json
  3. The script will count down 10 seconds — switch focus to Encompass and KEEP IT THERE.
  4. The script types each field with a pause of --delay seconds between fields so you can watch.

Safety:
  - Move your mouse to a screen corner to abort (pyautogui failsafe).
  - Use --dry-run first to see what would be typed without touching anything.
  - Use --delay 5 the first few runs to give yourself time to watch each field land.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import pyautogui

from field_map import FIELD_MAP

pyautogui.FAILSAFE = True   # mouse to corner aborts
pyautogui.PAUSE = 0.05      # tiny gap between actions

# Logical field name -> JSON key in values.json
# (most are 1:1; derived fields come from data["_derived"])
DERIVED_FIELDS = {"earnest_plus_dd_fee", "due_diligence_date"}

def value_for(data: dict, logical_name: str):
    if logical_name in DERIVED_FIELDS:
        derived = data.get("_derived") or {}
        # Fall back to top-level if extractor found a literal value
        return derived.get(logical_name) or data.get(logical_name)
    return data.get(logical_name)


def go_to_field(field_id: str):
    """Press Ctrl+G, type the field ID, press Enter."""
    pyautogui.hotkey("ctrl", "g")
    time.sleep(0.4)
    pyautogui.typewrite(field_id, interval=0.02)
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.4)


def type_value(value):
    text = str(value)
    pyautogui.typewrite(text, interval=0.02)
    pyautogui.press("tab")  # commit field
    time.sleep(0.2)


def run(values_path: Path, dry_run: bool, delay: float, countdown: int):
    data = json.loads(values_path.read_text())

    plan = []
    for logical, encompass_ids in FIELD_MAP.items():
        v = value_for(data, logical)
        if v in (None, "", []):
            continue
        for fid in encompass_ids:
            plan.append((logical, fid, v))

    if not plan:
        sys.exit("No fields to type — values.json had nothing to map.")

    print("Plan:")
    for logical, fid, v in plan:
        print(f"  {fid:25} <- {v!r}    ({logical})")
    print()

    if dry_run:
        print("Dry run — exiting without typing.")
        return

    print(f"Switch focus to Encompass NOW and keep it there. Typing starts in {countdown} seconds.")
    print("Move mouse to a screen corner to abort at any time.")
    for i in range(countdown, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    for logical, fid, v in plan:
        print(f"-> {fid} <- {v!r}")
        go_to_field(fid)
        type_value(v)
        time.sleep(delay)

    print("\nDone. Review every field in Encompass before saving the loan.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("values_json", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="Print plan, don't type")
    ap.add_argument("--delay", type=float, default=2.0,
                    help="Seconds to pause between fields (default 2.0). Use larger values to watch.")
    ap.add_argument("--countdown", type=int, default=10,
                    help="Initial countdown seconds before typing starts (default 10).")
    args = ap.parse_args()

    if not args.values_json.exists():
        sys.exit(f"Not found: {args.values_json}")

    run(args.values_json, args.dry_run, args.delay, args.countdown)


if __name__ == "__main__":
    main()
