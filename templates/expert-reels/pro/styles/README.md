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

`styles/<ad>.json` faylı yarat. `_` ilə başlayan açarlar (`_ad`, `_nə_vaxt`) yalnız sənəddir. Mövcud parametrlər: `sub` (`lines`/`words`/`none`), `zooms`, `gap`, `cut_sfx`, `word_size`, `word_mv`, `q_size`, `q_bg`, `card_size`, `color` (ffmpeg rəng zənciri), `accent`.

Qayda: oyun videoları həftədə 1-dən çox olmasın (kontent bəsit görünməsin).
