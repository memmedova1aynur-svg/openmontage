# Instagram müştəriləri

Hər müştərinin Instagram hesabı üçün ayrıca qovluq. `.claude/skills/` içindəki
`ig-*` bacarıqları (`/ig-reel`, `/ig-plan`, `/ig-caption` və s.) işə
başlamazdan əvvəl hansı müştəri üçün işlədiyini müəyyən edir və yalnız həmin
müştərinin qovluğunu oxuyur.

```
instagram-clients/
  _template/        yeni müştəri üçün şablon
    brand.md        brend qaydaları: səs, vizual, qadağalar (ən üstün qaydalar)
    voice.md
    brand.json
  kafe-nergiz/      nümunə: bir müştəri = bir qovluq
    brand.md        brend qaydaları
    context.md      rəylər tarixçəsi, paylaşılanlar, növbəti addımlar
    voice.md        səs profili: kim, kimə, necə danışır, nə deyilmir
    swipe.md        /ig-viral yazır: nişdə işləyən reels-lər
    plan.md         /ig-plan yazır: həftəlik plan
    log.md          paylaşılanların və şərh yazılanların qeydi
```

`voice.md`-dən başqa faylları bacarıqlar özləri yaradır.

## Sistem

Bütün müştəri işləri `.claude/skills/marketinq-sistemi` skill-indən keçir:
müştərini müəyyən edir, `brand.md` → `voice.md` → `context.md` oxuyur,
tapşırığı uyğun skill-ə yönləndirir (ig-*, post-studio, reels-pro, brand-*,
copywriting, impeccable və s.), keyfiyyət yoxlamasını və təhvil qaydalarını
tətbiq edir, sonda rəyi `context.md`-yə yazır.

## Yeni müştəri əlavə etmək

Ən sürətli yol: `sh .claude/skills/marketinq-sistemi/scripts/new_client.sh dental-smile "Dental Smile"`

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

## Gizlilik və saxlanma

Bu repo ictimaidir, ona görə müştəri qovluqları buraya commit olunmur
(`.gitignore`). Burada yalnız bu `README.md` və `_template/` saxlanılır.

Müştəri qovluqlarının əsas nüsxəsi Google Drive-dadır: `instagram-clients`
qovluğu, hər müştəri üçün bir alt qovluq. Claude yeni sessiyada müştərinin
qovluğunu Drive-dan götürür, dəyişiklikdən sonra Drive-a geri yükləyir.
