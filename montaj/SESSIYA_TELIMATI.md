# Sessiya təlimatı: istifadəçi Drive linki göndərəndə (montaj paneli, əlavə xərcsiz yol)

Bu təlimat Claude Code sessiyasındakı agent üçündür. İstifadəçi iPhone-dan Drive linki
və qısa istək göndərir; montaj bu sessiyanın konteynerində `montaj.session` ilə aparılır.

Qaydalar:
- Ödənişli xidmət (API, VPS, hosting) işə salma. `ANTHROPIC_API_KEY` tələb etmə.
- Bu yolu “daimi/avtomatik AI bağlantısı” kimi təqdim etmə; konteyner müvəqqətidir.
- Müştəri mediasını, transkriptini və layihə faylını repoya commit etmə.
- Storyboard istifadəçi təsdiq etmədən `apply`/`render` etmə.
- Real material ilə yoxlanılmayan keyfiyyəti (söz sərhədi, kadraj) zəmanət kimi yazma.

Addımlar:
1. Asılılıqlar yoxdursa: `bash scripts/cloud-setup.sh`.
2. `export MONTAJ_DATA_DIR=<scratchpad>/montaj MONTAJ_OUT_DIR=<scratchpad>/montaj/out`
3. `python -m montaj.session new --title "<ad>" --link "<drive linki>" [--client "<ad>"] [--aspect 9:16] [--cut suggest] [--goal sales] [--format talking_head] [--extras subtitle]`
   - Çıxışda ölçü, kodek, HDR-i yoxla və istifadəçiyə qısa bildir.
4. `python -m montaj.session storyboard <pid>` → `storyboard.jpg` və `storyboard.md`.
   Transkripti və kartları oxu; məzmuna görə təklif hazırla (açılış, hansı hissələr qalsın,
   ekrandakı mətn) və `edit` ilə tətbiq et. Bu plan sənin (sessiyadakı Claude-un) təklifidir — belə də de.
5. `storyboard.jpg`-ni istifadəçiyə göndər (SendUserFile) + 3–6 sətirlik xülasə. Təsdiq gözlə.
6. Düzəliş istəkləri: `edit <pid> --exclude 2 --include 3 --text 1="..." --order 3,1,2 --subtitles on|off`.
7. Təsdiqdən sonra: `apply <pid>`, `render <pid>`, `export <pid>`.
8. MP4-ü özün yoxla: ölçü/fps, səs-görüntü, kəsim nöqtələrinin yaxınlığında sözlər
   (transkriptə bax), bir neçə kadr. Problemləri açıq yaz.
9. MP4 və `*.montaj.json` faylını göndər. İstifadəçiyə Drive paylaşımını yenidən “Məhdud”
   etməyi xatırlat.
