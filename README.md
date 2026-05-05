# PDF → Encompass Automation (POC)

Reads a real estate purchase contract PDF, extracts key fields with Claude vision,
and types them into Encompass via `Ctrl+G` (Go to Field).

## One-time setup (work laptop)

1. Python is already installed (you're on Python 3.14).
2. Install dependencies:
   ```
   py -m pip install pypdf pdfplumber pdf2image anthropic pyautogui pillow
   ```
3. Install **poppler** (needed to convert PDF pages to images):
   - Download: https://github.com/oschwartz10612/poppler-windows/releases
   - Unzip to `C:\poppler` (or anywhere)
   - Add `C:\poppler\Library\bin` to your PATH, OR pass `poppler_path=` in `extract.py`
4. Get an Anthropic API key from https://console.anthropic.com/settings/keys
5. Set it as an environment variable (PowerShell):
   ```
   setx ANTHROPIC_API_KEY "sk-ant-..."
   ```
   Then close and reopen your terminal so it picks up.

## Daily use

```
# Step 1 — extract
py extract.py "Sales Contract [Ratified] - Abingdon.pdf"
# -> writes Sales Contract [Ratified] - Abingdon.values.json

# Step 2 — REVIEW the JSON. Open it, eyeball every value. Fix anything wrong.

# Step 3 — dry run to see what would be typed
py type_into_encompass.py "Sales Contract [Ratified] - Abingdon.values.json" --dry-run

# Step 4 — open the loan in Encompass, then run for real (with prompts):
py type_into_encompass.py "Sales Contract [Ratified] - Abingdon.values.json" --confirm

# Once you trust it, drop --confirm:
py type_into_encompass.py "Sales Contract [Ratified] - Abingdon.values.json"
```

## Field map

Edit `field_map.py` to add or change Encompass field IDs.
Find IDs in Encompass with right-click on a field, or `Ctrl+G` to go to a known one.

## Business rules currently implemented

- `earnest_money + due_diligence_fee → URLAROA0103` (summed if both exist).

## Safety

- `--dry-run` types nothing.
- `--confirm` prompts before every field.
- During typing, **move mouse to a screen corner to abort** (pyautogui failsafe).
- The Encompass window must have focus when typing starts. The script counts down 5 seconds.
