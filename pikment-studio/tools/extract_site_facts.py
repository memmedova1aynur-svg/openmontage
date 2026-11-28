#!/usr/bin/env python3
"""Pull the facts we are allowed to quote out of https://pikment.az into brand/facts.json.

Everything an ad says about trainings, durations, numbers and the app must come from
this file (or the SMM guide), never from memory. Re-run before each production.
"""
import html, json, re, subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "brand" / "facts.json"
raw = subprocess.run(["curl", "-sSL", "-m", "40", "https://pikment.az/"], capture_output=True, text=True).stdout
s = re.sub(r"(?is)<(script|style|svg).*?</\1>", "", raw)
L = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", s)).split("\n") if l.strip()]

cats = {"Məktəbəqədər", "Oyun və terapiya", "İnklüziv", "Ana və uşaq", "Təhsil biznesi", "Şəxsi inkişaf"}
courses, k = [], 0
while k < len(L) - 3:
    if L[k] in cats and L[k + 2].startswith("Kimlər üçün"):
        c, j = {"category": L[k], "name": L[k + 1]}, k + 2
        while j < len(L) and L[j] != "Müraciət et":
            for key, lab in (("for", "Kimlər üçün:"), ("trainers", "Təlimçi:"), ("duration", "Müddət:"), ("format", "Format:")):
                if L[j] == lab:
                    c[key] = L[j + 1]
            j += 1
        courses.append(c)
        k = j
    k += 1

def after(label, n=1):
    i = L.index(label)
    return L[i + 1 : i + 1 + n]

app = {}
if "Gündəlik iş bir tətbiqdə" in L:
    i = L.index("Gündəlik iş bir tətbiqdə")
    app = {
        "title": "Gündəlik iş bir tətbiqdə",
        "features": [{"n": L[i + 1], "name": L[i + 2], "text": L[i + 3]}, {"n": L[i + 4], "name": L[i + 5], "text": L[i + 6]}, {"n": L[i + 7], "name": L[i + 8], "text": L[i + 9]}],
        "status": L[i + 10],
        "cta": L[i + 11],
        "phone_mock": {"title": L[i + 13], "topic": L[i + 14], "group": L[i + 15], "items": [[L[i + 16], L[i + 17]], [L[i + 18], L[i + 19]], [L[i + 20], L[i + 21]], [L[i + 22], L[i + 23]]]},
    }

facts = {
    "source": "https://pikment.az/",
    "contact": {"whatsapp": "+994 51 999 88 70", "wa_link": "https://wa.me/994519998870", "site": "pikment.az", "instagram": "pikment.az"},
    "team_numbers": {"years": 6, "participants": "4300+", "trainers": 20,
                      "note": "Rəqəmlər Pikment adı ilə keçirilən təlimlərə aiddir (noyabr 2026). Tətbiqin istifadəçi sayı deyil."},
    "stats_label": "200+ təlim xidməti" if "200+ təlim xidməti" in L else None,
    "courses": courses,
    "app": app,
    "app_sections": ["Bu gün", "Fəaliyyətlər", "Pik", "Akademiya", "Profil"],
    "app_status": "Pilot mərhələ. Google Play-də hələ yoxdur: yalnız 'tezliklə'.",
    "certificate": "Təlimi bitirənlərə Pikment sertifikatı verilir; dövlət nümunəli sənəd deyil.",
    "mentorship": "Mentorluğa başlamazdan əvvəl mentorla pulsuz konsultasiya, heç bir öhdəlik yoxdur.",
    "tagline": "Hər kəsin öz rəngi var",
}
OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
print("courses:", len(courses), "| app features:", len(app.get("features", [])), "| wrote", OUT)
