// Montaj paneli v2 — telefon axını: material → müştəri → seçimlər → storyboard → montaj → paylaş.
import { M } from './app.js';

const { $, el, api, toast, TL, S } = M;
const fmt = M.fmt;

// ---------------------------------------------------------------------------
// Ümumi köməkçilər
// ---------------------------------------------------------------------------

function errBox(e, retry) {
  const msg = e && e.message ? e.message : String(e || 'Xəta');
  return el('div', { class: 'err-box', role: 'alert' }, el('b', {}, msg),
    e && e.hint ? el('div', {}, e.hint) : null,
    retry ? el('button', { onclick: retry, style: 'margin-top:8px' }, 'Yenidən cəhd et') : null);
}

function jobErr(j) { return { message: j.error || 'İş alınmadı.', hint: j.hint || '' }; }

async function waitJob(id, onProgress) {
  for (;;) {
    let j;
    try { j = await api(`/api/jobs/${id}`); } catch (e) {
      if (e.status === 404) throw e;
      await new Promise((r) => setTimeout(r, 2000));
      continue;
    }
    if (onProgress) onProgress(j);
    if (!['running', 'queued'].includes(j.status)) return j;
    await new Promise((r) => setTimeout(r, 1000));
  }
}

/** Redaktorda açıq olmayan layihəni serverdə dəyişmək (versiya ilə). */
async function patchProject(pid, fn) {
  for (let i = 0; i < 3; i++) {
    const p = await api(`/api/projects/${pid}`);
    const next = fn(TL.migrate(p));
    try {
      return await api(`/api/projects/${pid}`, { method: 'PUT', body: JSON.stringify({ project: next, baseRevision: p.revision }) });
    } catch (e) { if (e.status !== 409) throw e; }
  }
  throw new Error('Layihə saxlanmadı');
}

function chip(label, on, onclick, { sys = false, disabled = false, title = '' } = {}) {
  return el('button', { type: 'button', class: `chip${sys ? ' sys' : ''}${on ? ' on' : ''}`, 'aria-pressed': on ? 'true' : 'false', disabled, title, onclick }, label);
}

function slider(label, value, min, max, step, onchange, fmtv = (v) => v) {
  const out = el('span', {}, fmtv(Number(value)));
  const inp = el('input', { type: 'range', min, max, step, value, 'aria-label': label });
  inp.oninput = () => { out.textContent = fmtv(Number(inp.value)); };
  inp.onchange = () => onchange(Number(inp.value));
  return el('div', { class: 'slider-row' }, el('span', {}, label), inp, out);
}

function fill(node, ...kids) { node.replaceChildren(...kids.flat().filter((k) => k != null && k !== false)); return node; }
const show = (id) => {
  for (const s of ['home', 'flow', 'editor']) $(`#${s}`).hidden = s !== id;
  document.querySelector('.top').classList.toggle('flow-mode', id !== 'editor');
};

// ---------------------------------------------------------------------------
// Seçimlər (bütün formatlar hamı üçün açıqdır)
// ---------------------------------------------------------------------------

const GROUPS = [
  { key: 'format', title: 'Format', items: [
    ['talking_head', 'Talking-head'], ['interview', 'Müsahibə / sual-cavab'], ['event', 'Seminar / tədbir icmalı'],
    ['product', 'Məhsul nümayişi'], ['photos', 'Şəkillərdən video'], ['voiceover_broll', 'Səsləndirmə + əlavə görüntülər'],
    ['motion', 'Motion graphics'], ['motivation', 'Motivasiya çıxarışı'], ['custom', 'Özəl'],
  ] },
  { key: 'goal', title: 'Məqsəd', items: [['sales', 'Reklam / satış'], ['education', 'Maarifləndirmə'], ['expert', 'Ekspert mövqeyi'], ['testimonial', 'Müştəri rəyi']] },
  { key: 'style', title: 'Üslub', items: [['clean', 'Sadə / təmiz'], ['dynamic', 'Dinamik'], ['editorial', 'Editorial'], ['story', 'Hekayə əsaslı'], ['graphic', 'Qrafik vurğularla']] },
  { key: 'extras', title: 'Əlavələr', items: [['subtitle', 'Subtitr'], ['music', 'Musiqi'], ['sfx', 'Səs effektləri'], ['broll', 'B-roll'], ['voiceover', 'Səsləndirmə']] },
];
const CUT_MODES = [
  ['keep', 'Olduğu kimi saxla', 'Heç nə kəsilmir; yalnız kadraj, mətn və səs əlavə olunur.'],
  ['suggest', 'Kəsimləri təklif et', 'Yalnız uzun səssizliklər çıxarılmağa təklif olunur. Nəfəs və vurğu pauzaları qalır. (Standart)'],
  ['auto', 'Avtomatik təmizlə', 'Uzun pauzalar və “ee, ıı” kimi doldurucu sözlər çıxarılır. Yenə də storyboard təsdiqindən sonra tətbiq olunur.'],
];
const ASPECTS = [['9:16', 'Reels / TikTok 9:16'], ['4:5', 'Lent 4:5'], ['1:1', 'Kvadrat 1:1'], ['16:9', 'Üfüqi 16:9'], ['source', 'Orijinal ölçü']];
const ROLE = { opening: 'Açılış', hook: 'Cəlbedici giriş', body: 'Əsas', proof: 'Sübut', cta: 'Çağırış', closing: 'Bağlanış' };

function defaultOptions() {
  return { format: [], goal: [], style: [], extras: ['subtitle'], duration: null, cutMode: 'suggest', aspect: '9:16', language: 'az', useAi: true };
}

// ---------------------------------------------------------------------------
// Axın vəziyyəti
// ---------------------------------------------------------------------------

const F = { pid: null, title: '', items: [], options: defaultOptions(), sb: null, jobId: null, status: null, alts: {} };

async function status() { if (!F.status) { try { F.status = await api('/api/status'); } catch { F.status = null; } } return F.status; }

function resetFlow() {
  Object.assign(F, { pid: null, title: '', items: [], options: defaultOptions(), sb: null, jobId: null, alts: {} });
}

let creating = null;
async function ensureProject() {
  if (F.pid) return F.pid;
  if (creating) return creating;
  creating = createProject().finally(() => { creating = null; });
  return creating;
}

async function createProject() {
  const title = F.title || `Video ${new Date().toLocaleDateString('az')}`;
  const p = await api('/api/projects', { method: 'POST', body: JSON.stringify({ title, project: TL.migrate(TL.newProject({ id: 'tmp', title })) }) });
  F.pid = p.id;
  history.replaceState(null, '', `#/p/${p.id}`);
  return p.id;
}

// ---------------------------------------------------------------------------
// 1) Material
// ---------------------------------------------------------------------------

function startFlow() {
  resetFlow();
  renderSources();
}

function itemRow(it) {
  const bar = el('div', { class: 'progress' }, Object.assign(el('span'), {}));
  bar.firstChild.style.width = `${Math.round((it.progress || 0) * 100)}%`;
  const state = it.status === 'done' ? '✓ hazırdır' : it.status === 'error' ? 'alınmadı' : `${Math.round((it.progress || 0) * 100)}%`;
  return el('li', { class: it.status === 'error' ? 'err' : '' },
    el('div', { class: 'row1' }, el('span', {}, `${it.kind === 'drive' ? 'Drive: ' : ''}${it.name}`), el('span', { class: 'muted' }, state)),
    it.status === 'error' ? null : bar,
    it.status === 'error' ? el('div', { class: 'hint' }, [it.error, it.hint].filter(Boolean).join(' ')) : null);
}

function renderSources() {
  show('flow');
  const box = $('#flow');
  const list = el('ul', { class: 'items', id: 'srcItems' }, ...F.items.map(itemRow));
  const fileIn = el('input', { type: 'file', accept: 'video/*,image/*', multiple: true, hidden: true, id: 'srcFiles' });
  fileIn.onchange = () => { const fs = [...fileIn.files]; fileIn.value = ''; for (const f of fs) addUpload(f); };
  const drv = el('textarea', { rows: 2, placeholder: 'https://drive.google.com/file/d/…', id: 'driveLinks', 'aria-label': 'Drive linkləri' });
  const busy = F.items.some((x) => !['done', 'error'].includes(x.status));
  const ok = F.items.some((x) => x.status === 'done');
  fill(box, 
    el('p', { class: 'step' }, 'Addım 1 / 4'),
    el('h1', {}, 'Material'),
    el('label', { class: 'muted', for: 'flowTitle' }, 'Layihənin adı (istəyə bağlı)'),
    Object.assign(el('input', { id: 'flowTitle', maxlength: 120, value: F.title }), { oninput: (e) => { F.title = e.target.value; } }),
    el('h2', {}, 'Telefondan'),
    el('div', { class: 'pick' }, el('label', { class: 'file-btn', for: 'srcFiles' }, '📱 Video və ya şəkil seç'), fileIn),
    el('h2', {}, 'Google Drive linki'),
    drv,
    el('p', { class: 'muted' }, 'Hər sətirdə bir link. Fayl “linki olan hər kəs” üçün açıq olmalıdır. Orijinal fayl yüklənir.'),
    el('button', { onclick: () => { const links = drv.value.split(/\s+/).filter(Boolean); drv.value = ''; for (const l of links) addDrive(l); } }, 'Linki əlavə et'),
    list,
    el('div', { class: 'actions' },
      el('button', { onclick: () => M.showHome() }, 'Ləğv et'),
      el('button', { class: 'primary', disabled: !ok, id: 'toClient', onclick: () => openClientModal() }, busy ? 'Davam (yüklənmə davam edir)' : 'Davam')));
}

