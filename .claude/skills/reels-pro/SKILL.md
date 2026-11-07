---
name: reels-pro
description: Ekspert danışıq və reklam Reels-lərini Drive linkindən ilk dəfədən PRO keyfiyyətdə montaj edən sistem — paralel qəbul, sözə bağlı kart səhnələri, ev qaydaları (house.json) və göndərmədən əvvəl avtomatik QA darvazası. İstifadəçi "Drive linki", "bu videoları montaj et", "10 video", "reels pro", "reklam videosu", "danışıq videosu" deyəndə və ya bir neçə videonu toplu montaj istəyəndə işlət.
---

# reels-pro — Drive linkindən hazır Reels-ə

Kod: `templates/expert-reels/pro/` (build.py, lib.html, render.js, qa.py, house.json, ingest.py, batch.py, sfx_premium.py).
Hədəf: 10 video ≈ 1–1.5 saat, **ilk göndərilən versiya QA-dan keçmiş** olsun. İstifadəçi düzəliş yazmalı olmasın.

## Qızıl qaydalar (2 günlük səhvlərdən çıxarılıb — pozma)

1. **QA keçməyən video göndərilmir.** `build.py` sonda `qa.py`-ni çağırır; çıxış kodu 3 = keçmədi. Səbəbi `vN/qa.json`-dadır. Düzəlt, yenidən qur, sonra göndər. "Hamısını düzəltdim" demə — QA nəticəsini göstər.
2. **Ev qaydalarını dəyişmə, konfiqə yazma.** `house.json` hər videoya avtomatik qatılır:
   musiqi yoxdur · premium tonal SFX (xışıltı/pop/"öskürək" yox) · bir istiqamətli hamar glide zoom (yaxınlaş-uzaqlaş YOX) · yumşaq kart keçidi · təhlükəsiz zona (safe 0.86) · sözdən əvvəl 0.15 s / sonra 0.2 s boşluq · danışıq bərabərləşdirmə · yarpaq yaşılı palitra (laym QADAĞAN) · güzgü düzəlişi.
3. **İstifadəçi "yalnız X-i dəyiş" deyirsə** — yalnız o videonun konfiqinə toxun, başqa videoları yenidən render etmə.
4. **Səhnə ölçüsü qaydaları** (səhnə planı yazanda):
   - Kart ilk açar söz deyiləndə açılır (`from` + `ts` anchor-ları sözlərdir, saniyə yox).
   - Hər bənd (`ts`) ən az 1 s tam görünür — build.py kartı avtomatik uzadır; amma bəndləri sözlə yaxın seç ki, kart lazımsız uzanmasın.
   - Tam ekran kart (kinetic, page, icons, cols, contrast, transform, stripes...) ≤ 4.5 s; ardıcıl iki tam ekran kart qoyma.
   - Danışan kadr ən az 40% görünsün; split (alt panel) və lower/top kartlar üzü örtmür.
   - Reklam: 1 kinetic brend kartı əvvəldə ("ÖYRƏNMƏYİ ÖYRƏN"), 1 kinetic sonda, sonuncu `lower` kartda `btn: "Bizə yazın"`.
   - Video sonu: danışıq bitəndən sonra ≤ 0.7 s saxlama (build.py avtomatik).
5. **Faktlar**: kartlarda yalnız danışıqda deyilən və ya mənbəli fakt; qiymət/tarix uydurma.

## İş axını

```bash
cd templates/expert-reels/pro
export MONTAJ_DATA_DIR=/root/montaj-data PRO_WORK=/root/montaj-data/plans/pro PRO_OUT=<scratchpad>
# 1) qəbul (paralel): endir + ASR + kadraj + vN.json qaralama + vN_words.txt
python3 ingest.py batch.json
# 2) Claude: hər vN.json üçün "scenes" yaz (vN_words.txt-ə bax; examples/*.json nümunədir)
#    yoxla: python3 build.py vN.json plan   → səhnə vaxtları, render etmədən
# 3) montaj (3 paralel xətt) + QA darvazası
python3 batch.py --all          # və ya batch.py v9.json v10.json
```

`batch.json`: `{"client": "...", "prefix": "xeyyam-video", "start": 9, "videos": [{"link": "...", "type": "talk|ad", "title": "...", "script": "istəyə görə"}]}`.
İstifadəçidən yalnız linklər və hər videonun növü (danışıq / reklam) lazımdır. Növ deyilməyibsə: təlimə çağırış varsa `ad`, yoxsa `talk`.

## QA darvazası nəyi tutur (qa.py)

