# Əlavə xidmətlər: hansı funksiya, necə qoşulur, xərc

Mənbə: rəsmi sənədlər (2026-11-07 yoxlanıb). Açar heç vaxt söhbətə yazılmır: Claude `request_credential` ilə təhlükəsiz forma açır, açar mühitin "network secret"-i kimi saxlanır və proxy onu yalnız həmin hosta göndərir.

| Xidmət | Nə verir (API) | Host · başlıq | Xərc |
|---|---|---|---|
| **ElevenLabs** (qoşulub) | TTS (Azərbaycan: yalnız eleven_v3/v4), STT Scribe (aze), musiqi, SFX | `api.elevenlabs.io` · `xi-api-key` | API dollarla/kreditlə; TTS simvol, STT audio müddəti, musiqi generasiya başına. Qalıq üçün açara `user_read` icazəsi |
| **Magnific** (keçmiş Freepik API) | Generativ video (Kling, Hailuo, WAN, Runway, Seedance), Kling Motion Control (kamera/hərəkət), OmniHuman (səslə insan), şəkil/video upscale, relight | `api.magnific.com` · `x-magnific-api-key` | Ayrıca API kreditləri; veb "Unlimited" API-ni əhatə etmir |
| **OpusClip** | Uzun videodan klip (`/api/clip-projects`) | `api.opus.pro` · `Authorization: Bearer` | Pro/Business planında "Video Editing API"; qiymət göstərilməyib |
| **HeyGen** | Avatar, fotodan video, AI clipping + altyazı, dublyaj (Azərbaycan TTS siyahıda yoxdur) | `api.heygen.com` · `X-Api-Key` | Ayrıca API planı |
| **fal.ai** | Video modelləri, upscale, reframe, TTS/STT, musiqi (marketplace) | `fal.run` · `Authorization: Key` | Əvvəlcədən ödənişli kredit, model başına |
| **Runway** | Mətn/şəkil→video, upscale, TTS, dublyaj | `api.dev.runwayml.com` · `Authorization: Bearer` + `X-Runway-Version` | Ayrıca API krediti ($0.01/kredit), video saniyə ilə |
| **Google Gemini API** | Gemini Omni Flash: 3–15 s video (Veo Gemini API-də bağlanıb) | `generativelanguage.googleapis.com` · `x-goog-api-key` | Yalnız ödənişli səviyyə, ≈$0.07/s (720p) |

Qeydlər:
- Bu mühitdə yalnız ElevenLabs açarı var. Digərləri üçün: istifadəçi açarı rəsmi paneldən yaradır → Claude `request_credential` çağırır (host yuxarıdakı cədvəldən) → açar formaya daxil edilir. Şəbəkə icazəsi açarla birlikdə verilir.
- "Fotoya pan/zoom + mətn + motion" (`photo_ad.py`) generativ AI deyil, əlavə xidmət tələb etmir. Generativ video (şəkli canlandırmaq, insanı danışdırmaq) yalnız yuxarıdakı xidmətlərdən biri qoşulanda mümkündür və ayrıca sınanmalıdır.
