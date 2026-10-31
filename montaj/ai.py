"""Panel daxilindəki AI bağlantısı (Claude API).

Bu, Claude Code sessiyasındakı Claude-dan AYRI bir bağlantıdır: serverdə
`ANTHROPIC_API_KEY` mühit dəyişəni olmalıdır (console.anthropic.com → API keys,
ödənişli istifadə). Açarın qiyməti heç vaxt göstərilmir və saxlanmır.

Model: claude-opus-5-5 ($4 / 1M giriş, $20 / 1M çıxış token).
Claude yalnız əvvəlcədən hesablanmış, söz sərhədinə düşən hissələrdən seçir —
vaxt kodu uydura bilmir.
"""

from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from montaj import diag
from montaj.errors import UserError

MODEL = os.environ.get("MONTAJ_AI_MODEL", "claude-opus-5-5")
PRICE_IN, PRICE_OUT = 4.0, 20.0  # USD / 1M token (claude-opus-5-5)


class CardPlan(BaseModel):
    segment_id: str = Field(description="Namizəd hissənin id-si (siyahıdan)")
    include: bool
    role: Literal["opening", "hook", "body", "proof", "cta", "closing"]
    on_screen_text: str = Field(description="Ekranda qısa mətn (Azərbaycan dilində) və ya boş")
    text_style: str = Field(description="Mətnin görünüşü: yer, ölçü, rəng (brenddən), boş ola bilər")
    graphics: str = Field(description="Qrafika/vurğu təklifi və ya boş")
    broll: str = Field(description="B-roll təklifi (yalnız materialda varsa) və ya boş")
    transition: str = Field(description="Keçid: kəsim, yumşaq keçid və s.")
    reason: str = Field(description="Qısa səbəb (Azərbaycan dilində)")


class StoryboardPlan(BaseModel):
    cards: list[CardPlan]
    music_mood: str
    music_note: str
    overall_note: str
    subtitles: bool


class CaptionPlan(BaseModel):
    caption: str
    hashtags: list[str]
    notes: str


def key_present() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _client():
    if not key_present():
        raise UserError("AI bağlantısı qurulmayıb.",
                        "Serverdə ANTHROPIC_API_KEY təyin edin (deploy/README.md). İndi qaydalara əsaslanan təklifdən istifadə edə bilərsiniz.")
    import anthropic

    return anthropic.Anthropic(max_retries=2, timeout=300)


def check_key() -> dict[str, Any]:
    """Açarın işlədiyini yoxlayır (qiymətini göstərmir)."""
    if not key_present():
        return {"ok": False, "reason": "Açar təyin edilməyib."}
    import anthropic

    try:
        info = _client().models.retrieve(MODEL)
        return {"ok": True, "model": info.id}
    except anthropic.AuthenticationError:
        return {"ok": False, "reason": "Açar etibarsızdır."}
    except anthropic.PermissionDeniedError:
        return {"ok": False, "reason": "Açarın bu modelə icazəsi yoxdur."}
    except anthropic.NotFoundError:
        return {"ok": False, "reason": f"Model tapılmadı: {MODEL}"}
    except anthropic.APIConnectionError:
        return {"ok": False, "reason": "api.anthropic.com-a qoşulmaq alınmadı."}
    except anthropic.APIStatusError as e:
        return {"ok": False, "reason": f"API xətası ({e.status_code})."}


def frame_jpeg(src: Path, t: float, width: int = 384) -> bytes:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.2f}", "-i", str(src), "-frames:v", "1",
         "-vf", f"scale={width}:-2", "-f", "image2", "-c:v", "mjpeg", "-q:v", "6", "-"],
        capture_output=True)
    return out.stdout


SYSTEM = (
    "Sən Azərbaycan dilində qısa sosial media videoları üçün peşəkar montajçısan. "
    "Sənə real kadrlar və transkriptlə namizəd hissələr verilir. Yalnız bu hissələrdən seç; "
    "vaxt kodu, fakt, ad, rəqəm və ya brend məlumatı uydurma. Məlum olmayan sahəni boş saxla. "
    "Dekorativ yüklənmə etmə: subtitr, qrafika, B-roll və keçidi yalnız materiala və seçilmiş üsluba uyğun olduqda təklif et. "
    "B-roll yalnız layihədə ayrıca material varsa təklif oluna bilər. "
    "Əl ilə qorunan hissələrə toxunma. Bütün mətnlər Azərbaycan dilində olsun."
)


