"""Claude-un kodla hazırladığı B-roll: expert-reels şablonunun animasiyalı səhnələri danışansız qısa video kimi.

* Səhnələr şablondakı ilə eynidir (templates/expert-reels/src, giriş faylı scene_clip.tsx) — kod təkrarlanmır.
* Rəng: müştərinin profilindəki theme (rəng ailəsi). Müəllif hüququ problemi yoxdur, pulsuz, açarsız.
* Nəticə keşlənir (səhnə + props + müddət + theme + şablon kodu).
* Kataloq `// props:` şərhlərindən avtomatik çıxarılır.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates" / "expert-reels"
SRC = TPL / "src"
NODE_MODULES = ROOT / "remotion-composer" / "node_modules"
DEFAULT_STYLE = {"captions": "stroke", "pills": "top-card", "backdrop": "dots", "pipShape": "circle", "pipCorner": "br"}
TSCONFIG = {"compilerOptions": {"target": "ES2020", "module": "ESNext", "moduleResolution": "bundler", "jsx": "react-jsx",
                                "strict": True, "esModuleInterop": True, "resolveJsonModule": True, "skipLibCheck": True},
            "include": ["src"]}


def _src_hash() -> str:
    h = hashlib.sha1()
    for p in sorted(SRC.rglob("*.tsx")) + sorted(SRC.rglob("*.ts")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def _top_keys(body: str) -> list[tuple[str, str]]:
    """Obyekt literalının yuxarı səviyyəli açarları və dəyərin ilk sözü."""
    out, depth, i = [], 0, 0
    while i < len(body):
        c = body[i]
        if c in "{([":
            depth += 1
        elif c in "})]":
            depth -= 1
        elif depth == 0:
            m = re.match(r"\s*([A-Za-z_]\w*|\"[\w-]+\")\s*:\s*\(?\s*([A-Za-z_]\w*)?(?:\(\s*([A-Z]\w*))?", body[i:])
            if m and (i == 0 or body[i - 1] in ",\n {"):
                # wrap(Compare) kimi sarğılarda əsl komponent içdəkidir
                out.append((m.group(1).strip('"'), m.group(3) or m.group(2) or ""))
                i += body[i:].index(":") + 1  # dəyəri mötərizə dərinliyi ilə vergülə qədər keç
                # dəyərin sonuna (yuxarı səviyyədəki vergülə) qədər keç
                d = 0
                while i < len(body):
                    ch = body[i]
                    if ch in "{([":
                        d += 1
                    elif ch in "})]":
                        d -= 1
                    elif ch == "," and d == 0:
                        break
                    i += 1
        i += 1
    return out


def catalog() -> dict[str, dict[str, Any]]:
    """{səhnə: {"group", "component", "props"}} — props şərhi komponentin üstündəki `// props:` sətrindən."""
    res: dict[str, dict[str, Any]] = {}
    files = {p: p.read_text(encoding="utf-8") for p in sorted(SRC.rglob("*.tsx")) if p.name != "scene_clip.tsx"}
    alltext = "\n".join(files.values())
    for p, s in files.items():
        for m in re.finditer(r"export const (\w+)\s*:\s*Record<string,", s):
            name = m.group(1)
            if name in ("ICONS", "LOOKS"):
                continue
            i = s.index("= {", m.end()) + 2
            depth, j = 0, i
            while True:
                depth += s[j] == "{"
                depth -= s[j] == "}"
                j += 1
                if depth == 0:
                    break
            for key, comp in _top_keys(s[i + 1:j - 1]):
                doc = ""
                cm = re.search(r"((?://[^\n]*\n)+)\s*(?:export\s+)?const " + re.escape(comp) + r"\b", alltext) if comp else None
                if cm:
                    lines = [ln.strip()[2:].strip() for ln in cm.group(1).strip().splitlines()]
                    doc = " ".join(ln for ln in lines if ln)[:400]
                props_used: list[str] = []
                dm = re.search(r"\n(?:export\s+)?const " + re.escape(comp) + r"\b", alltext) if comp else None
                if dm:  # komponentin gövdəsi: növbəti yuxarı səviyyəli tərifə qədər
                    rest = alltext[dm.end():]
                    nxt = re.search(r"\n(?:export\s+)?(?:const|function) [A-Z]\w*\b", rest)
                    body = rest[: nxt.start() if nxt else len(rest)]
                    props_used = sorted(set(re.findall(r"\bp\.(\w+)", body)))
                doc_props = re.search(r"props:\s*(.*)", doc)
                res[key] = {"group": name.lower(), "component": comp, "props": props_used,
                            "doc": (doc_props.group(1) if doc_props else doc)[:300]}
    res.setdefault("bg_number", {"group": "kid", "component": "BigNumber", "props": [], "doc": "böyük rəqəm"})
    return res


def _workspace(base: Path) -> Path:
    ws = base / "sceneclip_ws"
    stamp = ws / ".src_hash"
    h = _src_hash()
    if stamp.is_file() and stamp.read_text() == h and (ws / "node_modules").exists():
        return ws
    if not NODE_MODULES.is_dir():
        raise RuntimeError("remotion-composer/node_modules yoxdur — bash scripts/cloud-setup.sh")
    (ws / "public").mkdir(parents=True, exist_ok=True)
    if not (ws / "node_modules").exists():
        os.symlink(NODE_MODULES, ws / "node_modules")
    if (ws / "src").exists():
        shutil.rmtree(ws / "src")
    shutil.copytree(SRC, ws / "src")  # kopya: webpack simlinki real yola açır, edit.json şablona işarə etməsin
    if not (ws / "public" / "fonts").exists():
        os.symlink(TPL / "public" / "fonts", ws / "public" / "fonts")
    (ws / "tsconfig.json").write_text(json.dumps(TSCONFIG))
    stamp.write_text(h)
    return ws


def _browser() -> list[str]:
    for b in sorted(Path("/opt/pw-browsers").glob("chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell")):
        if os.access(b, os.X_OK):
            return [f"--browser-executable={b}"]
    return []


def render(kind: str, props: dict[str, Any], dur: float, theme: dict[str, Any], out_dir: Path,
           style: dict[str, Any] | None = None, still: bool = False) -> Path:
    """Səhnəni 1080x1920, 30 fps MP4 (və ya still=True: orta kadr PNG) kimi render edir; keşlənir."""
    cat = catalog()
    if kind not in cat:
        raise ValueError(f"Naməlum səhnə: {kind}. `session scenes` ilə siyahıya baxın.")
    st = {**DEFAULT_STYLE, **(style or {})}
    key = hashlib.sha1(json.dumps([kind, props, round(dur, 2), theme, st, _src_hash()], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:14]
    out_dir.mkdir(parents=True, exist_ok=True)
    alpha = bool(props.get("transparent")) and not still
    out = out_dir / f"scene_{kind}_{key}.{'png' if still else 'mov' if alpha else 'mp4'}"
    if out.is_file():
        return out
    ws = _workspace(out_dir.parent if out_dir.name == "scenes" else out_dir)
    edit = {"duration": dur, "theme": theme, "style": st, "pip": {"focus": [540, 700], "radius": 230, "scale": 0.36},
            "pages": [], "zoom": [{"t": 0, "s": 1, "k": "cut"}], "pills": [], "cutaways": [], "captionShift": []}
    (ws / "public" / "edit.json").write_text(json.dumps(edit, ensure_ascii=False))
    inp = json.dumps({"kind": kind, "props": props, "dur": dur}, ensure_ascii=False)
    tmp = out.with_suffix(".part" + out.suffix)
    if still:
        cmd = ["npx", "remotion", "still", "src/scene_clip.tsx", "SceneClip", str(tmp), f"--frame={int(dur * 30 * 0.6)}"]
    elif alpha:  # şəffaf fon: real videonun üstünə qoyulan obraz (ProRes 4444, alfa ilə)
        cmd = ["npx", "remotion", "render", "src/scene_clip.tsx", "SceneClip", str(tmp), "--codec=prores", "--prores-profile=4444",
               "--pixel-format=yuva444p10le", "--image-format=png", "--concurrency=4", "--muted"]
    else:
        cmd = ["npx", "remotion", "render", "src/scene_clip.tsx", "SceneClip", str(tmp), "--codec=h264", "--crf=16",
               "--jpeg-quality=95", "--concurrency=4", "--muted"]
    r = subprocess.run(cmd + [f"--props={inp}", *_browser(), "--log=error"], cwd=ws, capture_output=True, text=True)
    if r.returncode != 0 or not tmp.is_file():
        raise RuntimeError(f"Səhnə render olunmadı ({kind}): {(r.stderr or r.stdout)[-600:]}")
    tmp.replace(out)
    return out
