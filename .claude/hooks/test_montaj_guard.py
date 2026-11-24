#!/usr/bin/env python3
"""montaj_guard.py sınağı: python3 .claude/hooks/test_montaj_guard.py"""
import json
import subprocess
import sys
from pathlib import Path

G = Path(__file__).with_name("montaj_guard.py")
CASES = [  # (əmr, gözlənən çıxış kodu: 2 = bloklanır, 0 = icazə)
    ("ffmpeg -i x.mp4 -c copy instagram-clients/m/paketler/yekun/V05.mp4", 2),
    ("cp out.mp4 instagram-clients/m/fin/gonder/a.mp4", 2),
    ("mv out.mp4 m/final/a.mp4", 2),
    ("cd /tmp && python3 final.py 05 /x/paketler/yekun/S.mp4", 2),
    ("python3 x.py --out instagram-clients/m/yekun/a.mp4", 2),
    ("ffmpeg -i m/paketler/yekun/V05.mp4 -frames:v 1 /tmp/a.jpg", 0),
    ("ffprobe m/paketler/yekun/V05.mp4", 0),
    ("ls m/paketler/yekun/", 0),
    ("python3 measure.py paketler/yekun/V05.mp4 paketler/7_video/a.mp4", 0),
    ("python3 qc_render.py paketler/yekun/V05.mp4 --out QC", 0),
    ("python -m montaj.gate deliver m 05 --to paketler/yekun/S.mp4", 0),
]
bad = 0
for cmd, want in CASES:
    r = subprocess.run([sys.executable, str(G)], input=json.dumps({"tool_input": {"command": cmd}}), capture_output=True, text=True)
    ok = r.returncode == want
    bad += not ok
    print(("OK  " if ok else "XƏTA") + f" rc={r.returncode} gözlənən={want} :: {cmd}")
sys.exit(1 if bad else 0)
