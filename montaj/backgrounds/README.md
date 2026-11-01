# Fon kitabxanası

Arxa fonun dəyişdirilməsi (`bg`, IS_AXINI.md 3c) üçün şəkillər. Şəkilləri istifadəçi verib (studiya/interyer fonları).
Ekspertin olmadığı real məkanı həqiqi kimi göstərmək üçün işlədilmir.

- Əlavə etmək: `python -m montaj.session bg-lib add <şəkillər> --tag interyer --tag ayaqüstə`
- Siyahı: `python -m montaj.session bg-lib list`
- Teqlər: `ayaqüstə` (döşəməsi görünür — tam boy danışan üçün), `oturan` (divar/rəf planı), `studiya`, `interyer`.
- `index.json` avtomatik yazılır (parlaqlıq, rəng temperaturu, qarışıqlıq) — `bg --auto` bununla seçir.
