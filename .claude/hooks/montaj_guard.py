#!/usr/bin/env python3
"""PreToolUse(Bash) hook: təhvil qovluqlarına (yekun/, gonder/, final/) video yazmanı yalnız
`python -m montaj.gate deliver` ilə icazə verir. Oxumaq (ffprobe, ls, kadr çıxarmaq) bloklanmır."""
import json
import re
import shlex
import sys

DELIV = re.compile(r"(^|/)(yekun|gonder|final)/[^ ]*\.(mp4|mov|m4v)$", re.I)
WRITERS = {"ffmpeg", "cp", "mv", "rsync", "ln", "install", "tee"}


def targets(seg: list[str]) -> list[str]:
    if not seg:
        return []
    tool = seg[0].split("/")[-1]
    if tool not in WRITERS:
        # python skriptinə çıxış yolu kimi verilən təhvil faylı
        if tool.startswith("python") and "montaj.gate" not in seg:
            out = [seg[i + 1] for i, t in enumerate(seg[:-1]) if t in ("-o", "--out", "--output", "--to", "--dest")]
            script = next((t for t in seg[1:] if t.endswith(".py")), "")
            if re.search(r"final|render|engine|export", script.split("/")[-1], re.I):
                out.append(seg[-1])
            return out
        return []
    return [seg[-1]]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    cmd = (data.get("tool_input") or {}).get("command", "")
    if "montaj.gate" in cmd and "deliver" in cmd:
        return
    for part in re.split(r"&&|\|\||;|\||\n", cmd):
        try:
            seg = shlex.split(part)
        except ValueError:
            seg = part.split()
        seg = [s for s in seg if s not in ("sudo", "nohup", "setsid", "time")]
        for t in targets(seg):
            if DELIV.search(t.strip("'\"")):
                print("BLOKLANDI (AYRA montaj darvazası): təhvil qovluğuna birbaşa video yazmaq olmaz → "
                      f"{t}. Video iş qovluğunda render olunur və yalnız `python -m montaj.gate deliver <müştəri> <video_id> "
                      "--to <yol>` ilə (QC keçəndən sonra) təhvil verilir.", file=sys.stderr)
                sys.exit(2)


if __name__ == "__main__":
    main()
