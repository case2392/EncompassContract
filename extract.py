"""
Extract structured contract data from a PDF using Claude vision.

Usage:
    py extract.py path/to/contract.pdf

Writes values.json next to the PDF. Review values.json before running type_into_encompass.py.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from pypdf import PdfReader, PdfWriter

MODEL = "claude-opus-4-7"

EXTRACTION_PROMPT = """You are reading a residential real estate purchase contract (e.g. South Carolina CCRA-01 or similar).
Extract the following fields. Return ONLY valid JSON, no prose, no markdown fences.

Fields to extract:
- seller_1_name: First seller name on the "Seller(s)" line in paragraph 1 (PARTIES). String or null.
- seller_2_name: Second seller, if any. Often separated by " & " or "and". String or null.
- seller_3_name: Third seller, if any. String or null.
- seller_4_name: Fourth seller, if any. String or null.
- closing_date: The closing date in paragraph 7. Format MM/DD/YYYY. String or null.
- due_diligence_date: The Due Diligence Period end date (paragraph 13 area). Format MM/DD/YYYY. String or null.
- listing_agent_name: Seller's / Listing Agent full name (typically near the signature/agent block at end). String or null.
- listing_agent_company: Listing Agent's brokerage / company name. String or null.
- listing_agent_email: Listing Agent email. String or null.
- listing_agent_phone: Listing Agent phone (keep formatting like 803-397-5021). String or null.
- transaction_costs: Dollar amount in paragraph 10b "Transaction Costs not to exceed $___". Number (no $ or commas) or null.
- earnest_money: Initial earnest money in paragraph 6 (e.g. 6a/6b). Number or null.
- due_diligence_fee: Due diligence fee, if separately listed. Number or null.

Rules:
- Names: copy exactly as written, including LLC/Inc, ampersands, etc. Do not split "Crystal Creative LLC" — that is one entity in seller_1_name.
- If two individuals are listed (e.g. "John Smith & Jane Smith"), put John Smith in seller_1_name and Jane Smith in seller_2_name.
- Dates: always MM/DD/YYYY with leading zeros (06/09/2026 not 6/9/2026).
- Money: numeric only, no currency symbols, no commas (1500 not "$1,500").
- If a field is blank or not present, return null. Do not guess.

Return JSON with exactly those keys."""


def pdf_to_images_b64(pdf_path: Path, scale: float = 2.0) -> list[str]:
    """Render each PDF page to PNG bytes (base64) for Claude vision.

    Uses pypdfium2 (no external binaries needed). scale=2.0 ~= 144 DPI.
    """
    import io
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    out = []
    for page in pdf:
        bitmap = page.render(scale=scale)
        img = bitmap.to_pil()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out.append(base64.standard_b64encode(buf.getvalue()).decode("ascii"))
    return out


def extract(pdf_path: Path) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY env var not set. See README.")

    client = Anthropic(api_key=api_key)
    pages_b64 = pdf_to_images_b64(pdf_path)

    content = [{"type": "text", "text": EXTRACTION_PROMPT}]
    for b64 in pages_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })

    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": content}],
    )

    raw = msg.content[0].text.strip()
    # Strip code fences if Claude added them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip("` \n")

    data = json.loads(raw)
    data["_derived"] = derive_fields(data)
    return data


def derive_fields(data: dict) -> dict:
    """Apply business rules: earnest money + due diligence fee → URLAROA0103."""
    em = data.get("earnest_money") or 0
    dd = data.get("due_diligence_fee") or 0
    total = em + dd
    return {"earnest_plus_dd_fee": total if total > 0 else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="Output JSON path (default: <pdf>.values.json)")
    args = ap.parse_args()

    if not args.pdf.exists():
        sys.exit(f"Not found: {args.pdf}")

    out_path = args.output or args.pdf.with_suffix(".values.json")
    print(f"Extracting from {args.pdf.name}...")
    data = extract(args.pdf)
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {out_path}")
    print()
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
