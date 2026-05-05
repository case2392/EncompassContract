"""
Read values.json and type the values into Encompass using Ctrl+G (Go to Field).

Workflow:
  1. Open the loan in the Encompass desktop client. Make sure the input form is visible.
  2. Run:  py type_into_encompass.py path/to/contract.values.json
  3. The script will count down 5 seconds — switch focus to the Encompass window.
  4. For each field, you'll see what it's about to type and (in --confirm mode) it asks before typing.

Safety:
  - Move your mouse to a screen corner to abort (pyautogui failsafe).
  - Use --dry-run first to see what would be typed without touching anything.
  - Use --confirm to require Enter between fields the first few times you run it.
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
def value_for(data: dict, logical_name: str):
    if logical_name == "earnest_plus_dd_fee":
        return (data.get("_derived") or {}).get("earnest_plus_dd_fee")
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


def run(values_path: Path, dry_run: bool, confirm: bool):
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

    print("Switch focus to the Encompass window NOW. Typing starts in 5 seconds...")
    print("(Move mouse to a screen corner to abort.)")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    for logical, fid, v in plan:
        if confirm:
            input(f"\n[Enter] to type {v!r} into field {fid} ({logical}) — Ctrl+C to abort: ")
        else:
            print(f"-> {fid} <- {v!r}")
        go_to_field(fid)
        type_value(v)

    print("\nDone. Review fields in Encompass before saving the loan.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("values_json", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="Print plan, don't type")
    ap.add_argument("--confirm", action="store_true", help="Pause for Enter between fields")
    args = ap.parse_args()

    if not args.values_json.exists():
        sys.exit(f"Not found: {args.values_json}")

    run(args.values_json, args.dry_run, args.confirm)


if __name__ == "__main__":
    main()
