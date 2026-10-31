# Montaj panelini telefondan açılan HTTPS ünvanına yerləşdirmək

Panel iPhone-dan işləməsi üçün daim açıq bir **server** lazımdır: video emalı,
transkripsiya, kadraj və MP4 render orada gedir. Telefon kilidlənsə də işlər
serverdə davam edir. Kompüter, eyni Wi-Fi və ya terminalı açıq saxlamaq lazım deyil.

> Bu repo yalnız **hazır yerləşdirmə paketini** verir. Server hesabı açmaq və
> ödəniş etmək sizin təsdiqinizi tələb edir — heç bir ödənişli resurs avtomatik
> yaradılmayıb.

## Nə lazımdır (maneələr)

| Lazım olan | Niyə | Kim edir |
|---|---|---|
| VPS hesabı (məs. Hetzner Cloud) | Panel və emal üçün daim açıq server | Siz — hesab + ödəniş kartı |
| Domen **və ya** pulsuz `sslip.io` ünvanı | HTTPS sertifikatı (Let's Encrypt) üçün | `sslip.io` hesab tələb etmir |
| Panel parolu | Giriş qorunması | Siz seçirsiniz |
| `ANTHROPIC_API_KEY` (istəyə bağlı) | Paneldaxili AI storyboard və caption | console.anthropic.com — ayrıca ödənişli hesab |

Bu Claude Code sessiyasındakı Claude **panelin içində işləmir** — panelin AI
hissəsi öz API açarı ilə ayrıca Anthropic hesabından istifadə edir.

## Təxmini xərc (yoxlanmalıdır)

| Xidmət | Təxmini qiymət | Qeyd |
|---|---|---|
| Hetzner CX33 (4 vCPU, 8 GB, 80 GB disk) — tövsiyə | ≈ €6,5–9 / ay + €0,50 IPv4 + ƏDV | 2026-cı ildə qiymətlər bir neçə dəfə dəyişib; mənbələr ziddiyyətlidir |
| Hetzner CX23 (2 vCPU, 4 GB) — minimum | ≈ €5,5 / ay + €0,50 IPv4 + ƏDV | Transkripsiya və render yavaş olacaq |
| Əlavə disk (Volume), lazım olsa | GB-a görə aylıq | Çoxlu 4K orijinal saxlayırsınızsa |
| Anthropic API (claude-opus-5-5) | $4 / 1M giriş token, $20 / 1M çıxış token | Bir storyboard ≈ $0,05–0,25 (token qiymətinə görə təxmin, ölçülməyib) |
| `sslip.io`, Let's Encrypt, Caddy | pulsuz | |

**Diqqət:** hetzner.com bu iş sessiyasının şəbəkəsində bağlı idi, ona görə qiymətlər
rəsmi səhifədən deyil, üçüncü tərəf mənbələrdən götürülüb. Sifarişdən əvvəl
<https://www.hetzner.com/cloud/> səhifəsində yoxlayın.

## Quraşdırma (bir dəfə, ~20 dəqiqə)

1. Hetzner Cloud-da Ubuntu 24.04 serveri yaradın (CX33). IP ünvanını qeyd edin, məs. `203.0.113.7`.
2. Serverə SSH ilə daxil olub Docker quraşdırın:
   ```bash
   curl -fsSL https://get.docker.com | sh
   git clone https://github.com/memmedova1aynur-svg/openmontage.git
   cd openmontage && git checkout claude/montaj-paneli-az
   cp deploy/.env.example deploy/.env
   nano deploy/.env
   ```
   `deploy/.env` faylında:
   - `MONTAJ_DOMAIN=203-0-113-7.sslip.io` (öz domeniniz varsa onu yazın)
   - `MONTAJ_PASSWORD=` — uzun parol
   - `MONTAJ_SECRET=` — `openssl rand -hex 32` nəticəsi
   - `ANTHROPIC_API_KEY=` — istəsəniz
3. İşə salın:
   ```bash
   docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build
   ```
4. iPhone-da Safari ilə `https://203-0-113-7.sslip.io` açın, parolla daxil olun.
   “Paylaş → Əsas ekrana əlavə et” ilə tətbiq kimi saxlaya bilərsiniz.

İlk transkripsiyada Whisper modeli (~0,5 GB) və ilk kadrajda üz modeli endirilir — bir dəfəlik.

## Təhlükəsizlik

- Bütün səhifələr, API və media faylları girişlə qorunur (HttpOnly + Secure cookie).
- 10 səhv parol cəhdindən sonra 10 dəqiqəlik blok.
- Açarlar yalnız `deploy/.env`-dədir; bu fayl `.gitignore`-dadır. Panel açarın yalnız
  “var / işləyir” vəziyyətini göstərir, qiymətini heç vaxt.
- Müştəri videoları `montaj-data` Docker volume-unda saxlanılır və açıq link ilə paylaşılmır.

## Yeniləmə və ehtiyat nüsxə

```bash
git pull && docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build
docker run --rm -v deploy_montaj-data:/data -v $PWD:/b alpine tar czf /b/montaj-backup.tgz /data
```
