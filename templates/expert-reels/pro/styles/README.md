# Montaj tərzləri kataloqu

Müştəri **kim** olduğunu, tərz isə videonun **necə** montaj olunacağını müəyyən edir.

| Qat | Nə saxlayır | Harada |
|---|---|---|
| Müştəri | kadraj (üz, aşağı hissə), güzgü, brend rəngi (`accent`), ad | `instagram-clients/<müştəri>/brand_kit.json` → `talk` |
| Tərz | altyazı tipi, kəsim tempi, zoom, kartlar, SFX, rəng | `styles/<tərz>.json` |
| Video | kəsim aralıqları, hook, düzəlişlər, kart mətnləri | video planı (`plan.json`) |

Birləşmə sırası: default → müştəri → tərz → video planı (sonrakı üstün gəlir). Yəni eyni müştəri hər videoda fərqli tərz seçə bilər, kadrajı və rəngi isə avtomatik qalır.

## Tərzlər

| Tərz | Alət | Nə vaxt | Video planında əlavə |
|---|---|---|---|
| `sade` | talk.py | Səmimi söhbət; sadə ağ altyazı, kəsiklərdə yüngül zoom | — |
| `dinamik` | talk.py | Sürətli məsləhət, siyahı; söz-söz iri altyazı (aktiv söz vurğu rəngində), sıx kəsim, güclü zoom, swoosh | — |
| `musahibe` | talk.py | Sual-cavab; sual kartı, geniş/yaxın plan növbəsi | `questions: [[san, müddət, "Sual"]]` |
| `mif_fakt` | talk.py | İddia kartı + jestə sinxron qırmızı/yaşıl/sarı işıq və səs | `statements: [[başla, son, "İddia"]]`, `verdicts: [[san, "mif"\|"fakt"\|"yari"]]` |
| `minimal` | talk.py | Reklam, tanıtım; davamlı altyazı yox, iri açar söz kartları, sakit rəng | `cards: [[başla, son, "Söz"]]` |
| `dinamik_qalin` | talk.py | Ən güclü hook, cəsarətli fikir; 1–2 sözlük iri BÖYÜK HƏRFLİ altyazı, açar sözlər ikinci rəngdə | `keywords: ["söz"]` |
| `hook_basliq` | talk.py | Universal: video boyu yuxarıda sabit başlıq (səssiz izləyən də anlayır) + izləmə xətti | `headline: "Başlıq"` |
| `siyahi` | talk.py | "3 səhv", "4 addım": hər bənd deyiləndə nömrə ilə düşür və qalır, sonda tam siyahı ekranda (yadda saxlama gətirir) | `items: [[san, "Bənd"]]` |
| `serh_cavab` | talk.py | İzləyicinin real şərhinə video cavab; Instagram şərh balonu (yalnız real şərh, icazə ilə) | `comment: {t0, t1, user, text}` |
| `sekil_izah` | talk.py | Sxem, ekran görüntüsü, sənəd: split ekran (yuxarıda şəkil, aşağıda danışan) və ya tam ekran + dairəvi PiP | `inserts: [[başla, son, "şəkil.png", "split"\|"full"]]` |
| `kinematik` | talk.py | Hekayə, motivasiya: kino çərçivəsi, dən, vinyet, isti-soyuq rəng, kursiv serif altyazı | — (musiqi tövsiyə olunur) |
| `taymer` | talk.py | "60 saniyədə 3 məsləhət": küncdə geri sayım + dinamik altyazı | `timer: {t0, dur, label}` |
| `senedli` | editorial.py | Elmi mövzu; qrafik səhnələr, məqalə, kamera hərəkəti, kino dənəsi | plan editorial.py başlığında |
| `oyun` | game.py | Ekspertsiz interaktiv animasiya (yaddaş, Stroop, diqqət, boşluq) | `page`, `name`, `music` |

Kart və sual mətnlərində yeni sətir: `\N`. Vaxtlar hazır videonun zaman xəttindədir (kəsimdən sonra).

## İstifadə

```bash
python3 talk.py plan.json          # plan.json-da "style": "dinamik"
python3 editorial.py plan.json
python3 game.py plan.json
```

Hər nəticə `_vN` versiyası ilə yazılır (təsdiqlənmiş fayl qorunur), yanında `_qa.json`, story parçası və üz qabığı kadrı olur.

## Yeni tərz əlavə etmək

`styles/<ad>.json` faylı yarat. `_` ilə başlayan açarlar (`_ad`, `_nə_vaxt`) yalnız sənəddir. Mövcud parametrlər:
- altyazı: `sub` (`lines`/`words`/`none`), `font`, `fontsize`, `sub_bold`, `sub_italic`, `sub_outline`, `mv`, `upper`, `max_words`, `max_chars`, `keywords`, `word_size`, `word_mv`
- tempo və kadr: `zooms`, `gap`, `cut_sfx`, `cut_sfx_db`, `color` (ffmpeg rəng zənciri), `letterbox`, `grain`
- elementlər: `progress`, `headline`, `items`, `comment`, `inserts`, `timer`, `questions`, `statements`, `verdicts`, `cards`
- rəng: `accent` (müştəri kitindən də gələ bilər), `accent2`, `q_bg`, `split_bg`, `full_bg`

Hər element istənilən tərzlə birləşə bilər: məs. `dinamik` + `headline` + `progress`.

Tərzin istədiyi şrift (məs. `Lora`) sistemdə yoxdursa, avtomatik yüklənir (Google Fonts, OFL).

Qayda: oyun videoları həftədə 1-dən çox olmasın (kontent bəsit görünməsin).
