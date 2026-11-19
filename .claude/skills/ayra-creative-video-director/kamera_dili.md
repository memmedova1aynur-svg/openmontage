# Kamera dili — bucaq, plan, hərəkət (AYRA bələdçisi)

Mənbə ideya: [mert-builds/rehberler — kamera.md](https://github.com/mert-builds/rehberler/blob/main/kamera.md) və onun əsaslandığı [Kapwing — The Complete AI Camera Prompt Guide: 77 Shots and Movements](https://www.kapwing.com/resources/the-complete-ai-camera-prompt-guide-77-shots-and-movements/) (hər hərəkətin nümunə klipi oradadır). Bu fayl həmin terminologiyanın AYRA üçün öz sözlərimizlə yazılmış xülasəsi və tətbiq qaydalarıdır; mətn köçürülməyib.

**Tam cədvəl (hər termin üçün açıqlama + hazır ingiliscə komanda, 9 hazır kombinasiya, model qeydləri):** `instagram-clients/_agency/kamera_77_komut.md` — agentliyin daxili nüsxəsi (mənbədə lisenziya yoxdur, ona görə açıq repoya qoyulmur). Prompt yazanda komanda oradan götürülür; bu fayl qaydalar və AYRA tətbiqi üçündür.

Üç yerdə işlənir:
1. **Süni intellektlə B-roll / səhnə yaradanda** (ai-video-gen, Higgsfield, Seedance, Kling, Veo, Sora, Runway) — prompt formulu.
2. **Montajda** (HyperFrames) — talking-head kadrında kamera hərəkətini təqlid etmək.
3. **Çəkiliş planında** — operatora hansı bucaq və planların lazım olduğunu demək (məs. yan rakurs).

---

## 1. Prompt formulu (4 hissə, həmişə bu ardıcıllıqla)

| # | Hissə | Nə yazılır |
|---|---|---|
| 1 | Səhnə | Kim, harada, nə edir — bir cümlə, kamera sözü yoxdur |
| 2 | Plan + bucaq | Kadrda nə qədəri var, kamera haradan baxır |
| 3 | Bir hərəkət | Kamera nə edir — yalnız bir |
| 4 | Üslub sətri | İşıq, lens, rəng — bütün kadrlarda eyni |

Şablon (ingiliscə — modellər ingiliscə daha dəqiq işləyir):
```
[Scene: who, where, doing what.]
[Shot size], [angle].
[One camera move, how it moves, how it ends].
[Style line — identical for every clip of the project].
```
Referans şəkil varsa başa əlavə et: `Image 1 is the [person/product].`

## 2. Qızıl qaydalar
1. Bir promptda **bir əsas hərəkət**. Pan + zoom + orbit birlikdə = üçü də yarımçıq.
2. İstəmədiyini açıq yaz: `static camera, no movement`; dolly ilə zoom qarışırsa `camera physically moves, no lens zoom`.
3. Bucaq və plan bir-birini dəstəkləsin: alçaq bucaq + yaxın plan = güc; yüksək bucaq + geniş plan = kiçiklik, təklik.
4. Üslub sətrini bütün kliplərdə **eyni** saxla — yoxsa montajda kliplər bir-birinə yad görünür.
5. Hərəkətin necə bitdiyini yaz (`ends on a stable frame`) — son kadr montajda işlənə bilsin.
6. **AYRA qaydası:** real müştərinin üzü süni intellektlə yaradılmır/dəyişdirilmir. Süni intellekt yalnız əşya, məkan, illüstrativ B-roll üçün; insanlı kadr = real çəkiliş.

## 3. Terminologiya (77)

### Hərəkətlər (46)
- **Pan/Tilt (7):** static shot · pan right / left · whip pan right / left · tilt up / down — kamera yerində fırlanır.
- **Zoom/Lens (6):** fast zoom in / out · slow zoom in / out · crash zoom in / out — kamera yerində, lens dəyişir.
- **Dolly/Track (9):** dolly in / out · tracking · side tracking · vehicle tracking · chase · follow / over-the-shoulder · reverse tracking (walk-and-talk) · low tracking — kamera fiziki hərəkət edir.
- **Fiziki yerdəyişmə (11):** truck left / right · pedestal up / down · slider left / right (paralaks) · arc left / right · orbit clockwise / counterclockwise · push-past.
- **İnsan əli (2):** first-person POV · handheld.
- **Dron/Kran (5):** crane up / down · drone pull back / push in · helicopter.
- **Xüsusi (6):** snorricam · pass-through · tilt-shift · time-lapse · earth zoom out · infinite zoom.

### Bucaqlar (22)
bird's-eye · dutch tilt · establishing · extreme dutch tilt · eye level · from behind · ground level · hero angle · high angle · hip level · low angle · over-the-shoulder · overhead/top-down · POV · **profile (tam yan)** · reverse angle · shoulder level · single · **three-quarter (≈45°)** · two-shot · upside down · worm's-eye.

### Plan ölçüləri (9)
extreme wide · wide · full · medium wide (cowboy) · medium (beldən yuxarı) · medium close-up (sinədən yuxarı) · close-up · extreme close-up · insert/macro.

## 4. Montajda təqlid (HyperFrames, talking-head)
Kadr bir kameradan çəkiləndə hərəkət rəqəmsal yolla verilir. Ani sıçrayış qadağandır (bütün müştərilər) — hamısı 0.6–1.2 s, `sine.inOut`.

| Termin | Montajda qarşılığı |
|---|---|
| slow zoom / dolly in | `#cam` miqyası 1.00 → 1.06–1.10, yavaş |
| dolly out | miqyas azalır; kəsik (insan maskası) qatı varsa fon bir az da kiçilir → dərinlik |
| slider / truck | insan kəsiyi və fon fərqli sürətlə sürüşür (paralaks) |
| arc / three-quarter hissi | kəsik qatına yüngül `rotateY` (≤12°) + fona əks sürüşmə — əsl yan bucaq deyil, effektdir; belə yazılır |
| whip pan | keçiddə üfüqi hərəkət bulanıqlığı + 0.2 s sürüşmə (yalnız mövzu dəyişəndə) |
| crash zoom | yalnız komik/şok vurğusu; ekspert videosunda nadir |
| static | kamera sabit — sakit izah, rəqəm, nəticə anları |
| handheld | çox yüngül titrəmə — yalnız sənədli/vlog tərzində |

## 5. Çəkiliş siyahısı (operator üçün)
Bir kameralı çəkilişdən sonra **yan rakurs montajda yaradıla bilmir** (üzün süni intellektlə yaradılması qadağandır). Lazımdırsa çəkilişdə əlavə olunur:
- **İkinci kamera** — **three-quarter (≈45°)** və ya **profile (90°)**, göz səviyyəsində, eyni işıq. Danışıq boyu yazır; montajda cümlə keçidlərində ona keçilir.
- Hər video üçün 3–4 **B-kadr (5–10 s)**: profildən dayanıb danışır · yana/pəncərəyə baxıb düşünür · masada kitab/dəftər (insert/macro) · otağa daxil olur (full shot, tracking).
- Eyni rəng balansı və eyni geyim — kadrlar bir-birinə uyğun gəlsin.