| yoxlama | nə | niyə əlavə olundu |
|---|---|---|
| freeze | danışan görünərkən ≥6 kadr hərəkətsiz | kart bağlananda PNG RGB↔RGBA dəyişib filtri sıfırlayırdı → səs gedir, görüntü donur |
| cut | kəsim mənbədə danışığa düşür | sözün başı/sonu kəsilirdi |
| loud | LUFS −16…−12.5, pik ≤ −1, klik | səs zəif/uca, kliklər |
| sfx | pop/softclick/paperclick | "öskürək" kimi səs |
| color | laym rəngləri konfiqdə | istifadəçi laymı qadağan edib |
| card | son bənd < 0.9 s görünür | "Kimlər üçün?" 3-cü bəndi yarım saniyə qalırdı |
| dup (warn) | tək təkrar kadr | ilişmə hissi |

## Bilinən texniki tələlər (həll olunub — geri qaytarma)

- Zoom: `scale+crop` pilləli idi → `zoom_filter` (perspective, subpiksel). Glide: bütün video boyu z0→z1, kəsimdə miqyas eyni.
- Kadr tezliyi: `fps=` filtri kəsimdən sonra kadr təkrarlayırdı → `setpts=N/30/TB` + ortaq `settb=1/90000` + overlay `ts_sync_mode=nearest`.
- Kompozit: hər video parçası öz `-ss` girişi ilə (split+trim sonu dondururdu); kart PNG-ləri RGBA-ya normallaşdırılır.
- Kart müddəti: `TAIL = 1.0 + keçid`; növbəti kiçik kart lazım olsa sürüşdürülür.
- Kadraj: framefix nəticəsi (`storyboard_draft.json`) və ya konfiqdə `crop: {s, cx, cy}`; oturma xətti altda qalmasın.

## Editorial tema (Vəfa Əli üslubu) — `"theme": "editorial"`