def _describe(options: dict[str, Any], brand: dict[str, Any] | None) -> str:
    def g(k):
        v = options.get(k) or []
        return ", ".join(v) if v else "sistem təklif etsin"
    lines = [
        f"Format: {g('format')}", f"Məqsəd: {g('goal')}", f"Üslub: {g('style')}",
        f"Əlavələr: {g('extras')}",
        f"Müddət: {options.get('duration') or 'sistem təklif etsin'} san",
        f"Kəsim rejimi: {options.get('cutMode', 'suggest')}",
        f"Kadr formatı: {options.get('aspect', '9:16')}",
    ]
    if brand:
        lines.append(f"Müştəri: {brand.get('name') or 'birdəfəlik'}; sahə: {brand.get('field') or 'məlum deyil'}; "
                     f"rənglər: {', '.join(brand.get('colors') or []) or 'məlum deyil'}; "
                     f"montaj üstünlükləri: {brand.get('preferences') or 'məlum deyil'}")
    return "\n".join(lines)


def _call(content: list[dict[str, Any]], fmt, max_tokens: int = 16000):
    import anthropic

    client = _client()
    try:
        resp = client.beta.messages.parse(
            model=MODEL, max_tokens=max_tokens, system=SYSTEM,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            messages=[{"role": "user", "content": content}], output_format=fmt,
        )
    except anthropic.AuthenticationError as e:
        raise UserError("AI açarı etibarsızdır.", "Serverdəki ANTHROPIC_API_KEY-i yeniləyin.", detail=str(e)) from e
    except anthropic.RateLimitError as e:
        raise UserError("AI xidməti hazırda məşğuldur.", "Bir dəqiqə sonra yenidən cəhd edin.", detail=str(e)) from e
    except anthropic.APIConnectionError as e:
        raise UserError("AI xidmətinə qoşulmaq alınmadı.", "İnterneti yoxlayıb yenidən cəhd edin.", detail=str(e)) from e
    except anthropic.APIStatusError as e:
        raise UserError("AI xidməti xəta qaytardı.", "Yenidən cəhd edin.", detail=f"{e.status_code} {e.message}") from e
    if resp.stop_reason == "refusal":
        raise UserError("AI bu sorğunu emal etmədi.", "Seçimləri dəyişib yenidən cəhd edin.")
    u = resp.usage
    cost = (u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT) / 1e6
    diag.log("info", "AI çağırışı", model=resp.model, input_tokens=u.input_tokens,
             output_tokens=u.output_tokens, usd=f"{cost:.4f}")
    if resp.parsed_output is None:
        raise UserError("AI cavabı oxunmadı.", "Yenidən cəhd edin.")
    return resp.parsed_output, {"inputTokens": u.input_tokens, "outputTokens": u.output_tokens, "usd": round(cost, 4)}


def ai_storyboard(project_dir: Path, project: dict[str, Any], segs_by_media: dict[str, list[dict[str, Any]]],
                  options: dict[str, Any], brand: dict[str, Any] | None) -> dict[str, Any]:
    media = {m["id"]: m for m in project["media"]}
    content: list[dict[str, Any]] = [{"type": "text", "text": "Layihə seçimləri:\n" + _describe(options, brand)}]
    n_img = 0
    seg_index: dict[str, dict[str, Any]] = {}
    for mid, segs in segs_by_media.items():
        m = media[mid]
        content.append({"type": "text", "text": f"\nMənbə: {m['name']} ({'şəkil' if m.get('isImage') else 'video'})"})
        for s in segs:
            seg_index[s["id"]] = s
            if m.get("hasVideo") and n_img < 40:
                jpg = frame_jpeg(project_dir / m["file"], (s["srcIn"] + s["srcOut"]) / 2)
                if jpg:
                    content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                                "data": base64.standard_b64encode(jpg).decode()}})
                    n_img += 1
            content.append({"type": "text", "text": f"[{s['id']}] {s['srcIn']:.2f}–{s['srcOut']:.2f} san: "
                                                    f"{s['text'] or '(danışıq yoxdur)'}"})
    content.append({"type": "text", "text": (
        "Hər namizəd hissə üçün bir kart qaytar (sırası montaj ardıcıllığıdır; açılışı ən güclü hissədən seç). "
        "Müddət hədəfinə uyğun include=false ilə artıq hissələri söndür. Musiqi əhvalını təsvir et, konkret mahnı adı uydurma.")})
    plan, usage = _call(content, StoryboardPlan)
    cards = []
    for cp in plan.cards:
        s = seg_index.get(cp.segment_id)
        if not s:
            continue  # uydurulmuş id — atılır
        cards.append({"id": "card_" + cp.segment_id[4:], "segmentId": s["id"], "mediaId": s["mediaId"],
                      "srcIn": s["srcIn"], "srcOut": s["srcOut"], "include": cp.include, "role": cp.role,
                      "transcript": s["text"], "words": s["words"], "onScreenText": cp.on_screen_text,
                      "textStyle": cp.text_style, "graphics": cp.graphics, "broll": cp.broll,
                      "transition": cp.transition, "reason": cp.reason, "source": "ai"})
    if not cards:
        raise UserError("AI istifadə oluna bilən plan qaytarmadı.", "Yenidən cəhd edin.")
    return {"generator": "ai", "model": MODEL, "cards": cards, "musicMood": plan.music_mood,
            "musicNote": plan.music_note, "overallNote": plan.overall_note, "subtitles": plan.subtitles,
            "usage": usage}


