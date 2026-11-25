# Creative Brief — hər videodan əvvəl 1 dəqiqəlik qərar kartı

**Nə vaxt:** hər yeni videoda, montaj planından ƏVVƏL. Transkript və analiz artıq keşdədirsə yenidən analiz etmə.
**Çıxış:** aşağıdakı kart (≤ 15 sətir, ≈200 token). Uzun esse yazma. Kartı layihə qeydinə yaz, repoya YOX
(müştəri transkripti/mətni commit olunmur).
**Mənbə sırası:** (1) istifadəçinin sorğusu və müştəri profili (`templates/expert-reels/experts/<ad>.json`: rəng ailəsi,
animasiya məhdudiyyətləri, `history`, `approved`/`rejected`); (2) keşlənmiş transkript; (3) yalnız qalanı özün qərarlaşdır.
Profildəki təsdiqlənmiş qaydalar (məs. "animasiya yoxdur", "fon bulanıqlaşdırılmır") kartdan üstündür.

## Kart
```
mövzu:        1 cümlə (transkriptdən)
məqsəd:       maarifləndirmə | reklam/satış | təlimə dəvət | hekayə | atmosfer
auditoriya:   kim, nə bilir, nə istəyir (profildən; uydurma)
ton:          sakit-etibarlı | enerjili | emosional | ciddi | yumşaq-mehriban
danışıq ritmi: sürətli | orta | yavaş, pauzalı  (pauzaların neçəsi vurğu/anlama pauzasıdır — bax: ritm qeydi)
kateqoriya:   VIDEO_TYPES növü (M01…M14) + reklam/maarifləndirici
vizual istiqamət: 1 cümlə (təmiz | qrafik | sənədli | premium-minimal …); brend = aksent, görüntü rəngi deyil
konsept:      videonun bir cümləlik montaj ideyası (məs. "sual → cavab → sübut")
hook:         → skills/creative/hook-design.md ilə seçilmiş üsul + səbəb + ilk 1–3 s planı
musiqi:       standart VAR (istisna yalnız istifadəçi bu müştəri/video üçün "yox" deyibsə); janr/enerji + səbəb
b-roll:       lazımdır/yox; lazımdırsa → broll-function.md (hər biri funksiya + fikir ilə)
tipoqrafiya:  → caption-typography.md (rollar: altyazı / hook / vurğu / CTA)
səs dizaynı:  SFX yalnız əsaslandırılmış yerlərdə; hər SFX bir effektə bağlıdır
retention:    məzmuna bağlı nöqtələr (vurğulu fikir, rəqəm, keçid); mexaniki "hər N s" YOX
CTA:          yox | var (mətn/kanal YALNIZ təsdiqlənmiş mənbədən: profil, danışıq, istifadəçi)
```

## Qərar qaydaları
- **Məqsəd reklamdırsa** `ad-editing.md` + montajın faydanı/təklifi vizual təqdim etməsi; məlumat videosu kimi qurma.
- **Müxtəliflik:** kartın `vizual istiqamət`, `hook`, `konsept` sahələri müştərinin son 3 videosundan (`history`) fərqlənsin.
  Brend ailəsi sabit qalır; icra mövzudan mövzuya dəyişir. Rədd edilmiş üsullar (`rejected`) təkrarlanmır.
- **Pauza (istifadəçi qaydası):** pauza vurğu yaradırsa və ya fikri anlamağa vaxt verirsə saxlanır. Yalnız ritmi pozan
  boş gözləmə, alınmayan cəhd, təkrar çıxarılır. Saniyə həddi ilə mexaniki kəsmə yoxdur.
- **Fərziyyə qaydası:** kartdakı hər "güman" `?` ilə işarələnir və təsdiqsiz daimi qayda olmur.
- **Ölçü:** kart yazmaq montaj vaxtını artırmamalıdır; profil və keş varsa sahələrin çoxu hazır doldurulur.
- Ziddiyyət: `short-form.md`-dəki mexaniki saniyə qaydaları ("hər 1–3 s dəyişiklik", "hər 2–4 s pattern interrupt") və
  oradakı statistika cədvəlləri bu sistemdə **qayda deyil**; yalnız ümumi istiqamət kimi oxu.
