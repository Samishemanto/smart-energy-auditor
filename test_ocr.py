"""Quick local OCR test — run: python test_ocr.py path/to/bill.jpg"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.ocr import extract_text
from backend.bill_parser import parse_bill

path = sys.argv[1] if len(sys.argv) > 1 else "Scan_20260514_022247.jpg"

print("=== RAW OCR TEXT ===")
text = extract_text(path)
print(repr(text[:2000]))
print("\n=== FIRST 2000 CHARS (readable) ===")
print(text[:2000])
print("\n=== PARSED RESULT ===")
import json
print(json.dumps(parse_bill(text), indent=2))
