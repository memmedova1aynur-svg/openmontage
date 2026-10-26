#!/usr/bin/env python3
"""Map an approved, hand-corrected script onto the transcriber's word timings.

Usage:
    python templates/expert-reels/scripts/align_words.py <transcript.json> <corrected.txt> <out.json>

<transcript.json> is the transcriber tool output (has "word_timestamps").
<corrected.txt> is the approved text. Matching words keep their exact timing;
replaced/inserted words share the time span of what they replace. Prints
every replacement so the edit can be spot-checked.
"""
import difflib
import json
import re
import sys

tr = json.load(open(sys.argv[1], encoding="utf-8"))
words = tr["word_timestamps"]
corrected = open(sys.argv[2], encoding="utf-8").read().split()
raw = [w["word"].strip() for w in words]


def norm(t: str) -> str:
    return re.sub(r"[^\wəğıöüçş]", "", t.lower())


sm = difflib.SequenceMatcher(a=[norm(t) for t in raw], b=[norm(t) for t in corrected], autojunk=False)
out = []
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op == "equal":
        out += [{"word": corrected[j], "start": words[i]["start"], "end": words[i]["end"]} for i, j in zip(range(a1, a2), range(b1, b2))]
        continue
    if b2 > b1:
        if a2 > a1:
            s, e = words[a1]["start"], words[a2 - 1]["end"]
        else:
            s = words[a1 - 1]["end"] if a1 > 0 else 0
            e = words[a1]["start"] if a1 < len(words) else s + 0.3
            e = max(e, s + 0.25 * (b2 - b1))
        d = (e - s) / (b2 - b1)
        out += [{"word": corrected[j], "start": round(s + k * d, 3), "end": round(s + (k + 1) * d, 3)} for k, j in enumerate(range(b1, b2))]
    print(f"{op}: {raw[a1:a2]} -> {corrected[b1:b2]}")

for i in range(1, len(out)):
    out[i]["start"] = max(out[i]["start"], out[i - 1]["start"])
    if out[i]["end"] <= out[i]["start"]:
        out[i]["end"] = out[i]["start"] + 0.1

json.dump([{"id": 0, "start": out[0]["start"], "end": out[-1]["end"], "text": " ".join(w["word"] for w in out), "words": out}],
          open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(out)} words aligned -> {sys.argv[3]}")
