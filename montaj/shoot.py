"""Çəkiliş tövsiyəsi — müştəriyə çəkilişdən ƏVVƏL göndərilir (videoqrafiya: coverage, çəkilişdən əvvəl yoxlama, səs).

Yaxşı çəkilmiş material montajı asanlaşdırır və sistemin imkanlarını açır: 4K → virtual multikamera (3 plan ölçüsü),
60 fps → yavaşlatma, otağın sükutu → səs keçidləri, sabit fon → fonun dəyişdirilməsi, sıralı danışıq → karusel.
Mətn qısa və telefonda oxunaqlıdır; müştəri növü bilməsə də anlasın.
"""

from __future__ import annotations

from typing import Any

COMMON: list[tuple[str, list[str]]] = [
    ("Telefon və kadr", [
        "Lensi silin. Kamera: 4K, 30 fps (bütün videolarda eyni). Yavaşlatma istədiyiniz kadrlar — 60 fps.",
        "HDR / Dolby Vision-u söndürün (rəng və parlaqlıq dəyişməsin).",
        "Ekranda üzə basıb saxlayın — fokus və işıq kilidlənsin (AE/AF Lock).",
        "Telefonu ştativə qoyun, göz səviyyəsində. Kadrda baş üstündə bir az boşluq saxlayın, çox yaxından çəkməyin.",
    ]),
    ("İşıq", [
        "İşıq qarşıdan və ya yandan düşsün (pəncərə üzünüzə tərəf). Arxanızda pəncərə olmasın.",
        "Pəncərə işığı ilə sarı lampanı qarışdırmayın — biri olsun.",
    ]),
    ("Səs", [
        "Yaxa mikrofonu ən yaxşısıdır. Yoxdursa: telefon 50–80 sm məsafədə, sakit otaq; kondisioneri, ventilyatoru söndürün.",
        "Çəkilişin əvvəlində 10 saniyə susun — otağın sükutu yazılsın (montajda keçidlər üçün lazımdır).",
        "Hər cümlədən əvvəl və sonra 2 saniyə sakit durun. Səhv etsəniz, cümləni əvvəldən təkrarlayın.",
    ]),
    ("Hazırlıq", [
        "Batareya dolu, yaddaş boş olsun (4K: 1 dəqiqə ≈ 400 MB). Təyyarə rejimi — zəng çəkilişi kəsməsin.",
        "Fon səliqəli olsun; fondan 1–2 m aralı durun. Fonu sonra dəyişmək istəsəniz, fonla eyni rəngli geyim geyinməyin.",
        "Xırda zolaqlı və damalı geyim ekranda titrəyir — düz rəng daha yaxşıdır.",
    ]),
]

NO_SPEECH = {5, 7, 9}  # tədbir, kameraarxası, nağıl (cizgi) — kameraya danışıq əsas deyil