Konfiqə `"theme": "editorial"` yazanda house.json-dakı `themes.editorial` qatılır: bordo vurğu (#7A1E3A), krem kağız kartlar, tünd isti fon, kiçik altyazı (vurğu sözü çəhrayı-bordo). Nümunə: `examples/editorial_example.json`.

| səhnə | növ | nə üçün |
|---|---|---|
| `equote` | video üstü | video qaralır, mərkəzdə sitat / rəqəm / müəllif (`lines` stil: s=italik, b=qalın, m=bordo blok) |
| `esticker` | video üstü | ağ etiket: "qeyri-müəyyənlik → təhlükə" |
| `ename` | video üstü | ad zolağı — **sonda** verilir, başda yox |
| `escale` | kağız kart | tərəzi: iki tərəfin qarşılaşdırılması |
| `evenn` | kağız kart | iki anlayış "eyni anda" |
| `elist` | kağız kart | seriyalı siyahı "02 / 04: ya …, ya da [çərçivə]" |
| `eword` | kağız kart | açar söz + çərçivəli nəticə |
| `eseries` | final kartı | "SERİYA · Başlıq · BİRİNCİ EPİZOD" (`toEnd`) |

Qaydalar: hook salamsız — sitat və ya rəqəmlə (`equote`) başlayır; hər 15–20 s bir kart; bir videoda 6–10 kart; vurğu rəngi yalnız bir; musiqi yalnız müştəri icazə verirsə (Xəyyam: musiqi yoxdur). Müştərinin öz rəngi varsa, `pal` üzərindən `acc` dəyişdirilir.

## Peşəkar alətlər (brend kiti, musiqi, rəng, punch-in, b-roll, formatlar)

**Brend kiti** — `instagram-clients/<müştəri>/brand_kit.json` (şablon: `brand_kit_template.json`; repoya düşmür). Video konfiqində `"brand": "<müştəri>"`. Sıra: house → tema → kit.cfg → video konfiqi. Kitdə: `handle`, `theme`, `palette` (məs. `{"acc": "#..."}`), `cfg` (look, music, punch, cta, exports, watermark), `glossary` (daimi altyazı düzəlişləri), `forbiddenColors` (QA yoxlayır), `hashtags`, `rules`.

| açar (kit.cfg və ya video konfiqi) | nə edir |
|---|---|
| `"music": {"file": "...", "volume": 0.12}` | bütöv musiqi yatağı, danışıqda avtomatik aşağı (sidechain). `null` = musiqi yoxdur (Xəyyam) |
| `"look": "warm_cinematic \| clean_studio \| natural \| moody"` | rəng preseti, yalnız danışan kadra |
| `"punch": "auto"` və ya `[{"from": "söz", "until": "söz", "scale": 1.1}]` | vacib yerdə yüngül yaxınlaşma (tam ekran kartlarda yox) |
| `"broll": [{"file": "...", "from": "söz", "dur": 2.5, "mode": "cover"}]` | müştərinin öz kadrları sözə bağlı |
| `"corrections": [{"from": "...", "to": "..."}]` | bu videonun altyazı düzəlişləri |
| `"exports": ["4x5", "short15"]` | QA-dan sonra 4:5 lent versiyası + 15 s qısa kəsim |
| `"watermark": true` (+ kitdə `handle`) | sağ yuxarıda kiçik @handle (QA-dan əvvəl) |
| `"coverTitle": "Başlıq *vurğu*"`, `"coverAt": 12.4` | üz qabığı başlığı / konkret kadr |

**Alətlər** (`templates/expert-reels/pro/`):
- `words_check.py <vN.json>` — render-dən ƏVVƏL: ASR-in əmin olmadığı sözlər → `vN_yoxla.md`. Şübhəli sözü düzəlt (corrections/glossary), sonra build.
- `postfx.py watermark|exports|cover` — build.py özü çağırır; əl ilə də işləyir. Üz qabığı montajın üz modeli ilə ən kəskin, mərkəzdə olan kadrı seçir → `_cover.jpg` + `_cover_grid.jpg` (3:4).
- `brief.py` — `_paket.md`: hook namizədləri, kartlar, mətn, caption şablonu. Son caption-ı Claude danışığa sadiq yazır.
- `review_page.py <mp4>` — `_baxis.html`: telefonda açılır, saniyəyə qeyd yazılır, "Kopyala" ilə chat-a.
- Sürət: səhnə kompozitləri paralel (`PRO_COMP_JOBS`, default 2), ara fayllar `PRO_COMP_PRESET=faster`.

Brend "möhürü" (videonun əvvəlinə 0.5 s logo) bilərəkdən qurulmayıb: hook-u gecikdirir, izləmə müddətini azaldır. Brendlik handle işarəsi və seriya final kartı ilə verilir.

## Ölçmə, planlaşdırma, çəkiliş, əlavə məzmun

| alət | nə vaxt | nə edir |
|---|---|---|
| `metrics_report.py <müştəri> <metrics.json>` | ayda 1 | Metricool reel göstəriciləri → `hesabat_<tarix>.html` + brend kitinə `learnings` (hook növü, uzunluq üzrə). Teqlər `instagram-clients/<müştəri>/posted.json`-dan; qrupda ən az 2 reel olmasa nəticə çıxarılmır |
| `schedule_plan.py <müştəri> <plan.json>` | paylaşımdan əvvəl | ən yaxşı saatlar (getBestTimeToPostByNetwork) + grid qaydası → cədvəl və Metricool qaralamaları (draft). Media = Drive linki (Drive Metricool-a bağlı olmalıdır). **Göndərmə yalnız istifadəçi təsdiqindən sonra** |
| `preflight.py <sınaq.mp4>` | çəkiliş günü, ilk 10–20 s | istiqamət, keyfiyyət, fps, danışıq səviyyəsi, fon küyü, klip, işıq, üz ölçüsü/mərkəz/baş üstü → HAZIR / DİQQƏT / DÜZƏLT + nə etmək |
| `shoot_sheet.py <çəkiliş.json>` | çəkilişdən əvvəl | bir səhifəlik vərəq: texniki checklist, videolar paltara görə qruplaşdırılmış, suallar |
| `carousel_from_cards.py <vN.json> <mp4>` | QA-dan sonra | videonun tam ekran kartlarından 4:5 karusel (üz qabığı + kartlar + çağırış) |
| `story_pack.py <vN.json> <mp4>` | QA-dan sonra | tizer (ilk cümlə + "Tam video profildə"), sorğu kadrı, kart kadrı |
| `ab_hook.py <vN.json> <mp4> "Hook B"` | test | ilk 2.8 s fərqli açılış → `_B.mp4`; Trial Reel kimi paylaşılır, view rate müqayisə olunur |
| `docs/razilig_formasi.md` | uşaq/üçüncü şəxs kadrda | valideyn razılıq forması |

Build özü: köhnə nəticə `versiyalar/PRO_x_vN.mp4` kimi saxlanılır; musiqi işlənəndə `vN/musiqi_lisenziya.txt` (konfiqdə `music.source`, `music.license`).
Metricool-da hazırda yalnız @1aynurmemmedova qoşuludur; müştərilər üçün onların səhifəsi Metricool-a əlavə olunmalıdır.

## Göndərmə

Yalnız `HAZIR (QA keçdi)` siyahısındakı faylları göndər. Hər video üçün bir sətir: QA nəticəsi (kəsim sayı, LUFS, donma 0). WARN-ları dürüst yaz.


## Agentlik qaydaları (üstündür)

`instagram-clients/_agency/` qovluğunda agentliyin iş sənədi (`studiya_qaydalari.md`, PDF) və montaj kataloqu (`s_kodlar.json`, S01–S36) varsa, işə başlamazdan əvvəl oxu; bu qaydalar bu faylla ziddiyyət təşkil edərsə onlar üstündür. Standart rejim avtomatik təhvildir; storyboard yalnız istənəndə (`talk.py plan.json storyboard`). Tərz kataloqu: `templates/expert-reels/pro/styles/README.md`.
