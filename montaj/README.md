# Montaj paneli

OpenMontage üçün Azərbaycan dilində brauzer montaj redaktoru. Mövcud pipeline
axınına (`pipeline_defs/`, `backlot/`, `tools/`) toxunmur — ayrıca paketdir.

## İşə salma

```bash
pip install -r requirements.txt          # fastapi, uvicorn, numpy …
pip install faster-whisper               # istəyə görə: yerli transkripsiya
python -m montaj                          # yalnız lokal sınaq: http://localhost:4760/ (MONTAJ_AUTH=off və ya MONTAJ_PASSWORD lazımdır)
python -m montaj --host 0.0.0.0           # eyni Wi-Fi-dakı telefondan: http://<kompüter-IP>:4760/
```

Tələb: `ffmpeg` və `ffprobe` PATH-də olmalıdır.

## Necə işləyir

| Mövzu | Həll |
|---|---|
| Orijinal fayl | `projects/<id>/media/originals/` — yüklənəndən sonra yalnız-oxunur (0444), heç vaxt dəyişmir |
| Klip | `media` + `srcIn`/`srcOut` (mənbə vaxtı). Video qatı ardıcıl (`order`), digər qatlar `start` ilə |
| Video + öz səsi | Danışıq qatındakı səs `linkedTo` ilə videoya bağlıdır: bölmə, silmə, kəsmə, yerdəyişmə birlikdə. **⛓ Səsi ayır** ayrıca seçimdir |
| Qatlar | Video · Danışıq · Musiqi · Səs effekti · Mətn |
| Kəsilmiş materialı qaytarmaq | Klipin kənarını sürüşdürün — mənbə faylın sərhədinə qədər geri uzanır |
| Undo/redo | Tam layihə snapşotları; brauzerdə saxlanır, yenidən açanda davam edir |
| Avtomatik saxlama | Hər dəyişiklikdən 0,6 s sonra `montaj.json`; əvvəlki 30 versiya `montaj_history/`-də |
| Önizləmə = render | Hər ikisi eyni `montaj.json`-dan oxuyur. Render yalnız saxlanmış versiyadan başlayır |
| Render | FFmpeg (`montaj/render.py`); video kadr sərhədinə kvantlaşdırılır, bağlı səs eyni başlanğıcı götürür → sürüşmə yığılmır |
| Təkliflər | Səssizlik (ffmpeg) və doldurucu sözlər (faster-whisper) storyboard kimi göstərilir; **Təsdiqlə** basılmayınca montaj dəyişmir. ✋ işarəli (əl ilə düzəldilmiş) kliplər atlanır |
| LLM təklifi | Qoşulmayıb — UI-da "qoşulmayıb" kimi göstərilir |

## Testlər

```bash
node --test tests/montaj/timeline.test.mjs   # zaman xətti əməliyyatları, undo/redo, təkliflər
pytest tests/montaj                          # render + səs-görüntü sinxronu, saxlama, API
# Brauzer E2E (server işləyərkən):
MONTAJ_URL=http://localhost:4760 MEDIA_DIR=<qovluq> OUT_DIR=<qovluq> NODE_PATH=$(npm root -g) \
  node tests/montaj/e2e_browser.mjs mobile   # və ya desktop
```

`MEDIA_DIR`-də `sinxron.mp4`, `sukut.mp4`, `musiqi.wav` olmalıdır —
`tests/montaj/test_montaj.py`-dəki `make_sync_source` / `make_silence_source` ilə yaradılır.

## v2: telefondan istifadə

Telefon üçün HTTPS yerləşdirməsi: [`deploy/README.md`](../deploy/README.md).
Tələblərin izlənən siyahısı və hər bəndin real statusu: [`TELEBLER.md`](TELEBLER.md).

Axın: **＋ Yeni video** → material (telefon / Drive linki) → “Kimin videosudur?” →
montaj seçimləri → storyboard (təsdiq) → redaktor (Kadraj, Görüntü, Səs, Qrafika) → **Paylaş**.

Parol: `MONTAJ_PASSWORD` mühit dəyişəni (yoxdursa server 503 qaytarır). Lokal sınaq üçün `MONTAJ_AUTH=off`.