SHOOT: dict[int, dict[str, Any]] = {
    1: {"format": "şaquli (9:16)", "shots": [
        "Əsas plan: beldən və ya sinədən yuxarı, kameraya baxaraq danışırsınız.",
        "2–3 əlavə görüntü (hər biri 5–10 s): iş prosesi, əllər, material, məkan — sonra araya qoyulur."],
        "tips": ["Mətni əzbərləməyə ehtiyac yoxdur; fikri cümlə-cümlə deyin."]},
    2: {"format": "şaquli (9:16)", "shots": [
        "Sual verən kameranın yanında, göz səviyyəsində dayanır; siz ona baxırsınız (kameraya yox).",
        "Əsas plan: beldən yuxarı."],
        "tips": ["Mikrofon sual verənin səsini də tutsun.",
                 "Cavaba sualı təkrarlayaraq başlayın («Ən böyük səhv odur ki…») — sual kəsilsə də cavab anlaşılsın."]},
    3: {"format": "şaquli (9:16)", "shots": [
        "Hazır mətni cümlə-cümlə çəkin, hər cümlə 2 dubl.",
        "Məhsul / xidmət görüntüləri: detal (yaxın), istifadə anı, nəticə — hər biri 5–10 s."],
        "tips": ["Qiyməti, tarixi, endirimi və çağırışı (məs. «Direktə yazın») aydın deyin — ekranda yalnız deyilən göstərilir.",
                 "Sonda bir aydın çağırış olsun."]},
    4: {"format": "üfüqi (16:9) — sonra qısa Reels hissələri çıxarılır", "shots": [
        "Arxadan sabit geniş plan (ştativ): təlimçi və lövhə/ekran.",
        "Mümkünsə ikinci telefon: təlimçinin yaxın planı.",
        "Auditoriya: reaksiyalar, sual verənlər (5–10 s)."],
        "tips": ["Təlimçiyə yaxa mikrofonu; auditoriyanın sualı üçün ikinci mikrofon.", "4K — sonra şaquli kəsim keyfiyyətli olsun."]},
    5: {"format": "şaquli (9:16)", "shots": [
        "Açılış: məkanın ümumi planı, giriş, banner/ad nişanı (detal).",
        "İnkişaf: iştirakçılar fəaliyyətdə, təlimçinin yaxın planı, əllər, materiallar.",
        "Reaksiyalar: gülüş, alqış, maraqla dinləyən üzlər.",
        "Final: sertifikat, qrup şəkli, sağollaşma."],
        "tips": ["Hər kadr 5–10 s sabit tutulsun; hərəkətli çəkilişdə yavaş gəzin.",
                 "Bir neçə gözəl anı 60 fps çəkin (yavaşlatma üçün).", "Musiqi montajda əlavə olunur — tədbirin səsi əsas deyil."]},
    6: {"format": "şaquli (9:16)", "shots": [
        "Hər addım üçün: ümumi plan + əllərin yaxın planı + nəticə.",
        "Material üzərində iş üçün yuxarıdan çəkiliş (telefon masanın üstündə)."],
        "tips": ["İzahı ya çəkiliş zamanı danışın, ya da sonra sakit otaqda ayrıca səs kimi yazın.",
                 "Vacib addımı gizlətməyin, yavaş göstərin."]},
    7: {"format": "şaquli (9:16)", "shots": [
        "Hazırlıq, material seçimi, iş anları: insan + detal.", "Hər kadr 10 s sabit."],
        "tips": ["Real prosesi çəkin — səhnələşdirmə lazım deyil."]},
    8: {"format": "şaquli (9:16)", "shots": [
        "Mətndəki hər fikir üçün 2–3 görüntü (5–10 s).", "Səsləndirmə ayrıca."],
        "tips": ["Səsləndirməni sakit otaqda, telefon ağızdan 15–20 sm, hazır mətnlə yazın."]},
    9: {"format": "şaquli (9:16)", "shots": [
        "Çəkiliş lazım deyil — səhnələr cizgi ilə qurulur.",
        "İstəsəniz: kameraya baxaraq nağıl oxuyun (küncdə dairədə görünəcəksiniz)."],
        "tips": ["Səsləndirmə: sakit otaq, ifadəli oxu; obrazların səsini bir az fərqləndirin."]},
    10: {"format": "şaquli (9:16)", "shots": [
        "Yaxın plan (sinədən yuxarı) — üz ifadəsi görünsün.", "Suallar qısa, ardıcıl."],
         "tips": ["Mikrofon sual verənin də səsini tutsun.", "Kəsmədən çəkin — spontan reaksiya və gülüş saxlanılır."]},
    11: {"format": "şaquli və ya üfüqi; 4K", "shots": [
        "İkiniz bir kadrda, yan-yana, bir-birinizə 30–45° dönük — hər ikinizin üzü görünsün.",
        "Ştativ sabit, kadr hər ikinizi tutsun."],
         "tips": ["Hər ikinizə mikrofon.", "4K — montajda kadraj danışana keçir və ya ekran ikiyə bölünür."]},
    12: {"format": "şaquli (9:16)", "shots": ["Əsas plan: beldən yuxarı, kameraya baxaraq."],
         "tips": ["Mövzunu sıra ilə danışın: «Birincisi…, ikincisi…, sonuncu…» — hər fikir ayrıca karusel slaydı olur.",
                  "Hər fikir 10–40 s."]},
    13: {"format": "şaquli (9:16)", "shots": [
        "Ekran yazısı (telefon/kompüter, ən azı 1080p) və ya materialın yaxın, kölgəsiz çəkilişi.",
        "Sizin kameraya baxaraq izahınız — ayrıca."],
         "tips": ["Ekranda lazımsız bildirişləri bağlayın."]},
    14: {"format": "şaquli (9:16)", "shots": [
        "Rəy verən: beldən yuxarı, sual verənə baxır.", "Təlim/xidmət anlarından 2–3 görüntü."],
         "tips": ["Öz sözləri ilə danışsın, hazır mətn olmasın.", "Adı və vəzifəsi ekrana yazılacaqsa — dəqiq yazılışı və razılığı."]},
    15: {"format": "üfüqi (16:9)", "shots": [
        "Ştativ, sabit kadr: beldən yuxarı, yanda slayd/lövhə üçün yer."],
         "tips": ["Bütün bölümlər eyni geyim, eyni məkan, eyni kadr və işıqla çəkilsin.",
                  "Bölümü adını deyərək başlayın. Slaydları ayrıca fayl kimi göndərin.", "4K, sabit işıq (pəncərə işığı dəyişməsin)."]},
    16: {"format": "şaquli (9:16)", "shots": ["Əsas plan: beldən yuxarı, kameraya baxaraq."],
         "tips": ["Rəqəmləri dəqiq deyin — qrafika yalnız deyilən rəqəmlə qurulur.", "Məlumat/cədvəl varsa, faylı ayrıca göndərin."]},
    17: {"format": "—", "shots": [], "tips": ["Loqo faylı: şəffaf fonlu PNG və ya SVG."]},
}


def text(n: int, name: str | None = None, compact: bool = False) -> str:
    """Müştəriyə göndəriləcək mesaj (az dilində)."""
    from montaj import types

    t = types.get(n)
    sh = SHOOT[int(n)]
    out = [f"Çəkiliş tövsiyəsi — {t['short']}" + (f" ({name})" if name else ""), f"Format: {sh['format']}", ""]
    if sh["shots"]:
        out.append("Nəyi çəkək:")
        out += [f"• {x}" for x in sh["shots"]]
    if sh["tips"]:
        out.append("")
        out.append("Vacib:")
        out += [f"• {x}" for x in sh["tips"]]
    if int(n) != 17:
        speech = int(n) not in NO_SPEECH
        for title, items in (COMMON[:3] if compact else COMMON):
            items = [x for x in items if speech or "cümlə" not in x]  # danışıqsız növdə danışıq məsləhəti yoxdur
            out.append("")
            out.append(f"{title}:")
            out += [f"• {x}" for x in items]
    return "\n".join(out)