def ai_revise_card(project_dir: Path, project: dict[str, Any], storyboard: dict[str, Any], card: dict[str, Any],
                   candidates: list[dict[str, Any]], instruction: str, alternative: bool,
                   options: dict[str, Any], brand: dict[str, Any] | None) -> dict[str, Any]:
    """Yalnız bir kartı dəyişir; digər kartlara toxunmur."""
    used = {c["segmentId"] for c in storyboard["cards"] if c["id"] != card["id"] and c.get("include")}
    pool = [s for s in candidates if s["id"] not in used or s["id"] == card["segmentId"]]
    media = {m["id"]: m for m in project["media"]}
    content: list[dict[str, Any]] = [{"type": "text", "text": "Layihə seçimləri:\n" + _describe(options, brand)},
                                     {"type": "text", "text": f"Dəyişdiriləcək kart: {card['segmentId']} rol={card['role']} "
                                                              f"mətn='{card.get('onScreenText', '')}' səbəb='{card.get('reason', '')}'"}]
    for s in pool[:20]:
        m = media[s["mediaId"]]
        if m.get("hasVideo"):
            jpg = frame_jpeg(project_dir / m["file"], (s["srcIn"] + s["srcOut"]) / 2)
            if jpg:
                content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                            "data": base64.standard_b64encode(jpg).decode()}})
        content.append({"type": "text", "text": f"[{s['id']}] {s['srcIn']:.2f}–{s['srcOut']:.2f}: {s['text'] or '(danışıq yoxdur)'}"})
    ask = ("Bu kart üçün FƏRQLİ bir variant təklif et (başqa hissə və ya başqa mətn/qrafika)." if alternative
           else f"İstifadəçinin istəyi: {instruction}")
    content.append({"type": "text", "text": ask + " Yalnız bir kart qaytar, cards siyahısında bir element."})
    plan, usage = _call(content, StoryboardPlan, max_tokens=8000)
    cp = next((c for c in plan.cards if any(s["id"] == c.segment_id for s in pool)), None)
    if cp is None:
        raise UserError("AI uyğun variant tapmadı.", "Başqa istək yazın və ya kartı əl ilə dəyişin.")
    s = next(s for s in pool if s["id"] == cp.segment_id)
    return {**card, "segmentId": s["id"], "mediaId": s["mediaId"], "srcIn": s["srcIn"], "srcOut": s["srcOut"],
            "transcript": s["text"], "words": s["words"], "include": cp.include, "role": cp.role,
            "onScreenText": cp.on_screen_text, "textStyle": cp.text_style, "graphics": cp.graphics,
            "broll": cp.broll, "transition": cp.transition, "reason": cp.reason, "source": "ai", "usage": usage}


def ai_caption(transcript: str, options: dict[str, Any], brand: dict[str, Any] | None,
               onscreen: list[str]) -> dict[str, Any]:
    content = [{"type": "text", "text": (
        "Montaj olunmuş videonun real transkripti və ekrandakı mətnlər əsasında Instagram caption-u yaz. "
        "Azərbaycan dilində. Uydurma fakt, rəqəm, vəd və ya 'viral olacaq' kimi alqoritmik uğur vədi olmasın. "
        "Müştərinin üslubuna uyğun ol. Hashtag-lar azsaylı və mövzuya uyğun olsun.\n\n"
        f"{_describe(options, brand)}\n\nTranskript:\n{transcript or '(danışıq yoxdur)'}\n\n"
        f"Ekrandakı mətnlər: {'; '.join(onscreen) or 'yoxdur'}")}]
    plan, usage = _call(content, CaptionPlan, max_tokens=8000)
    return {"caption": plan.caption, "hashtags": plan.hashtags, "notes": plan.notes, "usage": usage}


def estimate_note() -> str:
    return ("Storyboard təxminən 20–40 kadr şəkli + transkript (≈10–30 min token giriş, 2–6 min çıxış): "
            "claude-opus-5-5 ilə bir storyboard ≈ $0.05–0.25, bir kart dəyişikliyi ≈ $0.02–0.08, caption ≈ $0.01–0.03. "
            "Bu, ölçülmüş deyil, token qiymətinə görə təxmindir.")
