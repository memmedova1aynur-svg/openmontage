# Instagram müştəriləri

Hər müştərinin Instagram hesabı üçün ayrıca qovluq. `.claude/skills/` içindəki
`ig-*` bacarıqları (`/ig-reel`, `/ig-plan`, `/ig-caption` və s.) işə
başlamazdan əvvəl hansı müştəri üçün işlədiyini müəyyən edir və yalnız həmin
müştərinin qovluğunu oxuyur.

```
instagram-clients/
  _template/        yeni müştəri üçün şablon
    voice.md
  kafe-nergiz/      nümunə: bir müştəri = bir qovluq
    voice.md        səs profili: kim, kimə, necə danışır, nə deyilmir
    swipe.md        /ig-viral yazır: nişdə işləyən reels-lər
    plan.md         /ig-plan yazır: həftəlik plan
    log.md          paylaşılanların və şərh yazılanların qeydi
```

`voice.md`-dən başqa faylları bacarıqlar özləri yaradır.

## Yeni müştəri əlavə etmək

1. `_template/` qovluğunu kopyalayın və müştərinin adını verin: kiçik hərflərlə,
   boşluq əvəzinə defis (`dental-smile`, `kafe-nergiz`).
2. `voice.md`-ni doldurun. Daha asan yol: Claude-a müştərinin üç reels-ini və ya
   paylaşımını göndərib "dental-smile üçün voice.md yaz" deyin.

Və ya sadəcə Claude-a deyin: "yeni müştəri: Dental Smile, Bakıda stomatologiya
klinikası". Qovluğu özü yaradacaq.

## İstifadə

Sorğuda müştərinin adını çəkin: "kafe-nergiz üçün reel yaz", "dental-smile üçün
həftəni planla". Ad çəkilməsə, Claude soruşacaq.

Bir söhbətdə bir neçə müştəri ilə işləmək olar, amma böyük iş (həftəlik plan,
bir neçə reel) üçün hər müştəriyə ayrıca söhbət açmaq daha etibarlıdır.

## Gizlilik

Bu qovluq git repozitoriyasındadır. Müştərilərin şəxsi məlumatlarını, parollarını
və ya ictimai olmayan rəqəmlərini buraya yazmazdan əvvəl repoya kimlərin baxa
bildiyini yoxlayın.
