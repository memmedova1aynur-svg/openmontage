# Sürətli yol (tək variant, qənaət rejimi)

Standart sorğu "tək variant"dırsa `storyboard`-un kontakt şəkli və `variants` önizləməsi (540p render) ötülür.
Ardıcıllıq:

```
new → storyboard --quick → framefix → voice-clean → music → choose <plan.json> → render → verify → (təsdiqdən sonra) choose <pid> --remember
```

- `storyboard --quick`: yalnız qaralama (kontakt şəkli və `storyboard.md` yoxdur); material yoxlaması qalır.
- `choose` müştəri profilinə **yazmır** (sınaq/təsdiqsiz seçim): qeyd layihədə `pendingHistory` kimi qalır.
  İstifadəçi videonu təsdiq edəndən sonra `choose <pid> --remember` onu profilin `history`-sinə yazır.
  3 variantlı axında istifadəçi artıq seçibsə: `choose <pid> <plan.json> --remember`.
- Səs balansı: plan `music.volume` və `sfx[].vol` verilməsə və ya `"auto"` olsa, `apply`/`choose` onları danışığın ölçülmüş
  səviyyəsinə görə hesablayır (musiqi danışıqdan 16 LU aşağı, SFX pik danışıq pikindən 12 dB aşağı; `montaj/premix.py`).
  Rəqəm yazılıbsa istifadəçi qərarı kimi saxlanılır. Kurs dərsində (növ 15) musiqi 22 LU aşağı.
- `render` əvvəl **preflight** işlədir (`montaj/preflight.py`, `--no-preflight` ilə söndürülür): 360p SDR proksi ilə 3–4 kadr
  (açılış, ən uzun altyazı, kart+altyazı, sonluq) → `out/<pid>/preflight.jpg`.
  Avtomatik düzəliş: interfeys zonasına düşən kart/başlıq zonadan çıxarılır; qutusuz altyazı zəif kontrastdadırsa (WCAG < 3:1
  zonanın >35%-də) qutulu altyazıya keçir. Başı örtən və ya üst-üstə düşən kartlar yalnız hesabatda — yeri əl ilə dəyiş.
  Proksi bir dəfə hazırlanır (~15 s), sonra preflight ~20 s. Proksidə rəng/kəskinlik yoxlanmır.
- `verify` yekun faylda **bir dəfə** işlədilir; `_ig.mp4` mövcud olması artıq onu çökdürmür.
