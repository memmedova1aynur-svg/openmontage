# Hook Design — ilk saniyələrin kreativ seçimi

**Məqsəd:** izləyicinin diqqətini təbii və mənalı şəkildə tutmaq. Hook yalnız "ekrana böyük yazı" deyil.
**Qayda:** hər videoda bir üsul seçilir (lazım olsa iki üsul birləşdirilir). Hamısını işlətmək məcburi deyil.
**Vacib:** danışığın sırası dəyişmir, hook əvvələ çıxarılması yalnız ayrıca təklif + istifadəçi təsdiqi ilə
(`montaj/ad.py` qaydası). Hook danışıqda demədiyi vədi/rəqəmi/nəticəni YARATMIR.

## Üsullar və seçim cədvəli
| # | Üsul | Nə vaxt uyğundur | Nə vaxt YOX | Texniki icra (mövcud) |
|---|---|---|---|---|
| 1 | Kreativ tipoqrafiya | güclü bir cümlə/söz var, səssiz baxış | cümlə uzun, mücərrəddir | `caption-typography.md` hook rolu; `fx behind` (yazı insanın arxasında) |
| 2 | Məqsədli yaxınlaşma | emosional/vurğulu ilk söz | danışan artıq yaxın planda | `zooms` / `multicam` (keyfiyyət ehtiyatı daxilində) |
| 3 | Qrafik kompozisiya | rəqəm/siyahı/müqayisə danışıqdadır | danışıqda rəqəm yoxdur | `scenes` (`mg_*`), rəqəm yalnız danışıqdan |
| 4 | Vizual metafora | mücərrəd mövzu (psixologiya, qorxu, böyümə) | real məhsul/xidmət göstərilməlidir | `broll-function.md` metafora funksiyası |
| 5 | Maraqlı real görüntü | müştəridə real material var | material zəif/uyğunsuzdur | `add-broll` real kadr |
| 6 | Gözlənilməz, mənalı keçid | tonda dəyişiklik var (sual → cavab) | səbəbsiz effekt olardı | J/L-cut, `popout` (yalnız əsaslandırılıbsa) |
| 7 | Müqayisəli görüntü | "əvvəl/sonra", "yanlış/düzgün" | müqayisə danışıqda yoxdur | `split`, `mg_compare` |
| 8 | Mətn–görüntü sinxronu | söz və hərəkət eyni anda düşür | sinxron tutulmur | söz vaxtı ilə yazı girişi (±1 kadr) |
| 9 | Pattern interrupt | monoton başlanğıc riski | video artıq dinamikdir | gözlənilməz, amma mövzuya aid kadr; təsadüfi flaş YOX |
| 10 | Vizual sual | mövzu sualdır | cavab ilk saniyədə verilir | sual yazısı + cavabın gecikməsi |
| 12 | Kamera vizörü (REC + taymkod) | ekspert 'kamera arxasından' danışır kimi, etiraf/sirr/arxa plan hook-u | adi məlumat hook-u, sakit dərs | `frame` dəsti, `hook.viewfinder=true`; yalnız yuxarı künclər, üzə toxunmur |
| 11 | Dinamik kadr başlanğıcı | enerjili reklam/hekayə | sakit ekspert/dərs (M14) | ilk kadr ən güclü anla başlayır |

## Seçim alqoritmi (≤ 30 saniyə)
1. Transkriptin ilk 15 saniyəsini və ən güclü cümləni tap (söz-söz vaxtla).
2. Kartdakı `ton`, `kateqoriya`, `material` və `rejected` ilə cədvəli süz → 2 namizəd.
3. Birini seç, səbəbi **1 cümlə** ilə yaz: *"Seçilən: X, çünki …; alternativ Y — …; səbəb rədd: …"*.
4. İlk 1–3 s planı: (a) nə görünür, (b) nə eşidilir, (c) hansı sözdə nə baş verir.
5. Sadə yoxlama: səssiz baxılanda başa düşülürmü? İlk kadr boşdur? Hook müştərinin son videosunun kopyasıdırmı?

## Anti-şablon
- Hər videoda eyni giriş (qutu + yazı + whoosh) = şablon. `history`-dəki giriş təkrarlanmasın.
- Hook yalnız brend rəngli böyük yazı olmasın; rəng aksentdir.
- Yeni üsul təsdiqlənməyibsə "sınaq" kimi qeyd et; istifadəçi bəyənənə qədər daimi qayda olmur
  (təsdiq/rədd — `approved`/`rejected` profil sahəsi).
- Sakit mövzularda (ana-körpə, psixoloji dəstək, dərs) güclü pattern interrupt yoxdur: yumşaq tipoqrafiya, real kadr, sual.
