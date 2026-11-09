---
name: marketinq-sistemi
description: Aynurun marketinq/brend menecment iş sisteminin mərkəzi — bütün müştərilər (şəxsi brendlər, ekspertlər, bizneslər) və gələcək layihələr üçün. Hansı müştəri üçün işlədiyini müəyyən edir, onun brand.md/voice.md/context.md fayllarını oxuyur, tapşırığı düzgün skill-ə yönləndirir, keyfiyyət yoxlamasını və təhvil qaydalarını tətbiq edir, yeni müştəri açır. Hər müştəri işi, post, video, caption, plan, analiz, brend strategiyası və ya "yeni müştəri" sözündə ƏVVƏL bunu işlət.
---

# Marketinq sistemi

## 0. Müştərini müəyyən et
- Müştərilər: `instagram-clients/<qovluq>/` (məxfi, git-ə düşmür; əsas nüsxə Google Drive `instagram-clients`). Siyahı: `ls instagram-clients`.
- Ad çəkilməyibsə və söhbətdən aydın deyilsə — soruş. Bir müştərinin səsini, rəqəmini, planını başqasına daşıma.
- **Yeni müştəri**: `musteri-onboarding` skill-i — əvvəl Brend Anketi göndərilir, cavablar gələndə qovluq (`new_client.sh`), brand.md və Strateji paket 1 iş günündə hazırlanır.

## 1. Hər işdən əvvəl oxu (bu ardıcıllıqla)
1. `instagram-clients/<müştəri>/brand.md` — səs, vizual, qadağalar (ən üstün qaydalar).
2. `voice.md` — danışıq profili (video mətnləri üçün).
3. `context.md` / `master_context.md` / `plan_status.md` — rəylər tarixçəsi, paylaşılanlar, plan.
4. `brand.json` / `brand_kit.json` — render üçün rənglər və parametrlər.
5. Agentlik qaydaları: `instagram-clients/_agency/studiya_qaydalari.md` (montaj işi üçün).
Fayl yoxdursa: işi dayandırma, ehtiyatlı defolt götür, sonda nəyin çatışmadığını de.

## 2. Tapşırıq → skill
| Tapşırıq | Skill(lər) |
|---|---|
| Yeni müştəri onboarding (anket, strateji paket) | `musteri-onboarding` (Anket → 24 saat → Strateji paket → İş rejimi) |
| Brend strategiyası, mövqe | `personal-brand`, `brand-positioning`, `brand-messaging`, `brand-story`, `brand-identity`, `brand-guidelines`, `competitor-branding` |
| Aylıq / həftəlik plan | `ig-month`, `ig-week`, `ig-plan`, `social`, `marketing-plan` |
| Reels ssenarisi | `ig-reel` (ekspert danışıq: sakit, izahedici), `social` |
| Video montaj (Drive linki, danışıq, reklam) | `reels-pro`, `ffmpeg`, `video-edit`, `remotion-video-edit-az` |
| Post, karusel, poster, hərəkətli post | `post-studio` (+ `canvas-design`, `theme-factory`, `frontend-design`, `ig-carousel`) |
| Animasiya keyfiyyəti | `animate`, `choreograph`, `emil-design-eng` |
| Dizayn yoxlaması | `impeccable` (critique/polish), `taste-skill` |
| Caption, mətn | `ig-caption`, `copywriting`, `copy-editing`, `ig-human` |
| Story, highlight | `ig-story` |
| Şərh, DM | `ig-comment`, `ig-reply`, `ig-dm` |
| Analiz, rəqib | `ig-audit`, `ig-analiz`, `ig-viral`, `competitor-profiling`, `reverse-engineer-marketing` |
| Psixologiya, ideya | `marketing-psychology`, `ugc-strategy`, `influencer-marketing` |
| Satış mərhələsi (yalnız müştəri icazə verəndə) | `offers`, `lead-magnets`, `ad-creative`, `meta-ads` |
| Səs, musiqi, səsləndirmə | `elevenlabs`, `azure-text-to-speech`, `acestep` |

## 3. Kontent ritmi (defolt; brand.md başqa deyirsə ona əməl et)
Rollar növbə ilə, eyni rol ard-arda yox: Güldürür · Öyrədir · Göstərir · Analiz edir · Pərdə arxası · Fikir bildirir · Danışdırır (+ satışda Təklif edir). Video və statik növbələşir.

## 4. Keyfiyyət qapısı (təhvildən əvvəl)
- Vizual: `post-studio` §4 — telefon ölçüsü (390px), 1080 endə ≥24px yazı, Impeccable detektoru, kadrlara baxış.
- Mətn: klişe yox, uydurma fakt/rəqəm/sitat yox; müştərinin dilində (Azərbaycan hərfləri yoxlanır).
- Hüquq: real loqo və brend dizaynını təqlid etmə; stok CC0/PD; insan üzü yalnız razılıqla; dini simvollar/mövzu yox; müştərini lağa qoyan yumor yox.

## 5. Təhvil
- Faylları tək-tək göndər (zip yox). Qısa mesaj: nə hazırlandı, caption, nəyə diqqət (razılıq, çatışmayan fakt).
- Təhvil paylaşım icazəsi deyil. Metricool-da planlama yalnız açıq təsdiqdən sonra.
- Drive-a yalnız təsdiqlənmiş materiallar yüklənir.

## 6. Yaddaş (hər təhvildən sonra)
Müştərinin `context.md` (Aynur üçün `master_context.md`) faylına bir sətir: tarix · iş · fayl yolu · rəy. Yeni qayda yaranıbsa (məs. "dini mövzu yox"), onu `brand.md`-yə köçür — qaydalar orada yaşayır, tarixçə context-də.
