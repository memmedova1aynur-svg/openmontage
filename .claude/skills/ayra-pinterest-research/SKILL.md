---
name: ayra-pinterest-research
description: AYRA Pinterest Creative Research — BÜTÜN müştərilər üçün cover, post, karusel, story, reklam və Instagram grid dizaynından ƏVVƏL avtomatik işə düşür. Müştəri sahəsi + auditoriya + brend + kontent məqsədinə görə ingiliscə peşəkar dizayn sorğuları qurur, Pinterest-də 15–20+ nəticəni (login/API açarı olmadan, Pinterest MCP) önizləmə ilə vizual analiz edir, 3–5 güclü referans seçir, onlardan kompozisiya/tipoqrafiya/ritm prinsiplərini çıxarır və müştərinin brendində ORİJİNAL dizayna çevirir. Pin şəkilləri yekun dizayna qoyulmur. İstifadə et: 'referans', 'ilham', 'Pinterest', 'moodboard', 'necə görünsün' və hər yeni dizayn işində.
---

# AYRA Pinterest Creative Research

İstifadəçi referans göndərməməlidir — referansı biz tapırıq. Yalnız həqiqətən çatışmayan **müştəri** məlumatı (qiymət, tarix, real fakt) üçün sual ver.

## Standart iş axını
Müştəri + mövzu → **Pinterest araşdırması** → vizual analiz → kreativ istiqamət → real material (`ayra-visual-research`) → dizayn → vizual QA (`ayra-visual-design-critic`) → nəticə.

## 1. Alət
İki yol, eyni kitabxana (`@sunkimkk/pinterest-mcp@1.2.0`, MIT, login/açar yoxdur, yalnız pinterest.com + *.pinimg.com):
- **MCP** (`.mcp.json` → `pinterest`): `pinterest_search` (`previews: N` ilə şəkillər modelə görünür), `pinterest_get_pin`, `pinterest_board_pins`, `pinterest_preview_images`, `pinterest_download`. Yeni sessiyada avtomatik yüklənir.
- **Skript** (MCP yüklənməyibsə və ya toplu iş üçün):
  ```bash
  S=.claude/skills/ayra-pinterest-research/scripts
  [ -d $S/node_modules ] || (cd $S && npm i --silent @sunkimkk/pinterest-mcp@1.2.0)
  node $S/pin_research.mjs --out <scratch>/pin/<mövzu> --n 12 "query 1" "query 2" "query 3"
  python3 $S/pin_sheet.py <scratch>/pin/<mövzu> --cols 6 --h 360     # → sheet.jpg — BAX
  ```
- `pinterest_related_pins` («more like this») Pinterest girişi tələb edir — işləmir, istifadə etmə.

## 2. Sorğu qurmaq
Müştərinin sahəsini, auditoriyasını, brend rənglərini və postun məqsədini (reach/trust/value/sales) yaz, sonra 3–6 ingiliscə peşəkar sorğu qur. Format + üslub + sahə + rəng birləşdir:
- `pink editorial instagram post design typography`, `premium personal brand instagram grid <rəng>`
- `reels cover design <rəng> typography portrait`, `instagram reels cover expert woman editorial`
- `early childhood education branding`, `parenting instagram carousel design`, `modern psychology social media design`
- `creative typography poster design`, `<obyekt> editorial product photography`
Hər mövzuya yeni sorğu yarat; siyahı ilə məhdudlaşma.

## 3. Keyfiyyət filtri
Ən az 15–20 nəticəni sheet-də nəzərdən keçir. Seçim meyarları: peşəkar qrafik dizayner işi; kompozisiya və iyerarxiya; tipoqrafiya; rəng harmoniyası; real foto estetikası; sahəyə/auditoriyaya uyğunluq; kreativlik.
Rədd et: generic Canva şablonları, pin-in özü «template pack» reklamıdırsa, AI kollajlar, keyfiyyətsiz məhsul fotosu, sahəyə uyğun olmayan (məs. moda/gecə klubu) estetika.
3–5 referans seç və hər biri üçün **bir cümlə prinsip** yaz (nəyi götürürük: «nəhəng dar şrift üst-üstə, portret sağda kəsilir»), `refs.md`-də saxla.

## 4. Referansdan dizayna
- **Kopyalama yoxdur.** Mətn, loqo, illüstrasiya, xüsusi kompozisiya bir-bir təkrarlanmır — yalnız prinsip (iyerarxiya, miqyas, ritm, foto yerləşdirmə, kontrast ideyası).
- Müştərinin brend kitini (`instagram-clients/<müştəri>/brand_kit.json`, `visual-dna.md`) üstün tut: rəng, şrift, wordmark dəyişmir.
- **Pin şəkilləri lisenziyasızdır** — yekun dizayna yalnız: müştərinin real foto/video kadrları, bizim çəkdiyimiz/qurduğumuz qrafika, `ayra-visual-research` vasitəsilə tapılmış CC0/CC BY şəkillər.
- Pin önizləmələri `scratchpad`-da qalır; repoya və müştəri Drive-ına yüklənmir.
- Müştərinin üzü dəyişdirilmir, AI ilə müştəri şəkli yaradılmır.

## 5. Yoxlama
Render et, nəticəyə bax: üzün örtülməməsi, mətnin kəsilməməsi, 3:4 grid kəsimi, Azərbaycan hərfləri (Ə ə İ ı Ş ş Ğ ğ Ç ç Ö ö Ü ü), brend rəngləri. Zəifdirsə düzəlt, sonra göndər.

## Test (16.11.2026)
`claude mcp add` ilə layihəyə əlavə olundu; smoke test 7-dən 6 keçdi (related_pins giriş tələb edir). 5 sorğu → 54 pin önizləməsi yükləndi və vizual analiz edildi; Sura üçün 3 cover + 3 post bu referanslardan quruldu.