function refreshItems() {
  const list = $('#srcItems');
  if (list) fill(list, ...F.items.map(itemRow));
  const btn = $('#toClient');
  if (btn) {
    btn.disabled = !F.items.some((x) => x.status === 'done');
    btn.textContent = F.items.some((x) => !['done', 'error'].includes(x.status)) ? 'Davam (yüklənmə davam edir)' : 'Davam';
  }
  const go = $('#makeSb');
  if (go) go.disabled = F.items.some((x) => !['done', 'error'].includes(x.status));
}

async function addUpload(file) {
  const it = { kind: 'upload', name: file.name, status: 'uploading', progress: 0 };
  F.items.push(it);
  refreshItems();
  let pid;
  try { pid = await ensureProject(); } catch (e) { Object.assign(it, { status: 'error', error: e.message, hint: e.hint }); refreshItems(); return; }
  await new Promise((resolve) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/projects/${pid}/media?name=${encodeURIComponent(file.name)}`);
    xhr.upload.onprogress = (ev) => { if (ev.lengthComputable) { it.progress = ev.loaded / ev.total * 0.95; refreshItems(); } };
    xhr.onload = () => {
      let d = {};
      try { d = JSON.parse(xhr.responseText); } catch { /* */ }
      if (xhr.status >= 300) Object.assign(it, { status: 'error', error: d.error || 'Yükləmə alınmadı.', hint: d.hint || 'Yenidən cəhd edin.' });
      else Object.assign(it, { status: 'done', progress: 1, media: d.media });
      refreshItems();
      resolve();
    };
    xhr.onerror = () => { Object.assign(it, { status: 'error', error: 'Şəbəkə kəsildi.', hint: 'İnterneti yoxlayıb faylı yenidən seçin. (Telefon kilidlənəndə brauzerdən yükləmə dayana bilər.)' }); refreshItems(); resolve(); };
    xhr.send(file);
  });
}

async function addDrive(link) {
  const it = { kind: 'drive', name: link.replace(/^https?:\/\//, '').slice(0, 48) + '…', status: 'queued', progress: 0 };
  F.items.push(it);
  refreshItems();
  try {
    const pid = await ensureProject();
    const { job } = await api(`/api/projects/${pid}/drive`, { method: 'POST', body: JSON.stringify({ link }) });
    it.status = 'downloading';
    const j = await waitJob(job, (x) => { it.progress = x.progress || 0; refreshItems(); });
    if (j.status === 'done') Object.assign(it, { status: 'done', progress: 1, media: j.result.media, name: j.result.media.name });
    else Object.assign(it, { status: 'error', error: j.error, hint: j.hint });
  } catch (e) { Object.assign(it, { status: 'error', error: e.message, hint: e.hint }); }
  refreshItems();
}

// ---------------------------------------------------------------------------
// 2) Müştəri seçimi
// ---------------------------------------------------------------------------

let CLIENTS = [];

function closeModal() { $('#modal').hidden = true; }
function openModal(...kids) { fill($('#modalCard'), ...kids); $('#modal').hidden = false; }
$('#modal').addEventListener('click', (e) => { if (e.target.id === 'modal') closeModal(); });

async function openClientModal() {
  try { CLIENTS = await api('/api/clients'); } catch (e) { toast(e, true); return; }
  const q = el('input', { placeholder: 'Axtar…', 'aria-label': 'Müştəri axtar', type: 'search' });
  const list = el('ul', { class: 'client-list' });
  const draw = () => {
    const s = q.value.trim().toLocaleLowerCase('az');
    fill(list, ...CLIENTS.filter((c) => !s || c.name.toLocaleLowerCase('az').includes(s) || (c.field || '').toLocaleLowerCase('az').includes(s))
      .map((c) => el('li', {}, el('button', { onclick: () => showBrand(c) },
        el('span', {}, c.name, c.field ? el('small', { class: 'muted' }, ` · ${c.field}`) : null),
        el('span', { class: 'dots' }, ...(c.colors || []).slice(0, 4).map((col) => { const d = el('i', { class: 'dot' }); d.style.background = col; return d; }))))));
  };
  q.oninput = draw;
  draw();
  openModal(el('h2', {}, 'Kimin videosudur?'), q, list,
    el('div', { class: 'row', style: 'display:flex;gap:8px;flex-wrap:wrap' },
      el('button', { onclick: () => editClient(null) }, '＋ Yeni müştəri əlavə et'),
      el('button', { onclick: () => { F.brand = null; F.clientId = null; saveBrand(null).then(() => { closeModal(); renderOptions(); }); } }, 'Birdəfəlik layihə')));
  setTimeout(() => q.focus(), 50);
}

function brandView(c) {
  const sw = (c.colors || []).length
    ? el('div', { class: 'swatches' }, ...c.colors.map((col) => { const i = el('i'); i.style.background = col; return el('span', { class: 'swatch' }, i, col); }))
    : el('p', { class: 'muted' }, 'Rəng kodları qeyd olunmayıb.');
  return el('div', { class: 'form-grid' },
    el('div', {}, el('b', {}, c.name || 'Birdəfəlik layihə'), c.field ? el('span', { class: 'muted' }, ` · ${c.field}`) : null),
    sw,
    el('div', {}, el('span', { class: 'muted' }, 'Şrift: '), c.font ? el('span', { style: `font-family:${JSON.stringify(c.font)}` }, c.font) : el('span', { class: 'muted' }, 'qeyd olunmayıb')),
    c.logo ? el('img', { class: 'brand-logo', src: `/api/logos/${encodeURIComponent(c.logo)}`, alt: 'Loqo' }) : el('p', { class: 'muted' }, 'Loqo yüklənməyib.'),
    c.preferences ? el('p', {}, el('span', { class: 'muted' }, 'Montaj üstünlükləri: '), c.preferences) : null);
}

function showBrand(c) {
  openModal(el('h2', {}, 'Müştəri'), brandView(c),
    el('div', { style: 'display:grid;gap:8px;margin-top:14px' },
      el('button', { class: 'primary', onclick: async () => { F.clientId = c.id; await saveBrand(c); closeModal(); renderOptions(); } }, 'Bu müştəri ilə davam et'),
      el('button', { onclick: () => editClient(c) }, 'Dəyişiklik et'),
      el('button', { onclick: () => openClientModal() }, '← Siyahıya qayıt')));
}

function editClient(c) {
  const isNew = !c;
  const v = c ? { ...c } : { name: '', field: '', colors: [], font: '', logo: null, preferences: '' };
  const name = el('input', { value: v.name, required: true });
  const field = el('input', { value: v.field, placeholder: 'məs. pediatriya, kosmetika' });
  const colors = el('input', { value: (v.colors || []).join(', '), placeholder: '#1A2B3C, #FFFFFF' });
  const picker = el('input', { type: 'color', 'aria-label': 'Rəng seç' });
  picker.onchange = () => { colors.value = [colors.value, picker.value.toUpperCase()].filter(Boolean).join(', '); };
  const font = el('input', { value: v.font, placeholder: 'məs. Montserrat' });
  const prefs = el('textarea', { rows: 3, placeholder: 'məs. sakit ton, subtitr həmişə, loqo sağ yuxarıda' }, v.preferences || '');
  const logoImg = el('img', { class: 'brand-logo', alt: '', hidden: !v.logo, src: v.logo ? `/api/logos/${encodeURIComponent(v.logo)}` : '' });
  const logoIn = el('input', { type: 'file', accept: 'image/png,image/jpeg,image/webp,image/svg+xml' });
  logoIn.onchange = async () => {
    const f = logoIn.files[0];
    if (!f) return;
    try {
      const r = await fetch(`/api/logos?name=${encodeURIComponent(f.name)}`, { method: 'POST', body: f });
      const d = await r.json();
      if (!r.ok) throw Object.assign(new Error(d.error), { hint: d.hint });
      v.logo = d.logo; logoImg.src = `/api/logos/${encodeURIComponent(d.logo)}`; logoImg.hidden = false;
    } catch (e) { toast(e, true); }
  };
  const collect = () => ({ name: name.value.trim(), field: field.value.trim(), colors: colors.value.split(/[,\s]+/).filter(Boolean),
    font: font.value.trim(), logo: v.logo, preferences: prefs.value.trim() });
  const err = el('div');
  const doSave = async (toProfile) => {
    const data = collect();
    try {
      let saved = { ...v, ...data };
      if (isNew) saved = await api('/api/clients', { method: 'POST', body: JSON.stringify(data) });
      else if (toProfile) saved = await api(`/api/clients/${c.id}`, { method: 'PUT', body: JSON.stringify(data) });
      else {
        // yalnız bu layihəyə: rəng formatını yoxla
        if (data.colors.some((x) => !/^#[0-9A-Fa-f]{6}$/.test(x))) throw Object.assign(new Error('Rəng kodu səhvdir.'), { hint: '#RRGGBB formatında yazın.' });
        saved.colors = data.colors.map((x) => x.toUpperCase());
      }
      F.clientId = isNew || toProfile ? saved.id : c.id;
      await saveBrand({ ...saved, appliedTo: toProfile || isNew ? 'profile' : 'project' });
      closeModal();
      toast(toProfile || isNew ? 'Müştəri profilində saxlanıldı' : 'Yalnız bu layihəyə tətbiq olundu');
      renderOptions();
    } catch (e) { fill(err, errBox(e)); }
  };
  openModal(el('h2', {}, isNew ? 'Yeni müştəri' : `${c.name} — dəyişiklik`),
    el('div', { class: 'form-grid' },
      el('label', {}, 'Ad', name), el('label', {}, 'Sahə', field),
      el('label', {}, 'Rəng kodları', colors, picker), el('label', {}, 'Şrift', font),
      el('label', {}, 'Loqo', logoIn, logoImg), el('label', {}, 'Montaj üstünlükləri', prefs)),
    el('p', { class: 'muted' }, 'Bilmədiyiniz sahəni boş saxlayın — sistem brend məlumatı uydurmur.'),
    err,
    el('div', { style: 'display:grid;gap:8px;margin-top:10px' },
      isNew ? el('button', { class: 'primary', onclick: () => doSave(true) }, 'Müştəri profilində saxla')
        : el('button', { class: 'primary', onclick: () => doSave(false) }, 'Yalnız bu layihəyə tətbiq et'),
      isNew ? null : el('button', { onclick: () => doSave(true) }, 'Müştəri profilində saxla'),
      el('button', { onclick: () => (isNew ? openClientModal() : showBrand(c)) }, 'Geri')));
}

async function saveBrand(brand) {
  F.brand = brand;
  if (!F.pid) return;
  try {
    await patchProject(F.pid, (p) => {
      p.clientId = brand && brand.id ? brand.id : null;
      p.brand = brand ? { id: brand.id || null, name: brand.name, field: brand.field, colors: brand.colors || [], font: brand.font,
        logo: brand.logo, preferences: brand.preferences, appliedTo: brand.appliedTo || 'profile' } : null;
      if (brand && brand.logo) p.branding.logo = { ...p.branding.logo, enabled: true };
      if (brand && (brand.colors || []).length) p.branding.end = { ...p.branding.end, bg: brand.colors[0] };
      if (brand && brand.preferences && !F.options.preferencesApplied) F.options.preferences = brand.preferences;
      return p;
    });
  } catch (e) { toast(e, true); }
}

// ---------------------------------------------------------------------------
// 3) Montaj seçimləri
// ---------------------------------------------------------------------------

async function renderOptions() {
  show('flow');
  const st = await status();
  const o = F.options;
  const box = $('#flow');
  const groups = GROUPS.map((g) => {
    const sel = o[g.key] || [];
    const sysOn = sel.length === 0;
    const items = g.items.map(([k, label]) => {
      let disabled = false; let title = '';
      if (g.key === 'extras' && k === 'voiceover' && !(st && st.voiceover.available)) { disabled = true; title = st ? st.voiceover.note : ''; }
      return chip(label + (disabled ? ' (qoşulmayıb)' : ''), sel.includes(k), () => {
        const cur = new Set(o[g.key] || []);
        if (cur.has(k)) cur.delete(k); else cur.add(k);
        o[g.key] = [...cur];
        renderOptions();
      }, { disabled, title });
    });
    return el('section', {}, el('h2', {}, g.title),
      el('div', { class: 'chips' }, chip('Sistem təklif etsin', sysOn, () => { o[g.key] = []; renderOptions(); }, { sys: true }), ...items));
  });
  const dur = el('input', { type: 'number', min: 3, max: 3600, step: 1, value: o.duration || '', placeholder: 'saniyə', style: 'max-width:140px', 'aria-label': 'Müddət (saniyə)' });
  dur.onchange = () => { o.duration = dur.value ? Number(dur.value) : null; renderOptions(); };
  const cut = el('div', { class: 'radio-list' }, ...CUT_MODES.map(([k, t, d]) => {
    const r = el('input', { type: 'radio', name: 'cut', value: k, checked: o.cutMode === k });
    r.onchange = () => { o.cutMode = k; renderOptions(); };
    return el('label', { class: o.cutMode === k ? 'on' : '' }, r, el('span', {}, el('b', {}, t), el('small', {}, d)));
  }));
  const aspects = el('div', { class: 'chips' }, ...ASPECTS.map(([k, t]) => chip(t, o.aspect === k, () => { o.aspect = k; renderOptions(); })));
  const aiNote = st && st.ai.keyPresent
    ? el('div', { class: 'notice ok' }, `AI: ${st.ai.model} (Anthropic Claude API) storyboard hazırlayacaq. ${st.ai.cost}`)
    : el('div', { class: 'notice' }, 'AI bağlantısı qurulmayıb: storyboard qaydalara əsaslanacaq (uzun səssizliklər, söz sərhədləri). Bu, yaradıcı AI montajı deyil — məzmunu siz seçəcəksiniz.');
  const busy = F.items.some((x) => !['done', 'error'].includes(x.status));
  fill(box, 
    el('p', { class: 'step' }, 'Addım 3 / 4'),
    el('h1', {}, 'Montaj seçimləri'),
    F.brand ? el('p', { class: 'muted' }, `Müştəri: ${F.brand.name}`) : el('p', { class: 'muted' }, 'Birdəfəlik layihə'),
    el('p', { class: 'muted' }, 'Bir neçə seçimi birlikdə edə bilərsiniz (məs. Talking-head + Reklam/satış).'),
    ...groups,
    el('h2', {}, 'Müddət'),
    el('div', { class: 'chips' }, chip('Sistem təklif etsin', !o.duration, () => { o.duration = null; renderOptions(); }, { sys: true }), dur),
    el('h2', {}, 'Kəsim rejimi'), cut,
    el('h2', {}, 'Kadr formatı'), aspects,
    aiNote,
    el('div', { class: 'actions' },
      el('button', { onclick: () => openClientModal() }, '← Müştəri'),
      el('button', { class: 'primary', id: 'makeSb', disabled: busy, onclick: () => makeStoryboard() }, 'Storyboard hazırla')));
}

async function makeStoryboard() {
  const pid = F.pid;
  try {
    const size = await api(`/api/projects/${pid}/output-size?aspect=${encodeURIComponent(F.options.aspect)}`);
    await patchProject(pid, (p) => { p.options = { ...F.options }; p.aspect = F.options.aspect; p.width = size.width; p.height = size.height; p.storyboardDraft = null; return p; });
    const { job } = await api(`/api/projects/${pid}/storyboard`, { method: 'POST', body: JSON.stringify({ options: F.options }) });
    F.jobId = job;
    renderProgress(job);
  } catch (e) { toast(e, true); }
}

// ---------------------------------------------------------------------------
// Proses göstəricisi (iş serverdə davam edir — səhifə bağlansa da)
// ---------------------------------------------------------------------------

async function renderProgress(job) {
  show('flow');
  const bar = el('div', { class: 'bigbar' }, el('span'));
  const pct = el('p', { class: 'muted' }, '0%');
  const box = $('#flow');
  fill(box, el('p', { class: 'step' }, 'Addım 4 / 4'), el('h1', {}, 'Storyboard hazırlanır'), bar, pct,
    el('p', { class: 'muted' }, 'Telefonu kilidləyə və ya səhifəni bağlaya bilərsiniz — iş serverdə davam edir. Layihəni yenidən açanda nəticə burada olacaq.'));
  let j;
  try {
    j = await waitJob(job, (x) => { bar.firstChild.style.width = `${Math.round((x.progress || 0) * 100)}%`; pct.textContent = `${Math.round((x.progress || 0) * 100)}%`; });
  } catch (e) { box.append(errBox(e, () => renderOptions())); return; }
  if (j.status !== 'done') {
    box.append(errBox(jobErr(j), async () => {
      try { const r = await api(`/api/jobs/${job}/retry`, { method: 'POST' }); renderProgress(r.job); } catch (e) { toast(e, true); }
    }), el('button', { onclick: () => renderOptions() }, 'Seçimlərə qayıt'));
    return;
  }
  const sb = await api(`/api/projects/${F.pid}/storyboard/draft`);
  F.sb = sb;
  await persistDraft();
  renderStoryboard();
}

let draftTimer = 0;
async function persistDraft() {
  clearTimeout(draftTimer);
  const sb = F.sb;
  try { await patchProject(F.pid, (p) => { p.storyboardDraft = sb; return p; }); } catch (e) { toast(e, true); }
}
function persistDraftSoon() { clearTimeout(draftTimer); draftTimer = setTimeout(persistDraft, 800); }

// ---------------------------------------------------------------------------
// 4) Vizual storyboard
// ---------------------------------------------------------------------------

function mediaOf(id) { return (F.media || []).find((m) => m.id === id); }

function croppedThumb(card, wantVertical) {
  const m = mediaOf(card.mediaId) || {};
  const fr = (F.sb.frames || {})[card.mediaId];
  const th = el('div', { class: 'thumb' + (wantVertical ? ' vert' : '') });
  if (!m.hasVideo) { th.append(el('div', { class: 'role' }, 'Səs')); return th; }
  const t = (card.srcIn + card.srcOut) / 2;
  const img = el('img', { alt: '', loading: 'lazy', src: `/api/projects/${F.pid}/media/${m.id}/frame?t=${t.toFixed(1)}&w=640` });
  const place = () => {
    const bw = th.clientWidth || 260; const bh = th.clientHeight || 146;
    const sw = m.width || 16; const sh = m.height || 9;
    if (fr && (fr.mode === 'auto' || fr.mode === 'manual')) {
      const cw = (fr.baseW || 1) * (fr.s || 1); const ch = (fr.baseH || 1) * (fr.s || 1);
      const key = (fr.keys || []).reduce((a, k) => (k.t <= t ? k : a), (fr.keys || [])[0] || { cx: 0.5, cy: 0.5 });
      const cx = Math.max(cw / 2, Math.min(1 - cw / 2, key.cx)); const cy = Math.max(ch / 2, Math.min(1 - ch / 2, key.cy));
      const k = bw / (cw * sw);
      Object.assign(img.style, { width: `${sw * k}px`, height: `${sh * k}px`, left: `${-(cx - cw / 2) * sw * k}px`, top: `${-(cy - ch / 2) * sh * k}px` });
    } else {
      const k = Math.min(bw / sw, bh / sh);
      Object.assign(img.style, { width: `${sw * k}px`, height: `${sh * k}px`, left: `${(bw - sw * k) / 2}px`, top: `${(bh - sh * k) / 2}px` });
    }
  };
  img.onload = place;
  requestAnimationFrame(place);
  th.append(img);
  if (card.onScreenText) th.append(el('div', { class: 'ost' }, card.onScreenText));
  th.append(el('div', { class: 'role' }, ROLE[card.role] || card.role || ''));
  th._place = place;
  return th;
}

function playCard(th, card) {
  const m = mediaOf(card.mediaId);
  if (!m || !m.hasVideo || m.isImage) return;
  const v = el('video', { playsinline: true, src: `/api/projects/${F.pid}/media/${m.id}?preview=1#t=${card.srcIn.toFixed(2)}` });
  const img = th.querySelector('img');
  v.style.cssText = img ? img.style.cssText : 'width:100%;height:100%;';
  if (img) img.replaceWith(v); else th.prepend(v);
  v.currentTime = card.srcIn;
  v.play().catch(() => {});
  v.ontimeupdate = () => { if (v.currentTime >= card.srcOut) { v.pause(); } };
}

function updateCard(id, patch) {
  F.sb = { ...F.sb, cards: F.sb.cards.map((c) => (c.id === id ? { ...c, ...patch, edited: true } : c)) };
  persistDraftSoon();
  renderStoryboard();
}

async function changeCard(card, alternative) {
  const ai = F.sb.generator === 'ai';
  if (!ai) {
    if (!F.alts[card.id]) {
      try {
        const r = await api(`/api/projects/${F.pid}/storyboard/card`, { method: 'POST', body: JSON.stringify({ storyboard: F.sb, cardId: card.id }) });
        F.alts[card.id] = { list: r.alternatives || [], i: -1, orig: { srcIn: card.srcIn, srcOut: card.srcOut, transcript: card.transcript, words: card.words } };
      } catch (e) { toast(e, true); return; }
    }
    if (alternative) {
      const a = F.alts[card.id];
      if (!a.list.length) { toast('Bu hissə üçün başqa variant yoxdur.'); return; }
      a.i = (a.i + 1) % (a.list.length + 1);
      const pick = a.i === a.list.length ? { ...a.orig, label: 'İlkin variant' } : a.list[a.i];
      updateCard(card.id, { srcIn: pick.srcIn, srcOut: pick.srcOut, transcript: pick.transcript, words: pick.words, altLabel: pick.label });
      return;
    }
    editCardModal(card, null);
    return;
  }
  if (alternative) return runAiCard(card, '', true);
  editCardModal(card, (instr) => runAiCard(card, instr, false));
}

async function runAiCard(card, instruction, alternative) {
  const cardEl = document.querySelector(`[data-card="${card.id}"]`);
  if (cardEl) cardEl.style.opacity = 0.5;
  try {
    const r = await api(`/api/projects/${F.pid}/storyboard/card`, { method: 'POST', body: JSON.stringify({ storyboard: F.sb, cardId: card.id, instruction, alternative }) });
    const j = await waitJob(r.job);
    if (j.status !== 'done') throw Object.assign(new Error(j.error), { hint: j.hint });
    updateCard(card.id, j.result.card);
  } catch (e) { toast(e, true); if (cardEl) cardEl.style.opacity = 1; }
}

function editCardModal(card, onAi) {
  const ost = el('input', { value: card.onScreenText || '' });
  const gr = el('input', { value: card.graphics || '' });
  const tr = el('input', { value: card.transition || '' });
  const instr = el('textarea', { rows: 3, placeholder: 'məs. “açılışda daha qısa olsun”, “mətni sual kimi yaz”' });
  openModal(el('h2', {}, 'Bu hissəni dəyiş'),
    el('div', { class: 'form-grid' }, el('label', {}, 'Ekrandakı mətn', ost), el('label', {}, 'Qrafika / vurğu', gr), el('label', {}, 'Keçid', tr)),
    el('button', { class: 'primary', style: 'width:100%;margin-top:10px', onclick: () => { closeModal(); updateCard(card.id, { onScreenText: ost.value, graphics: gr.value, transition: tr.value }); } }, 'Saxla'),
    onAi ? el('div', { class: 'form-grid', style: 'margin-top:16px' }, el('label', {}, 'Və ya AI-dən istəyin (yalnız bu kart dəyişəcək)', instr),
      el('button', { onclick: () => { closeModal(); onAi(instr.value); } }, 'AI ilə dəyiş')) : null,
    el('button', { style: 'width:100%;margin-top:10px', onclick: closeModal }, 'Bağla'));
}

async function renderStoryboard() {
  show('flow');
  const sb = F.sb;
  if (!F.media || F.mediaPid !== F.pid) { const p = await api(`/api/projects/${F.pid}`); F.media = p.media; F.mediaPid = F.pid; F.brand = p.brand; }
  const vertical = ['9:16', '4:5'].includes((sb.options || {}).aspect);
  const included = sb.cards.filter((c) => c.include);
  const total = included.reduce((a, c) => a + (c.srcOut - c.srcIn), 0);
  const gen = sb.generator === 'ai'
    ? el('div', { class: 'notice ok' }, `AI təklifi: ${sb.model}. Kartları dəyişə, alternativ istəyə və ya söndürə bilərsiniz.`)
    : el('div', { class: 'notice' }, 'Qaydalara əsaslanan təklif (AI qoşulmayıb): hissələr uzun səssizliklərə və söz sərhədlərinə görə bölünüb. Açılışı, mətni və hansı hissələrin qalacağını siz seçin.');
  const warns = [];
  const cmps = [];
  for (const [mid, fr] of Object.entries(sb.frames || {})) {
    const m = mediaOf(mid);
    for (const w of fr.warnings || []) warns.push(`${m ? m.name : ''}: ${w}`);
    if (m && m.hasVideo && (fr.mode === 'auto')) {
      const k = fr.keys[0];
      const cw = (fr.baseW || 1) * (fr.s || 1); const ch = (fr.baseH || 1) * (fr.s || 1);
      const win = el('div', { class: 'win' });
      Object.assign(win.style, { left: `${(k.cx - cw / 2) * 100}%`, top: `${(k.cy - ch / 2) * 100}%`, width: `${cw * 100}%`, height: `${ch * 100}%` });
      const t = Math.min(1, (m.duration || 1) / 2);
      cmps.push(el('div', { class: 'crop-cmp' },
        el('figure', {}, el('div', { class: 'crop-orig' }, el('img', { alt: '', src: `/api/projects/${F.pid}/media/${mid}/frame?t=${t}&w=640` }), win), el('figcaption', {}, 'Orijinal (sarı — təklif edilən kadr)')),
        el('figure', {}, croppedThumb({ mediaId: mid, srcIn: t, srcOut: t, role: '' }, vertical), el('figcaption', {}, 'Təklif edilən kadraj'))));
    }
  }
  const cards = sb.cards.map((c, i) => {
    const th = croppedThumb(c, vertical);
    const m = mediaOf(c.mediaId);
    return el('article', { class: 'sb-card' + (c.include ? '' : ' off'), 'data-card': c.id },
      th,
      el('div', { class: 'body' },
        el('div', { class: 'meta' }, `#${i + 1} · ${m ? m.name : ''} · ${fmt(c.srcIn)}–${fmt(c.srcOut)} (${(c.srcOut - c.srcIn).toFixed(1)} san)${c.altLabel ? ' · ' + c.altLabel : ''}`),
        c.transcript ? el('div', { class: 'tr' }, `“${c.transcript.slice(0, 220)}${c.transcript.length > 220 ? '…' : ''}”`) : null,
        el('dl', { class: 'kv2' },
          ...(c.onScreenText ? [el('dt', {}, 'Mətn'), el('dd', {}, c.onScreenText)] : []),
          ...(c.textStyle ? [el('dt', {}, 'Görünüş'), el('dd', {}, c.textStyle)] : []),
          ...(c.graphics ? [el('dt', {}, 'Qrafika'), el('dd', {}, c.graphics)] : []),
          ...(c.broll ? [el('dt', {}, 'B-roll'), el('dd', {}, c.broll)] : []),
          ...(c.transition ? [el('dt', {}, 'Keçid'), el('dd', {}, c.transition)] : []),
          ...(c.reason ? [el('dt', {}, 'Səbəb'), el('dd', {}, c.reason)] : []))),
      el('div', { class: 'btns' },
        el('button', { onclick: () => playCard(th, c), 'aria-label': 'Hissəni oynat' }, '▶ Önizlə'),
        el('button', { onclick: () => updateCard(c.id, { include: !c.include }) }, c.include ? 'Çıxar' : 'Daxil et'),
        el('button', { onclick: () => changeCard(c, false) }, 'Bu hissəni dəyiş'),
        el('button', { onclick: () => changeCard(c, true) }, 'Alternativ göstər')));
  });
  const box = $('#flow');
  fill(box, 
    el('p', { class: 'step' }, 'Storyboard'),
    el('h1', {}, 'Təklif olunan montaj'),
    gen,
    el('div', { class: 'sb-head' },
      el('span', { class: 'badge' }, `${included.length} hissə · ${fmt(total)}`),
      sb.options && sb.options.duration ? el('span', { class: 'badge' + (total > sb.options.duration * 1.1 ? ' warn' : '') }, `hədəf ${sb.options.duration} san`) : null,
      sb.subtitles ? el('span', { class: 'badge ok' }, 'subtitr: bəli') : el('span', { class: 'badge off' }, 'subtitr: xeyr')),
    sb.musicMood ? el('p', {}, el('b', {}, 'Musiqi: '), sb.musicMood, sb.musicNote ? ` — ${sb.musicNote}` : '') : el('p', { class: 'muted' }, 'Musiqi: lisenziyası məlum kitabxana qoşulmayıb — montajdan sonra öz musiqinizi əlavə edə bilərsiniz.'),
    sb.overallNote ? el('p', {}, sb.overallNote) : null,
    ...warns.map((w) => el('div', { class: 'notice' }, w)),
    cmps.length ? el('h2', {}, 'Kadraj: orijinal / təklif') : null, ...cmps,
    el('h2', {}, 'Hissələr'),
    el('div', { class: 'sb-cards' }, ...cards),
    el('div', { class: 'actions' },
      el('button', { onclick: () => renderOptions() }, 'Seçimlər'),
      el('button', { class: 'primary', id: 'approveSb', disabled: !included.length, onclick: () => approve() }, 'Təsdiqlə və montaja keç')));
}

async function approve() {
  const sb = F.sb;
  const pid = F.pid;
  await M.openProject(pid);
  const r = TL.applyStoryboard(S.hist.present, sb, { frames: sb.frames || {}, brand: S.hist.present.brand });
  const next = { ...r.project, storyboardDraft: null };
  M.commit(next, `Montaj hazırdır: ${r.applied} hissə${r.skipped.length ? `, ${r.skipped.length} mənbə əl ilə düzəliş səbəbindən toxunulmadı` : ''}`);
  M.seek(0);
  show('editor');
}

// ---------------------------------------------------------------------------
// Layihəni açanda doğru ekrana qayıtmaq (iş və ya storyboard varsa)
// ---------------------------------------------------------------------------

async function route(pid) {
  let p;
  try { p = await api(`/api/projects/${pid}`); } catch (e) { toast(e, true); return M.showHome(); }
  F.pid = pid; F.media = p.media; F.mediaPid = pid; F.brand = p.brand; F.options = { ...defaultOptions(), ...(p.options || {}) };
  F.items = p.media.map((m) => ({ kind: 'upload', name: m.name, status: 'done', progress: 1, media: m }));
  let jobs = [];
  try { jobs = await api(`/api/projects/${pid}/jobs`); } catch { /* */ }
  const sbJob = jobs.find((j) => j.kind === 'storyboard');
  if (sbJob && ['running', 'queued'].includes(sbJob.status)) { history.replaceState(null, '', `#/p/${pid}`); return renderProgress(sbJob.id); }
  if (p.storyboardDraft && p.storyboardDraft.status === 'draft') { F.sb = p.storyboardDraft; history.replaceState(null, '', `#/p/${pid}`); return renderStoryboard(); }
  if (sbJob && sbJob.status === 'done' && !p.storyboard && !p.clips.length) {
    try { F.sb = await api(`/api/projects/${pid}/storyboard/draft`); await persistDraft(); return renderStoryboard(); } catch { /* */ }
  }
  if (!p.clips.length && !p.options) { history.replaceState(null, '', `#/p/${pid}`); return p.media.length ? openClientModal().then(() => renderSources()) : renderSources(); }
  await M.openProject(pid);
  show('editor');
  resumeEditorJobs(jobs);
}
window.__route = route;

function resumeEditorJobs(jobs) {
  const r = jobs.find((j) => j.kind === 'render' && ['running', 'queued'].includes(j.status));
  if (r) { M.setTab('share'); watchRender(r.id); }
}

// ---------------------------------------------------------------------------
// Redaktor bölmələri: Kadraj
// ---------------------------------------------------------------------------

function selVideo() {
  const p = M.P();
  const c = S.sel && TL.clipById(p, S.sel);
  if (!c) return null;
  if (TL.trackKind(p, c) === 'video') return c;
  if (c.linkedTo) return TL.clipById(p, c.linkedTo);
  return null;
}

function clipAtPlayhead() {
  const a = TL.activeAt(M.P(), S.t);
  return a.video ? a.video.clip : null;
}

M.SIDE.frame = async function renderFrameTab() {
  const box = $('#tab-frame');
  const p = M.P();
  const aspect = p.aspect || 'source';
  const sel = el('select', { 'aria-label': 'Çıxış formatı' }, ...ASPECTS.map(([k, t]) => el('option', { value: k, selected: k === aspect }, t)));
  sel.onchange = async () => {
    try {
      const size = await api(`/api/projects/${S.pid}/output-size?aspect=${encodeURIComponent(sel.value)}`);
      M.commit({ ...TL.clone(p), aspect: sel.value, width: size.width, height: size.height }, `Format: ${sel.value === 'source' ? 'orijinal' : sel.value} (${size.width}×${size.height})`);
    } catch (e) { toast(e, true); }
  };
  const kids = [el('h3', {}, 'Kadraj'), el('div', { class: 'row' }, el('label', {}, 'Çıxış formatı'), sel),
    el('p', { class: 'muted' }, `Çıxış: ${p.width}×${p.height}. “Orijinal” düyməsini basılı saxlayaraq müqayisə edin.`)];
  const c = selVideo() || clipAtPlayhead();
  if (!c) { fill(box, ...kids, el('p', { class: 'muted' }, 'Kadrajı dəyişmək üçün video klip seçin.')); return; }
  const m = S.mediaInfo[c.media] || TL.mediaById(p, c.media);
  const fr = c.frame || null;
  const mode = fr ? fr.mode : 'none';
  kids.push(el('p', {}, el('b', {}, m.name), ` — ${mode === 'auto' ? 'avtomatik təklif' : mode === 'manual' ? 'əl ilə' : 'kəsimsiz (qara zolaqlarla sığdırılır)'}`));
  const ar = (p.width || 16) / (p.height || 9);
  const sw = m.width || 16; const sh = m.height || 9;
  const base = sw / sh > ar ? { baseW: ar * sh / sw, baseH: 1 } : { baseW: 1, baseH: (sw / ar) / sh };
  const cur = fr && fr.keys ? (fr.keys.length === 1 ? fr.keys[0] : fr.keys.reduce((a, k) => (k.t <= (TL.activeAt(p, S.t).video?.local ?? 0) ? k : a), fr.keys[0])) : { cx: 0.5, cy: 0.5 };
  const setManual = (patch) => {
    const nf = { aspect: p.aspect, mode: 'manual', s: fr?.s || 1, ...base, rotate: fr?.rotate || 0, keys: [{ t: c.srcIn, cx: cur.cx, cy: cur.cy }], warnings: [], ...patch };
    if (patch.cx != null || patch.cy != null) nf.keys = [{ t: c.srcIn, cx: patch.cx ?? cur.cx, cy: patch.cy ?? cur.cy }];
    delete nf.cx; delete nf.cy;
    M.tryOp((q) => TL.setFrame(q, c.id, nf));
  };
  if (aspect !== 'source') {
    kids.push(slider('Üfüqi yer', cur.cx, 0, 1, 0.005, (v) => setManual({ cx: v }), (v) => `${Math.round(v * 100)}%`));
    kids.push(slider('Şaquli yer', cur.cy, 0, 1, 0.005, (v) => setManual({ cy: v }), (v) => `${Math.round(v * 100)}%`));
    kids.push(slider('Yaxınlaşma', 1 / (fr?.s || 1), 1, 2, 0.01, (v) => setManual({ s: 1 / v }), (v) => `${v.toFixed(2)}x`));
  }
  kids.push(slider('Fırlatma (əyrilik)', fr?.rotate || 0, -10, 10, 0.1, (v) => setManual({ rotate: v }), (v) => `${v.toFixed(1)}°`));
  const cropPx = sh * (fr ? (fr.baseH || 1) * (fr.s || 1) : 1);
  if (fr && cropPx < p.height * 0.66) kids.push(el('div', { class: 'notice' }, `Kəsim çox kiçikdir: ${Math.round(cropPx)} px → ${p.height} px. Görüntü yumşalacaq.`));
  for (const w of fr?.warnings || []) kids.push(el('div', { class: 'notice' }, w));
  const sug = (p.storyboard && p.storyboard.frames && p.storyboard.frames[c.media]) || null;
  kids.push(el('div', { class: 'row' },
    el('button', { onclick: () => requestReframe(c, m) }, 'Avtomatik kadraj təklif et'),
    sug ? el('button', { onclick: () => M.tryOp((q) => TL.setFrame(q, c.id, sug, { manual: false }), 'Təklif edilən kadraj bərpa olundu') }, 'İlkin təklifə qaytar') : null,
    el('button', { onclick: () => M.tryOp((q) => TL.setFrame(q, c.id, null), 'Kadraj sıfırlandı (kəsimsiz)') }, 'Sıfırla')));
  kids.push(el('p', { class: 'muted' }, 'Əl ilə kadraj sabitdir (izləmə yoxdur). Mənbədə olmayan hissə uydurulmur — kənarlarda qara zolaq qalırsa, yaxınlaşdırın.'));
  fill(box, ...kids);
};

async function requestReframe(c, m) {
  const p = M.P();
  if (!p.aspect || p.aspect === 'source') { toast('Əvvəl çıxış formatını seçin (məs. 9:16).'); return; }
  try {
    await M.flushSave();
    const { job } = await api(`/api/projects/${S.pid}/reframe`, { method: 'POST', body: JSON.stringify({ mediaId: m.id, srcIn: c.srcIn, srcOut: c.srcOut, aspect: p.aspect }) });
    toast('Kadraj hesablanır…');
    const j = await waitJob(job);
    if (j.status !== 'done') throw Object.assign(new Error(j.error), { hint: j.hint });
    M.tryOp((q) => TL.setFrame(q, c.id, j.result.frame, { manual: false }), 'Avtomatik kadraj tətbiq olundu');
  } catch (e) { toast(e, true); }
}

// ---------------------------------------------------------------------------
// Görüntü (yalnız istifadəçinin seçimi ilə)
// ---------------------------------------------------------------------------

let lookAll = false;
M.SIDE.look = function renderLook() {
  const box = $('#tab-look');
  const p = M.P();
  const c = selVideo() || clipAtPlayhead();
  const kids = [el('h3', {}, 'Görüntü düzəlişləri'), el('p', { class: 'muted' }, 'Heç bir filtr avtomatik tətbiq olunmur. Dəyişikliklər render-də də görünür.')];
  const mirAll = el('input', { type: 'checkbox', checked: !!p.mirrorAll });
  mirAll.onchange = () => M.commit({ ...TL.clone(p), mirrorAll: mirAll.checked }, mirAll.checked ? 'Bütün çəkiliş güzgülənib' : 'Güzgü söndürüldü');
  kids.push(el('label', { class: 'row' }, mirAll, ' Bütün çəkilişi güzgülə (subtitr və loqo çevrilmir)'));
  if (!c) { fill(box, ...kids, el('p', { class: 'muted' }, 'Klip seçin.')); return; }
  const adj = c.adjust || {};
  const all = el('input', { type: 'checkbox', checked: lookAll });
  all.onchange = () => { lookAll = all.checked; };
  const set = (patch) => M.tryOp((q) => TL.setAdjust(q, c.id, patch, { all: lookAll }));
  const mir = el('input', { type: 'checkbox', checked: !!adj.mirror });
  mir.onchange = () => set({ mirror: mir.checked });
  kids.push(el('label', { class: 'row' }, mir, ' Bu klipi güzgülə'),
    el('label', { class: 'row' }, all, ' Dəyişikliyi bütün kliplərə tətbiq et'),
    slider('Parlaqlıq', adj.brightness || 0, -0.3, 0.3, 0.01, (v) => set({ brightness: v }), (v) => v.toFixed(2)),
    slider('Kontrast', adj.contrast ?? 1, 0.5, 1.5, 0.01, (v) => set({ contrast: v }), (v) => v.toFixed(2)),
    slider('Doyumluluq', adj.saturation ?? 1, 0, 2, 0.01, (v) => set({ saturation: v }), (v) => v.toFixed(2)),
    slider('Temperatur', adj.temperature || 6500, 3000, 10000, 100, (v) => set({ temperature: v }), (v) => `${v}K`),
    el('p', { class: 'muted' }, 'Temperaturun önizləməsi təxminidir; dəqiq nəticə render-dədir.'));
  const before = el('button', {}, 'Əvvəl / sonra (basılı saxla)');
  const on = () => { S.hideAdjust = true; M.syncPlayer(); };
  const off = () => { S.hideAdjust = false; M.syncPlayer(); };
  before.addEventListener('pointerdown', on); before.addEventListener('pointerup', off); before.addEventListener('pointerleave', off);
  kids.push(el('div', { class: 'row' }, before, el('button', { onclick: () => M.tryOp((q) => TL.resetAdjust(q, c.id, { all: lookAll }), 'Sıfırlandı') }, 'Sıfırla')));
  kids.push(el('div', { class: 'unavail' }, 'Hələ yoxdur (düymə qoyulmayıb): dəri yumşaltma və üz işığı, paltarın tündləşdirilməsi, arxa fon bulanıqlığı. Bunlar hərəkət boyunca izlənən maska tələb edir.'));
  fill(box, ...kids);
};

// ---------------------------------------------------------------------------
// Səs
// ---------------------------------------------------------------------------

M.SIDE.audio = async function renderAudio() {
  const box = $('#tab-audio');
  const p = M.P();
  const mix = { ...TL.DEFAULT_MIX, ...(p.mix || {}) };
  const st = await status();
  const setMix = (patch) => M.commit(TL.patchProject(M.P(), 'mix', patch));
  const duck = el('input', { type: 'checkbox', checked: !!mix.duck });
  duck.onchange = () => setMix({ duck: duck.checked });
  const musicIn = el('input', { type: 'file', accept: 'audio/*,video/*', hidden: true, id: 'musicIn' });
  musicIn.onchange = async () => {
    const f = musicIn.files[0]; musicIn.value = '';
    if (!f) return;
    S.sel = null;
    await M.uploadFile(f);
  };
  fill(box, el('h3', {}, 'Səs balansı'),
    slider('Danışıq', mix.speech, 0, 2, 0.05, (v) => setMix({ speech: v }), (v) => `${Math.round(v * 100)}%`),
    slider('Musiqi', mix.music, 0, 2, 0.05, (v) => setMix({ music: v }), (v) => `${Math.round(v * 100)}%`),
    slider('Səs effekti', mix.sfx, 0, 2, 0.05, (v) => setMix({ sfx: v }), (v) => `${Math.round(v * 100)}%`),
    slider('Səsləndirmə', mix.voice, 0, 2, 0.05, (v) => setMix({ voice: v }), (v) => `${Math.round(v * 100)}%`),
    el('label', { class: 'row' }, duck, ' Danışıq zamanı musiqini azalt'),
    el('p', { class: 'muted' }, 'Musiqinin hissəsini və vaxtını zaman xəttində klipin kənarlarını və yerini dəyişərək seçin.'),
    el('h3', {}, 'Musiqi'),
    el('label', { class: 'file-btn', for: 'musicIn' }, '♫ Öz musiqimi yüklə'), musicIn,
    el('div', { class: 'unavail' }, st ? st.musicLibrary.note : ''),
    el('h3', {}, 'Səsləndirmə'),
    el('div', { class: 'unavail' }, st ? st.voiceover.note : ''));
};

// ---------------------------------------------------------------------------
// Qrafika: loqo, mətn üslubu, sonluq
// ---------------------------------------------------------------------------

M.SIDE.graphics = function renderGraphics() {
  const box = $('#tab-graphics');
  const p = M.P();
  const b = p.branding || {};
  const lg = b.logo || {}; const end = b.end || {};
  const setLogo = (patch) => M.commit(TL.patchProject(M.P(), 'branding', { logo: { ...lg, ...patch } }));
  const setEnd = (patch) => M.commit(TL.patchProject(M.P(), 'branding', { end: { ...end, ...patch } }));
  const logoIn = el('input', { type: 'file', accept: 'image/png,image/jpeg,image/webp,image/svg+xml', hidden: true, id: 'logoIn' });
  logoIn.onchange = async () => {
    const f = logoIn.files[0]; logoIn.value = '';
    if (!f) return;
    try {
      const r = await fetch(`/api/logos?name=${encodeURIComponent(f.name)}`, { method: 'POST', body: f });
      const d = await r.json();
      if (!r.ok) throw Object.assign(new Error(d.error), { hint: d.hint });
      const q = TL.clone(M.P());
      q.brand = { ...(q.brand || {}), logo: d.logo, appliedTo: 'project' };
      q.branding = { ...q.branding, logo: { ...lg, enabled: true } };
      M.commit(q, 'Loqo yükləndi (yalnız bu layihə)');
    } catch (e) { toast(e, true); }
  };
  const url = M.logoUrl(p);
  const cb = (checked, fn) => { const i = el('input', { type: 'checkbox', checked: !!checked }); i.onchange = () => fn(i.checked); return i; };
  const pos = el('select', {}, ...[['top-left', 'Sol yuxarı'], ['top-right', 'Sağ yuxarı'], ['bottom-left', 'Sol aşağı'], ['bottom-right', 'Sağ aşağı'], ['center', 'Mərkəz']]
    .map(([k, t]) => el('option', { value: k, selected: (lg.position || 'top-right') === k }, t)));
  pos.onchange = () => setLogo({ position: pos.value });
  const cta = el('input', { value: end.cta || '', placeholder: 'məs. Qeydiyyat üçün yazın' });
  cta.onchange = () => setEnd({ cta: cta.value });
  const contact = el('input', { value: end.contact || '', placeholder: 'telefon, sayt, @hesab' });
  contact.onchange = () => setEnd({ contact: contact.value });
  const bg = el('input', { type: 'color', value: end.bg || '#000000' });
  bg.onchange = () => setEnd({ bg: bg.value.toUpperCase() });
  const fg = el('input', { type: 'color', value: end.color || '#FFFFFF' });
  fg.onchange = () => setEnd({ color: fg.value.toUpperCase() });
  const kids = [el('h3', {}, 'Loqo'),
    url ? el('img', { class: 'brand-logo', src: url, alt: 'Loqo' }) : el('p', { class: 'muted' }, 'Loqo yoxdur.'),
    el('label', { class: 'file-btn', for: 'logoIn' }, 'Loqo yüklə'), logoIn,
    el('label', { class: 'row' }, cb(lg.enabled, (v) => setLogo({ enabled: v })), ' Videoda loqonu göstər'),
    el('div', { class: 'row' }, el('label', {}, 'Yer'), pos),
    slider('Ölçü', lg.size || 0.18, 0.06, 0.4, 0.01, (v) => setLogo({ size: v }), (v) => `${Math.round(v * 100)}%`),
    slider('Şəffaflıq', lg.opacity ?? 1, 0.2, 1, 0.05, (v) => setLogo({ opacity: v }), (v) => `${Math.round(v * 100)}%`),
    el('h3', {}, 'Sonluq'),
    el('label', { class: 'row' }, cb(end.enabled, (v) => setEnd({ enabled: v })), ' Animasiyalı sonluq əlavə et'),
    slider('Müddət', end.duration || 3, 1, 8, 0.5, (v) => setEnd({ duration: v }), (v) => `${v} san`),
    el('label', { class: 'row' }, cb(end.showLogo !== false, (v) => setEnd({ showLogo: v })), ' Loqolu bitiş'),
    el('div', { class: 'form-grid' }, el('label', {}, 'CTA (boş qoysanız göstərilmir)', cta), el('label', {}, 'Əlaqə məlumatı (boş qoysanız göstərilmir)', contact)),
    el('div', { class: 'row' }, el('label', {}, 'Fon'), bg, el('label', {}, 'Mətn'), fg),
    el('p', { class: 'muted' }, 'Sonluğu önizləmək üçün videonun sonuna keçin.')];
  const c = S.sel && TL.clipById(p, S.sel);
  if (c && TL.trackKind(p, c) === 'text') {
    const colors = (p.brand && p.brand.colors) || [];
    kids.push(el('h3', {}, 'Seçilmiş mətnin rəngi'),
      el('div', { class: 'chips' }, ...['#FFFFFF', '#000000', ...colors].map((col) => {
        const bt = el('button', { class: 'chip', title: col, onclick: () => M.tryOp((q) => { const r = TL.clone(q); const x = TL.clipById(r, c.id); x.color = col; x.manual = true; return r; }) }, col);
        bt.style.borderColor = col; return bt;
      })),
      el('div', { class: 'chips', style: 'margin-top:8px' }, ...['', ...colors].map((col) =>
        el('button', { class: 'chip', onclick: () => M.tryOp((q) => { const r = TL.clone(q); const x = TL.clipById(r, c.id); x.bg = col ? `${col}@0.85` : null; x.manual = true; return r; }) }, col ? `Fon ${col}` : 'Standart fon'))));
  }
  if (p.brand && p.brand.font) kids.push(el('p', { class: 'muted' }, `Brend şrifti: ${p.brand.font}. Render hazırda standart şriftlə (DejaVu Sans) aparılır — şrift faylı yüklənməyib.`));
  fill(box, ...kids);
};

// ---------------------------------------------------------------------------
// Paylaş: render, cover, caption, paylaşma menyusu
// ---------------------------------------------------------------------------

const SH = { render: null, blob: null, file: null, jobId: null, progress: 0, err: null, coverT: 0 };

async function watchRender(job) {
  SH.jobId = job; SH.err = null;
  const j = await waitJob(job, (x) => { SH.progress = x.progress || 0; if (S.tab === 'share') M.SIDE.share(); });
  SH.jobId = null;
  if (j.status === 'done') { SH.render = j.result; SH.blob = null; SH.file = null; prefetch(); } else SH.err = jobErr(j);
  if (S.tab === 'share') M.SIDE.share();
}

async function prefetch() {
  // iOS Safari: paylaşma düyməsinə toxunanda fayl hazır olmalıdır (istifadəçi jesti itməsin)
  if (!SH.render) return;
  try {
    const r = await fetch(SH.render.url);
    const b = await r.blob();
    SH.blob = b;
    SH.file = new File([b], SH.render.file, { type: 'video/mp4' });
    if (S.tab === 'share') M.SIDE.share();
  } catch { /* yüklənmədi — “MP4 endir” işləyir */ }
}

async function startRender() {
  if (!(await M.flushSave())) { toast('Layihə saxlanmadı — yenidən yoxlayın', true); return; }
  try {
    const { job } = await api(`/api/projects/${S.pid}/render`, { method: 'POST', body: JSON.stringify({ revision: S.revision }) });
    SH.render = null; SH.progress = 0;
    M.SIDE.share();
    watchRender(job);
  } catch (e) { SH.err = e; M.SIDE.share(); }
}

M.SIDE.share = async function renderShare() {
  const box = $('#tab-share');
  const p = M.P();
  if (!SH.render && !SH.jobId && SH.pid !== S.pid) {
    SH.pid = S.pid;
    try {
      const rs = await api(`/api/projects/${S.pid}/renders`);
      const want = `montaj_r${S.revision}_`;
      const cur = rs.find((r) => r.file.startsWith(want));
      if (cur) { SH.render = { ...cur, revision: S.revision }; prefetch(); }
    } catch { /* */ }
  }
  const kids = [el('h3', {}, 'Son nəticə')];
  const stale = SH.render && Number(SH.render.revision) !== Number(S.revision);
  if (SH.jobId) {
    const bar = el('div', { class: 'bigbar' }, el('span'));
    bar.firstChild.style.width = `${Math.round(SH.progress * 100)}%`;
    kids.push(el('p', {}, 'MP4 hazırlanır'), bar, el('p', { class: 'muted' }, `${Math.round(SH.progress * 100)}% — telefonu kilidləsəniz də serverdə davam edir.`));
  } else if (!SH.render || stale) {
    if (SH.err) kids.push(errBox(SH.err));
    kids.push(el('p', { class: 'muted' }, stale ? 'Son düzəlişlərdən sonra yeni MP4 lazımdır. Render orijinal fayllardan yenidən hazırlanır.' : 'MP4 hələ hazırlanmayıb.'),
      el('button', { class: 'primary big', onclick: startRender }, 'MP4 hazırla'));
  }
  if (SH.render && !SH.jobId) {
    const v = el('video', { class: 'share-video', src: SH.render.url, controls: true, playsinline: true, preload: 'metadata' });
    const cover = el('img', { class: 'cover-img', alt: 'Cover', src: `${SH.render.url}/cover?t=${SH.coverT}` });
    const coverRange = el('input', { type: 'range', min: 0, max: Math.max(1, Math.floor(M.totalDur(p))), step: 0.5, value: SH.coverT, 'aria-label': 'Cover anı' });
    coverRange.onchange = () => { SH.coverT = Number(coverRange.value); cover.src = `${SH.render.url}/cover?t=${SH.coverT}`; v.currentTime = SH.coverT; };
    const cap = el('textarea', { rows: 6, placeholder: 'Caption…', 'aria-label': 'Caption' }, p.caption || '');
    cap.onchange = () => M.commit({ ...TL.clone(M.P()), caption: cap.value });
    const st = await status();
    const capBtn = el('button', { disabled: !(st && st.ai.keyPresent) }, 'AI ilə caption təklif et');
    capBtn.onclick = async () => {
      capBtn.disabled = true;
      try {
        await M.flushSave();
        const { job } = await api(`/api/projects/${S.pid}/caption`, { method: 'POST' });
        const j = await waitJob(job);
        if (j.status !== 'done') throw Object.assign(new Error(j.error), { hint: j.hint });
        const text = `${j.result.caption}\n\n${(j.result.hashtags || []).map((h) => (h.startsWith('#') ? h : `#${h}`)).join(' ')}`.trim();
        cap.value = text;
        M.commit({ ...TL.clone(M.P()), caption: text }, 'Caption təklifi hazırdır — yoxlayıb redaktə edin');
      } catch (e) { toast(e, true); }
      capBtn.disabled = false;
    };
    const copy = el('button', { onclick: async () => {
      try { await navigator.clipboard.writeText(cap.value); toast('Caption kopyalandı'); } catch { cap.select(); document.execCommand('copy'); toast('Caption kopyalandı'); }
    } }, 'Caption-u kopyala');
    const canShare = SH.file && navigator.canShare && navigator.canShare({ files: [SH.file] });
    const shareBtn = el('button', { class: 'primary', disabled: !canShare }, SH.file ? 'Paylaş' : 'Paylaş (fayl hazırlanır…)');
    shareBtn.onclick = async () => {
      try {
        try { await navigator.clipboard.writeText(cap.value); } catch { /* */ }
        await navigator.share({ files: [SH.file] });
      } catch (e) { if (e && e.name !== 'AbortError') toast({ message: 'Paylaşma menyusu açılmadı.', hint: '“MP4 endir” ilə faylı saxlayın.' }, true); }
    };
    kids.push(v,
      el('h3', {}, 'Cover'), el('div', { class: 'row' }, cover, coverRange),
      el('a', { href: `${SH.render.url}/cover?t=${SH.coverT}`, download: 'cover.jpg' }, 'Cover-i yüklə'),
      el('p', { class: 'muted' }, 'Instagram cover-i avtomatik qəbul etmir: Instagram-da “Cover” bölməsindən bu şəkli seçin.'),
      el('h3', {}, 'Caption'), cap,
      st && st.ai.keyPresent ? null : el('p', { class: 'muted' }, 'AI caption üçün serverdə ANTHROPIC_API_KEY lazımdır. Caption-u özünüz yaza bilərsiniz.'),
      el('div', { class: 'row' }, capBtn, copy),
      el('div', { class: 'share-btns' },
        shareBtn,
        el('a', { href: 'instagram://app', onclick: () => { try { navigator.clipboard.writeText(cap.value); } catch { /* */ } } }, 'Instagram-ı aç'),
        el('a', { href: `${SH.render.url}?download=1`, download: SH.render.file }, 'MP4 endir'),
        el('button', { onclick: startRender }, 'Yenidən hazırla')),
      el('p', { class: 'muted' }, '“Paylaş” iPhone-un paylaşma menyusunu açır; videonu hara göndərəcəyinizi siz seçirsiniz. Caption avtomatik ötürülmür — paylaşmadan əvvəl panoya kopyalanır. “Instagram-ı aç” yalnız tətbiqi açır, videonu ötürmür; panel Instagram-da hansı hesabın aktiv olduğunu bilmir.'),
      canShare === false && SH.file ? el('div', { class: 'notice' }, 'Bu brauzer fayl paylaşmanı dəstəkləmir. “MP4 endir” istifadə edin.') : null);
  }
  try {
    const conv = await api(`/api/projects/${S.pid}/conversions`);
    kids.push(el('h3', {}, 'Keyfiyyət və çevrilmələr'), el('ul', {}, ...conv.items.map((x) => el('li', { class: 'muted' }, x))));
  } catch { /* */ }
  fill(box, ...kids);
};

// ---------------------------------------------------------------------------
// Diaqnostika
// ---------------------------------------------------------------------------

async function showDiag() {
  show('flow');
  const box = $('#flow');
  fill(box, el('h1', {}, 'Diaqnostika'), el('p', { class: 'muted' }, 'Texniki qeydlər. Problem olarsa bu məlumatı göndərin.'));
  try {
    const [d, st] = await Promise.all([api('/api/diag'), api('/api/status')]);
    const chk = el('button', {}, 'AI açarını yoxla');
    const res = el('span', { class: 'muted' });
    chk.onclick = async () => { const r = await api('/api/ai/check', { method: 'POST' }); res.textContent = r.ok ? ` İşləyir (${r.model})` : ` ${r.reason}`; };
    box.append(
      el('pre', { class: 'logs' }, JSON.stringify({ ffmpeg: d.ffmpeg, python: d.python, jobsRunning: d.jobsRunning, status: st }, null, 2)),
      el('div', { class: 'row' }, chk, res),
      el('h2', {}, 'Son qeydlər'),
      el('pre', { class: 'logs' }, d.logs.slice().reverse().map((l) => `${new Date(l.t * 1000).toLocaleString('az')} [${l.level}] ${l.msg}${l.detail ? ' — ' + l.detail : ''}${l.trace ? '\n' + l.trace : ''}`).join('\n') || 'Qeyd yoxdur.'),
      el('button', { onclick: () => M.showHome() }, '← Geri'));
  } catch (e) { box.append(errBox(e)); }
}

// ---------------------------------------------------------------------------
// Bağlantılar
// ---------------------------------------------------------------------------

$('#btnNew').onclick = startFlow;
$('#btnDiag').onclick = showDiag;
$('#btnLogout').onclick = async () => { await api('/api/logout', { method: 'POST' }).catch(() => {}); location.href = '/login'; };
$('#btnRender').onclick = () => M.setTab('share');
const cmp = $('#btnCompare');
const cmpOn = () => { S.compareOriginal = true; M.syncPlayer(); };
const cmpOff = () => { S.compareOriginal = false; M.syncPlayer(); };
cmp.addEventListener('pointerdown', cmpOn); cmp.addEventListener('pointerup', cmpOff); cmp.addEventListener('pointerleave', cmpOff);
window.addEventListener('resize', () => { if (!$('#flow').hidden && F.sb) document.querySelectorAll('.thumb').forEach((t) => t._place && t._place()); });

const m = location.hash.match(/^#\/p\/([a-z0-9_-]+)/);
if (m) route(m[1]); else M.showHome();
