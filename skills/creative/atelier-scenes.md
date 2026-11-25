# Bəzək rejimi (atelier) — hero videolar üçün sıfırdan yazılmış səhnə

Hazır `scenes` kataloqu = dondurulmuş görünüşlər (hamısı bir-birinə oxşar). Hero video (reklam, brend, vacib bir video) üçün səhnəni həmin video üçün YAZ.
Mühərrikin biliyini istifadə et, yaradıcı komponenti yox: mövcud səhnəni kopyalama.

## Müqavilə
- Tək HTML fayl. `window.setTime(t)` — t saniyəyə görə səhnəni qurur. Animasiya YALNIZ t-dən asılıdır (`Date`, `requestAnimationFrame`, CSS keçid/animasiya yoxdur) —
  çünki kadrlar deterministik çəkilir.
- `window.ATELIER_CTX = {W, H, fps, dur, theme}` səhnə yüklənməmişdən əvvəl verilir (ölçü və brend teması). Şriftlər: Montserrat, Caveat (Azərbaycan hərfləri daxil).
- Ölçü: `100vw × 100vh` (layihənin çıxış ölçüsü); mətn danışıqdan; rəqəm/fakt uydurma.

## Plana qoşmaq
```json
{"broll": [{"make": {"kind": "atelier", "props": {"html": "yol/səhnə.html"}}, "mode": "cover", "at": 18.2, "dur": 4.2}]}
```
Sxem: `montaj/atelier/example_hero.html` (kopya üçün yox). Müddət ≈ 0.1 s/kadr; nəticə keşlənir. Element qaydaları eynidir: fikir bitəndən sonra, ≥2 s, mövzuya funksional.

## Keyfiyyət
Bir səhnə = bir fikir. Hərəkət sakit və hamar (ease-out), 2–3 element, bol boşluq; ucuz konfeti/parıltı yox. Distinctness sualı: *bu başqa videoya da oxşayırmı?* — oxşayırsa yenidən yaz.
