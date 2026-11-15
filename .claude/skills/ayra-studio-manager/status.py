#!/usr/bin/env python3
"""İstehsal növbəsinin statusu. İstifadə: status.py [müştəri]"""
import json, sys
from pathlib import Path
from collections import Counter
P = Path(__file__).resolve().parents[3] / "instagram-clients/_agency/istehsal.json"
if not P.exists():
    P.parent.mkdir(parents=True, exist_ok=True); P.write_text("[]"); print(f"{P} yaradıldı (boş)")
rows = json.loads(P.read_text())
if len(sys.argv) > 1: rows = [r for r in rows if r.get("musteri") == sys.argv[1]]
print(f"{'müştəri':18} {'video':26} {'mərhələ':12} {'təhvil':10} açıq düzəliş")
for r in rows:
    acq = sum(1 for d in r.get("duzelisler", []) if d.get("status") != "edildi")
    print(f"{r.get('musteri',''):18} {r.get('video',''):26} {r.get('merhele',''):12} {r.get('tehvil',''):10} {acq}")
print("cəm:", dict(Counter(r.get("merhele") for r in rows)))
