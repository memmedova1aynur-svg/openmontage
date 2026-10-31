// Montaj paneli — brauzer tətbiqi.
import * as TL from './timeline.js';

const $ = (s) => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) n.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null) n.append(k.nodeType ? k : document.createTextNode(String(k)));
  return n;
};

const S = {
  pid: null,
  hist: null, // TL.History
  draft: null, // sürükləmə zamanı müvəqqəti layihə
  revision: 0, // serverdə saxlanmış versiya
  dirty: false,
  saving: false,
  saveTimer: null,
  sel: null,
  t: 0,
  playing: false,
  pps: 60, // piksel / saniyə
  mediaInfo: {}, // serverdən: preview, peaks
  peaks: {},
  status: null,
  tab: 'inspector',
  transcripts: {},
  jobs: {},
  renders: [],
};

const P = () => S.draft || S.hist.present;
const fmt = (t) => {
  t = Math.max(0, t || 0);
  const m = Math.floor(t / 60);
  const s = t - m * 60;
  return `${m}:${s.toFixed(2).padStart(5, '0')}`;
};
const KIND_NAME = { video: 'Video', speech: 'Danışıq', music: 'Musiqi', sfx: 'Səs effekti', text: 'Mətn' };

function toast(msg, err = false) {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast' + (err ? ' err' : '');
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.hidden = true; }, err ? 5000 : 2600);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: opts.body && !(opts.body instanceof Blob) ? { 'Content-Type': 'application/json' } : {},
    ...opts,
  });
  let data = null;
  try { data = await res.json(); } catch { /* boş cavab */ }
  if (!res.ok) {
    const e = new Error((data && (data.detail || data.error)) || `Xəta ${res.status}`);
    e.status = res.status;
    e.data = data;
    throw e;
  }
  return data;
}

// ---------------------------------------------------------------------------
// Layihələr siyahısı / açma
// ---------------------------------------------------------------------------

async function showHome() {
  pause();
  S.pid = null;
  $('#home').hidden = false;
  $('#editor').hidden = true;
  $('#title').disabled = true;
  $('#title').value = '';
  $('#btnRender').disabled = true;
  $('#saveState').textContent = '';
  history.replaceState(null, '', '/');
  const list = $('#projectList');
  try {
    const items = await api('/api/projects');
    list.replaceChildren(...(items.length ? items.map((p) => el('li', {},
      el('a', { href: `#/p/${p.id}`, onclick: (e) => { e.preventDefault(); openProject(p.id); } },
        el('span', {}, p.title || p.id),
        el('span', { class: 'muted' }, `${p.media} media · ${p.clips} klip · ${new Date(p.updatedAt * 1000).toLocaleString('az')}`)))) :
      [el('li', { class: 'muted' }, 'Hələ layihə yoxdur.')]));
  } catch (e) {
    list.replaceChildren(el('li', { class: 'muted' }, 'Siyahı yüklənmədi: ' + e.message));
  }
}

$('#newForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = $('#newTitle').value.trim() || 'Yeni layihə';
  try {
    const p = await api('/api/projects', { method: 'POST', body: JSON.stringify({ title, project: TL.newProject({ id: 'tmp', title }) }) });
    openProject(p.id);
  } catch (err) { toast(err.message, true); }
});

function histKey(pid) { return `montaj:hist:${pid}`; }

function persistHistory() {
  try {
    const h = S.hist;
    localStorage.setItem(histKey(S.pid), JSON.stringify({
      revision: S.revision, past: h.past.slice(-40), future: h.future.slice(-40),
    }));
  } catch { /* yaddaş dolu və ya bağlıdır — vacib deyil */ }
}

async function openProject(pid) {
  let p;
  try { p = await api(`/api/projects/${pid}`); } catch (e) { toast(e.message, true); return showHome(); }
  S.pid = pid;
  S.hist = new TL.History(p, 100);
  S.revision = p.revision;
  S.sel = null;
  S.t = 0;
  S.transcripts = {};
  S.renders = [];
  // Undo tarixçəsini bərpa et (yalnız eyni versiyadan davam edirsə)
  try {
    const saved = JSON.parse(localStorage.getItem(histKey(pid)) || 'null');
    if (saved && saved.revision === p.revision) {
      S.hist.past = saved.past || [];
      S.hist.future = saved.future || [];
    }
  } catch { /* yox */ }
  for (const m of p.media) S.mediaInfo[m.id] = m;
  $('#home').hidden = true;
  $('#editor').hidden = false;
  $('#title').disabled = false;
  $('#title').value = p.title;
  $('#btnRender').disabled = false;
  history.replaceState(null, '', `#/p/${pid}`);
  setSaveState('Saxlanılıb');
  loadPeaksAll();
  pollMedia();
  renderAll();
  seek(0);
}

// ---------------------------------------------------------------------------
// Dəyişiklik, undo/redo, avtomatik saxlama
// ---------------------------------------------------------------------------

function commit(next, msg) {
  S.draft = null;
  S.hist.commit(next);
  markDirty();
  if (msg) toast(msg);
  renderAll();
  syncPlayer(true);
}

function tryOp(fn, msg) {
  try {
    commit(fn(S.hist.present), msg);
    return true;
  } catch (e) {
    toast(e.message, true);
    renderAll();
    return false;
  }
}

function markDirty() {
  S.dirty = true;
  setSaveState('Saxlanılır…');
  persistHistory();
  clearTimeout(S.saveTimer);
  S.saveTimer = setTimeout(save, 600);
}

function setSaveState(txt, err = false) {
  const n = $('#saveState');
  n.textContent = txt;
  n.classList.toggle('err', err);
}

async function save() {
  if (!S.pid || !S.dirty) return;
  if (S.saving) { clearTimeout(S.saveTimer); S.saveTimer = setTimeout(save, 400); return; }
  S.saving = true;
  S.dirty = false;
  const project = { ...S.hist.present, title: $('#title').value.trim() || S.hist.present.title };
  try {
    let res;
    try {
      res = await api(`/api/projects/${S.pid}`, { method: 'PUT', body: JSON.stringify({ project, baseRevision: S.revision }) });
    } catch (e) {
      if (e.status !== 409) throw e;
      // Tək istifadəçi rejimi: serverdəki yeni versiya yalnız media əlavəsidir — üzərinə yaz.
      res = await api(`/api/projects/${S.pid}`, { method: 'PUT', body: JSON.stringify({ project, baseRevision: null }) });
    }
    S.revision = res.revision;
    persistHistory();
    setSaveState(S.dirty ? 'Saxlanılır…' : 'Saxlanılıb ✓');
  } catch (e) {
    S.dirty = true;
    setSaveState('Saxlanmadı: ' + e.message, true);
    clearTimeout(S.saveTimer);
    S.saveTimer = setTimeout(save, 3000);
  } finally {
    S.saving = false;
  }
}

async function flushSave() {
  clearTimeout(S.saveTimer);
  for (let i = 0; i < 50 && (S.saving || S.dirty); i++) {
    if (!S.saving && S.dirty) await save();
    else await new Promise((r) => setTimeout(r, 100));
  }
  return !S.dirty;
}

window.addEventListener('beforeunload', () => {
  if (S.pid && S.dirty) {
    fetch(`/api/projects/${S.pid}`, {
      method: 'PUT', keepalive: true, headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project: S.hist.present, baseRevision: null }),
    });
  }
});

function undo() { if (S.hist.undo()) { markDirty(); renderAll(); syncPlayer(true); } }
function redo() { if (S.hist.redo()) { markDirty(); renderAll(); syncPlayer(true); } }
$('#btnUndo').onclick = undo;
$('#btnRedo').onclick = redo;
$('#btnHome').onclick = async () => { await flushSave(); showHome(); };
$('#title').addEventListener('change', () => {
  const v = $('#title').value.trim();
  if (v) commit({ ...TL.clone(S.hist.present), title: v });
});

// ---------------------------------------------------------------------------
// Media yükləmə
// ---------------------------------------------------------------------------

$('#fileInput').addEventListener('change', async (e) => {
  const files = [...e.target.files];
  e.target.value = '';
  for (const f of files) await uploadFile(f);
});

function uploadFile(file) {
  return new Promise((resolve) => {
    const bar = $('#uploadBar');
    bar.hidden = false;
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/projects/${S.pid}/media?name=${encodeURIComponent(file.name)}`);
    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable) bar.textContent = `Yüklənir: ${file.name} — ${Math.round((ev.loaded / ev.total) * 100)}%`;
    };
    xhr.onload = async () => {
      bar.hidden = true;
      let data = null;
      try { data = JSON.parse(xhr.responseText); } catch { /* */ }
      if (xhr.status >= 300) { toast((data && data.detail) || 'Yükləmə alınmadı', true); return resolve(); }
      const m = data.media;
      S.mediaInfo[m.id] = m;
      S.revision = data.revision;
      const target = m.hasVideo ? null : (selectedAudioTrack() || 'm1');
      tryOp((p) => TL.addMedia(p, m, { targetTrack: target, at: S.t }),
        m.hasVideo ? `Video əlavə olundu: ${m.name}` : `Səs “${KIND_NAME[TL.trackOf(P(), target).kind]}” qatına əlavə olundu`);
      pollMedia();
      resolve();
    };
    xhr.onerror = () => { bar.hidden = true; toast('Şəbəkə xətası — yükləmə dayandı', true); resolve(); };
    xhr.send(file);
  });
}

function selectedAudioTrack() {
  const c = S.sel && TL.clipById(P(), S.sel);
  if (!c) return null;
  const k = TL.trackKind(P(), c);
  return ['speech', 'music', 'sfx'].includes(k) ? c.track : null;
}

async function pollMedia() {
  clearTimeout(pollMedia._t);
  if (!S.pid) return;
  const pending = Object.values(S.mediaInfo).some((m) => !m.preview && !m.previewError);
  if (!pending) return;
  try {
    const p = await api(`/api/projects/${S.pid}`);
    let changed = false;
    for (const m of p.media) {
      const old = S.mediaInfo[m.id];
      if (!old || old.preview !== m.preview || old.peaks !== m.peaks) changed = true;
      S.mediaInfo[m.id] = m;
    }
    if (changed) { loadPeaksAll(); syncPlayer(true); renderSide(); }
  } catch { /* növbəti dəfə */ }
  pollMedia._t = setTimeout(pollMedia, 1500);
}

async function loadPeaksAll() {
  for (const m of Object.values(S.mediaInfo)) {
    if (m.peaks && !S.peaks[m.id]) {
      try {
        S.peaks[m.id] = await api(`/api/projects/${S.pid}/media/${m.id}/peaks`);
        renderTimeline();
      } catch { /* hələ hazır deyil */ }
    }
  }
}

function mediaUrl(mid) {
  const m = S.mediaInfo[mid];
  return `/api/projects/${S.pid}/media/${mid}${m && m.preview ? '?preview=1' : ''}`;
}

// ---------------------------------------------------------------------------
// Önizləmə pleyeri — layihə JSON-undan oxuyur (render ilə eyni məlumat)
// ---------------------------------------------------------------------------

const vid = $('#vid');
const audios = new Map(); // clipId -> HTMLAudioElement
let curVideoClip = null;
let curSrc = null;
let wallStart = 0;
let tStart = 0;
let raf = 0;

function setVideoSrc(url) {
  if (curSrc === url) return Promise.resolve();
  curSrc = url;
  vid.src = url;
  return new Promise((res) => {
    const done = () => { vid.removeEventListener('loadedmetadata', done); vid.removeEventListener('error', done); res(); };
    vid.addEventListener('loadedmetadata', done);
    vid.addEventListener('error', done);
  });
}

async function syncPlayer(force = false) {
  if (!S.pid) return;
  const p = P();
  const a = TL.activeAt(p, S.t);
  const v = a.video;
  $('#emptyHint').hidden = p.clips.length > 0;
  if (v) {
    const url = mediaUrl(v.clip.media);
    const changed = !curVideoClip || curVideoClip.id !== v.clip.id || curSrc !== url;
    curVideoClip = v.clip;
    vid.classList.remove('blank');
    if (changed || force || !S.playing) {
      S.switching = true;
      await setVideoSrc(url);
      // gözləmə müddətində vaxt irəliləyibsə, yeni yerə keç
      const now = TL.activeAt(P(), S.t).video;
      const local = now && now.clip.id === v.clip.id ? now.local : v.local;
      if (Math.abs(vid.currentTime - local) > (S.playing ? 0.12 : 0.01)) vid.currentTime = local;
      S.switching = false;
    }
    const partner = TL.partnerOf(p, v.clip);
    const linkedAudio = partner && partner.linkedTo === v.clip.id ? partner : null;
    vid.muted = !linkedAudio;
    vid.volume = linkedAudio ? Math.min(1, linkedAudio.volume ?? 1) : 0;
    if (S.playing && vid.paused) vid.play().catch(() => {});
  } else {
    curVideoClip = null;
    vid.classList.add('blank');
    if (!vid.paused) vid.pause();
  }
  // Ayrı səs klipləri (ayrılmış danışıq, musiqi, effekt)
  const want = new Set();
  for (const x of a.audio) {
    if (x.clip.linkedTo && v && x.clip.linkedTo === v.clip.id) continue;
    want.add(x.clip.id);
    let au = audios.get(x.clip.id);
    if (!au) {
      au = new Audio();
      au.preload = 'auto';
      audios.set(x.clip.id, au);
    }
    const url = mediaUrl(x.clip.media);
    if (au.dataset.src !== url) { au.dataset.src = url; au.src = url; }
    au.volume = Math.min(1, x.clip.volume ?? 1);
    if (Math.abs(au.currentTime - x.local) > (S.playing ? 0.15 : 0.02)) {
      try { au.currentTime = x.local; } catch { /* metadata hələ yox */ }
    }
    if (S.playing && au.paused) au.play().catch(() => {});
    if (!S.playing && !au.paused) au.pause();
  }
  for (const [id, au] of audios) {
    if (!want.has(id)) { au.pause(); if (!TL.clipById(p, id)) audios.delete(id); }
  }
  renderTextLayer(a.text);
}

function renderTextLayer(items) {
  const layer = $('#textLayer');
  const h = layer.clientHeight || 1;
  const p = P();
  // önizləmədə render ilə eyni nisbət: video sahəsinin hündürlüyünə görə
  const vh = Math.min(h, (layer.clientWidth || 1) * (p.height / p.width));
  layer.replaceChildren(...items.map(({ clip }) => {
    const pos = clip.position || 'bottom';
    const n = el('div', { class: 'ov' }, clip.text || '');
    n.style.fontSize = `${Math.max(10, vh * (clip.size || 0.06))}px`;
    const top = (h - vh) / 2;
    if (pos === 'top') n.style.top = `${top + vh * 0.08}px`;
    else if (pos === 'center') { n.style.top = '50%'; n.style.transform = 'translate(-50%,-50%)'; }
    else n.style.bottom = `${top + vh * 0.12}px`;
    return n;
  }));
}

function tick() {
  if (!S.playing) return;
  const p = P();
  const total = TL.duration(p);
  if (curVideoClip && !S.switching && !vid.seeking && !vid.paused && vid.readyState >= 2) {
    const lay = TL.layout(p).get(curVideoClip.id);
    if (lay) {
      S.t = lay.start + (vid.currentTime - curVideoClip.srcIn);
      if (vid.currentTime >= curVideoClip.srcOut - 0.02) {
        S.t = lay.end;
        tStart = S.t; wallStart = performance.now();
        syncPlayer();
      }
    }
    tStart = S.t; wallStart = performance.now();
  } else {
    S.t = tStart + (performance.now() - wallStart) / 1000;
    const a = TL.activeAt(p, S.t);
    if ((a.video && (!curVideoClip || a.video.clip.id !== curVideoClip.id)) || !a.video) syncPlayer();
  }
  if (S.t >= total) { S.t = total; pause(); }
  else if (tick._n++ % 10 === 0) syncPlayer();
  updatePlayhead();
  raf = requestAnimationFrame(tick);
}
tick._n = 0;

function play() {
  if (!S.pid) return;
  const total = TL.duration(P());
  if (total <= 0) return;
  if (S.t >= total - 0.01) S.t = 0;
  S.playing = true;
  tStart = S.t; wallStart = performance.now();
  $('#btnPlay').textContent = '⏸';
  syncPlayer(true);
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(tick);
}

function pause() {
  S.playing = false;
  $('#btnPlay').textContent = '▶';
  cancelAnimationFrame(raf);
  vid.pause();
  for (const au of audios.values()) au.pause();
  if (S.pid) renderTools();
}

function seek(t) {
  const total = S.pid ? TL.duration(P()) : 0;
  S.t = Math.max(0, Math.min(total, t));
  tStart = S.t; wallStart = performance.now();
  updatePlayhead();
  renderTools();
  syncPlayer(true);
}

$('#btnPlay').onclick = () => (S.playing ? pause() : play());
$('#btnBack').onclick = () => { pause(); seek(S.t - 1 / P().fps); };
$('#btnFwd').onclick = () => { pause(); seek(S.t + 1 / P().fps); };

function updatePlayhead() {
  if (!S.pid) return;
  $('#playhead').style.left = `${S.t * S.pps}px`;
  $('#timecode').textContent = `${fmt(S.t)} / ${fmt(TL.duration(P()))}`;
  if (S.playing) {
    const tl = $('#timeline');
    const x = S.t * S.pps;
    if (x < tl.scrollLeft || x > tl.scrollLeft + tl.clientWidth - 40) tl.scrollLeft = x - 40;
  }
}

// ---------------------------------------------------------------------------
// Zaman xətti
// ---------------------------------------------------------------------------

function renderAll() {
  if (!S.pid) return;
  $('#btnUndo').disabled = !S.hist.canUndo;
  $('#btnRedo').disabled = !S.hist.canRedo;
  if (S.sel && !TL.clipById(P(), S.sel)) S.sel = null;
  renderTimeline();
  renderTools();
  renderSide();
  updatePlayhead();
}

function renderTools() {
  const p = P();
  const c = S.sel && TL.clipById(p, S.sel);
  $('#tDelete').disabled = !c;
  $('#tLeft').disabled = !c;
  $('#tRight').disabled = !c;
  $('#tUnlink').disabled = !(c && TL.partnerOf(p, c));
  $('#tSplit').disabled = !splitTarget();
}

function splitTarget() {
  const p = P();
  const lay = TL.layout(p);
  const inside = (c) => { const l = lay.get(c.id); return l && S.t > l.start + TL.MIN_CLIP && S.t < l.end - TL.MIN_CLIP; };
  const c = S.sel && TL.clipById(p, S.sel);
  if (c && inside(c)) return c;
  if (c) {
    const partner = TL.partnerOf(p, c);
    if (partner && inside(partner)) return partner;
  }
  return p.clips.find((x) => TL.trackKind(p, x) === 'video' && inside(x)) || null;
}

function renderTimeline() {
  const p = P();
  const lay = TL.layout(p);
  const total = TL.duration(p);
  const width = Math.max((total + 10) * S.pps, $('#timeline').clientWidth);
  $('#tlInner').style.width = `${width}px`;
  $('#trackHeads').replaceChildren(...p.tracks.map((t) => el('div', {}, t.name)));
  // xətkeş
  const step = S.pps >= 120 ? 1 : S.pps >= 40 ? 2 : S.pps >= 15 ? 5 : 10;
  const ticks = [];
  for (let s = 0; s * S.pps < width; s += step) {
    const n = el('div', { class: 'tick' }, fmt(s).replace(/\.\d\d$/, ''));
    n.style.left = `${s * S.pps}px`;
    ticks.push(n);
  }
  $('#ruler').replaceChildren(...ticks);
  // Mövcud elementləri yerində yenilə (sürükləmə zamanı göstərici itməsin)
  const lanesBox = $('#lanes');
  if (lanesBox.children.length !== p.tracks.length) {
    lanesBox.replaceChildren(...p.tracks.map((t) => el('div', { class: 'lane', 'data-track': t.id })));
  }
  const existing = new Map([...lanesBox.querySelectorAll('.clip')].map((n) => [n.dataset.id, n]));
  const seen = new Set();
  p.tracks.forEach((t, i) => {
    const lane = lanesBox.children[i];
    for (const c of p.clips.filter((x) => x.track === t.id)) {
      seen.add(c.id);
      const old = existing.get(c.id);
      const fresh = clipEl(p, c, lay.get(c.id), t.kind);
      if (!old) { lane.append(fresh); continue; }
      if (old.parentNode !== lane) lane.append(old);
      old.className = fresh.className;
      old.title = fresh.title;
      old.style.left = fresh.style.left;
      old.style.width = fresh.style.width;
      old.style.transform = '';
      old.querySelector('.lbl').textContent = fresh.querySelector('.lbl').textContent;
      const key = fresh.dataset.wave || '';
      if ((old.dataset.wave || '') !== key) {
        old.querySelector('canvas')?.remove();
        const cv = fresh.querySelector('canvas');
        if (cv) old.prepend(cv);
        old.dataset.wave = key;
      }
    }
  });
  for (const [id, n] of existing) if (!seen.has(id)) n.remove();
}

function clipEl(p, c, l, kind) {
  const m = c.media ? S.mediaInfo[c.media] || TL.mediaById(p, c.media) : null;
  const cls = ['clip', `k-${kind}`];
  if (c.id === S.sel) cls.push('sel');
  if (TL.partnerOf(p, c)) cls.push('linked');
  if (c.manual) cls.push('manual');
  const name = kind === 'text' ? (c.text || 'Mətn') : (m ? m.name : '?');
  const n = el('div', { class: cls.join(' '), 'data-id': c.id, title: `${name} — ${fmt(TL.clipDur(c))}` },
    el('div', { class: 'lbl' }, name));
  n.style.left = `${l.start * S.pps}px`;
  n.style.width = `${Math.max(4, (l.end - l.start) * S.pps)}px`;
  if (['speech', 'music', 'sfx'].includes(kind) && S.peaks[c.media]) {
    n.append(waveCanvas(c, l));
    n.dataset.wave = `${c.srcIn}:${c.srcOut}:${S.pps}:${c.volume ?? 1}`;
  }
  n.append(el('div', { class: 'h in', 'data-edge': 'in' }), el('div', { class: 'h out', 'data-edge': 'out' }));
  return n;
}

function waveCanvas(c, l) {
  const pk = S.peaks[c.media];
  const w = Math.max(4, Math.round((l.end - l.start) * S.pps));
  const h = 40;
  const cv = el('canvas', { width: w, height: h });
  const g = cv.getContext('2d');
  g.fillStyle = 'rgba(255,255,255,.9)';
  const per = pk.perSecond;
  for (let x = 0; x < w; x++) {
    const t = c.srcIn + (x / S.pps);
    const v = pk.peaks[Math.floor(t * per)] || 0;
    const bh = Math.max(1, v * h * (c.volume ?? 1));
    g.fillRect(x, (h - bh) / 2, 1, bh);
  }
  return cv;
}

// --- Toxunma / siçan ilə idarə ---

function timeFromClientX(x) {
  const r = $('#tlInner').getBoundingClientRect();
  return (x - r.left) / S.pps;
}

$('#ruler').addEventListener('pointerdown', (e) => {
  pause();
  $('#ruler').setPointerCapture(e.pointerId);
  seek(timeFromClientX(e.clientX));
  const move = (ev) => seek(timeFromClientX(ev.clientX));
  const up = () => { $('#ruler').removeEventListener('pointermove', move); $('#ruler').removeEventListener('pointerup', up); renderTools(); };
  $('#ruler').addEventListener('pointermove', move);
  $('#ruler').addEventListener('pointerup', up);
});

$('#lanes').addEventListener('pointerdown', (e) => {
  const clipNode = e.target.closest('.clip');
  if (!clipNode) {
    // boş sahəyə toxunma -> seçimi götür və oraya keç
    if (e.target.closest('.lane')) { S.sel = null; seek(timeFromClientX(e.clientX)); renderAll(); }
    return;
  }
  const id = clipNode.dataset.id;
  const edge = e.target.dataset.edge;
  const base = S.hist.present;
  const c = TL.clipById(base, id);
  if (!c) return;
  const kind = TL.trackKind(base, c);
  if (S.sel !== id) { S.sel = id; renderTools(); renderSide(); for (const n of document.querySelectorAll('.clip.sel')) n.classList.remove('sel'); clipNode.classList.add('sel'); }
  const x0 = e.clientX;
  const touch = e.pointerType === 'touch';
  if (!edge && touch) return; // telefonda gövdə sürüşdürmə əvəzinə ◀ ▶ düymələri (scroll pozulmasın)
  e.preventDefault();
  const pid = e.pointerId;
  let moved = false;
  let dropIdx = null;
  const lay0 = TL.layout(base);
  const l0 = lay0.get(id);
  const onMove = (ev) => {
    if (ev.pointerId !== pid) return;
    const dx = ev.clientX - x0;
    if (!moved && Math.abs(dx) < 4) return;
    moved = true;
    const dt = dx / S.pps;
    try {
      if (edge) {
        const value = kind === 'text'
          ? (edge === 'in' ? l0.start + dt : l0.end + dt)
          : (edge === 'in' ? c.srcIn + dt : c.srcOut + dt);
        S.draft = TL.trim(base, id, edge, value);
        renderTimeline();
        showExtents(id);
      } else if (kind === 'video') {
        // sıra dəyişmə: göstərici hansı klipin ortasından keçib
        const t = timeFromClientX(ev.clientX);
        const seq = TL.videoClips(base).filter((x) => x.id !== id);
        dropIdx = seq.filter((x) => { const l = lay0.get(x.id); return (l.start + l.end) / 2 < t; }).length;
        const live = document.querySelector(`.clip[data-id="${id}"]`);
        if (live) { live.style.transform = `translateX(${dx}px)`; live.classList.add('dragging'); }
        showDropMark(seq, lay0, dropIdx);
      } else if (!c.linkedTo) {
        S.draft = TL.moveFree(base, id, (c.start || 0) + dt);
        renderTimeline();
      }
    } catch { /* sərhəddə — saxla */ }
  };
  const onUp = (ev) => {
    if (ev.pointerId !== pid) return;
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
    window.removeEventListener('pointercancel', onUp);
    document.querySelector('.drop-mark')?.remove();
    if (!moved) { S.draft = null; return; }
    if (edge || (kind !== 'video' && !c.linkedTo)) {
      const next = S.draft;
      S.draft = null;
      if (next) commit(next);
    } else if (kind === 'video' && dropIdx != null) {
      tryOp((p) => TL.moveVideo(p, id, dropIdx));
    } else renderAll();
  };
  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', onUp);
  window.addEventListener('pointercancel', onUp);
});

function showDropMark(seq, lay, idx) {
  let mark = document.querySelector('.drop-mark');
  if (!mark) { mark = el('div', { class: 'drop-mark' }); $('#lanes').append(mark); }
  const t = idx < seq.length ? lay.get(seq[idx].id).start : (seq.length ? lay.get(seq[seq.length - 1].id).end : 0);
  mark.style.left = `${t * S.pps}px`;
}

// Sürükləmə zamanı mənbə sərhədlərini göstər (kəsilmiş material geri qaytarıla bilər)
function showExtents(id) {
  const p = P();
  const c = TL.clipById(p, id);
  const m = c && c.media && S.mediaInfo[c.media];
  if (!m) return;
  $('#saveState').textContent = `Mənbə ${fmt(c.srcIn)} – ${fmt(c.srcOut)} / fayl ${fmt(m.duration)}`;
}

// --- Alət düymələri ---

$('#tSplit').onclick = () => {
  const c = splitTarget();
  if (c) tryOp((p) => TL.split(p, c.id, S.t), 'Bölündü');
};
$('#tDelete').onclick = () => {
  if (S.sel) tryOp((p) => TL.deleteClip(p, S.sel), 'Silindi (orijinal fayl qalır)');
};
function nudge(dir) {
  const p = P();
  const c = S.sel && TL.clipById(p, S.sel);
  if (!c) return;
  const kind = TL.trackKind(p, c);
  if (kind === 'video' || c.linkedTo) {
    const v = kind === 'video' ? c : TL.clipById(p, c.linkedTo);
    tryOp((q) => TL.moveVideo(q, v.id, v.order + dir));
  } else {
    tryOp((q) => TL.moveFree(q, c.id, (c.start || 0) + dir * 0.5));
  }
}
$('#tLeft').onclick = () => nudge(-1);
$('#tRight').onclick = () => nudge(1);
$('#tUnlink').onclick = () => { if (S.sel) tryOp((p) => TL.unlink(p, S.sel), 'Səs videodan ayrıldı — indi ayrıca hərəkət edir'); };
$('#tText').onclick = () => {
  const before = new Set(P().clips.map((c) => c.id));
  if (tryOp((p) => TL.addText(p, { start: S.t, dur: 3, text: 'Mətn' }), 'Mətn əlavə olundu')) {
    const nc = P().clips.find((c) => !before.has(c.id));
    if (nc) { S.sel = nc.id; setTab('inspector'); renderAll(); }
  }
};
$('#zIn').onclick = () => zoom(1.5);
$('#zOut').onclick = () => zoom(1 / 1.5);
function zoom(f) {
  const tl = $('#timeline');
  const center = (tl.scrollLeft + tl.clientWidth / 2) / S.pps;
  S.pps = Math.max(4, Math.min(600, S.pps * f));
  renderTimeline();
  updatePlayhead();
  tl.scrollLeft = center * S.pps - tl.clientWidth / 2;
}

document.addEventListener('keydown', (e) => {
  if (!S.pid || e.target.closest('input, textarea, select')) return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); }
  else if ((e.ctrlKey || e.metaKey) && k === 'y') { e.preventDefault(); redo(); }
  else if (k === ' ') { e.preventDefault(); S.playing ? pause() : play(); }
  else if (k === 's') $('#tSplit').click();
  else if (k === 'delete' || k === 'backspace') $('#tDelete').click();
  else if (k === 'arrowleft') { pause(); seek(S.t - 1 / P().fps); }
  else if (k === 'arrowright') { pause(); seek(S.t + 1 / P().fps); }
});

// ---------------------------------------------------------------------------
// Yan panel: Klip / Təkliflər / Media / İxrac
// ---------------------------------------------------------------------------

for (const b of document.querySelectorAll('.tabs button')) b.onclick = () => setTab(b.dataset.tab);
function setTab(tab) {
  S.tab = tab;
  for (const b of document.querySelectorAll('.tabs button')) b.classList.toggle('active', b.dataset.tab === tab);
  for (const t of ['inspector', 'ai', 'media', 'export']) $(`#tab-${t}`).hidden = t !== tab;
  renderSide();
}

function renderSide() {
  if (!S.pid) return;
  if (S.tab === 'inspector') renderInspector();
  if (S.tab === 'ai') renderAI();
  if (S.tab === 'media') renderMedia();
  if (S.tab === 'export') renderExport();
}

function renderInspector() {
  const box = $('#tab-inspector');
  const p = P();
  const c = S.sel && TL.clipById(p, S.sel);
  if (!c) {
    box.replaceChildren(el('p', { class: 'muted' }, 'Klipi seçmək üçün zaman xəttində ona toxunun. Kənarlarını sürükləyərək kəsin və ya kəsilmiş hissəni geri qaytarın.'));
    return;
  }
  const kind = TL.trackKind(p, c);
  const lay = TL.layout(p).get(c.id);
  const m = c.media ? (S.mediaInfo[c.media] || TL.mediaById(p, c.media)) : null;
  const partner = TL.partnerOf(p, c);
  const kids = [
    el('h3', {}, `${KIND_NAME[kind]} klipi`),
    el('dl', { class: 'kv' },
      el('dt', {}, 'Zaman xətti'), el('dd', {}, `${fmt(lay.start)} – ${fmt(lay.end)}`),
      ...(m ? [el('dt', {}, 'Mənbə fayl'), el('dd', {}, m.name),
        el('dt', {}, 'Mənbə in/out'), el('dd', {}, `${fmt(c.srcIn)} – ${fmt(c.srcOut)} (fayl ${fmt(m.duration)})`)] : []),
      el('dt', {}, 'Mənşə'), el('dd', {}, c.origin === 'ai' ? 'AI təklifi' : c.origin === 'import' ? 'İdxal' : 'Əl ilə'),
      el('dt', {}, 'Bağlılıq'), el('dd', {}, partner ? (kind === 'video' ? 'Öz səsi ilə bağlı' : 'Videoya bağlı') : 'Sərbəst')),
  ];
  if (kind !== 'text' && kind !== 'video') {
    const vol = el('input', { type: 'range', min: 0, max: 2, step: 0.05, value: c.volume ?? 1 });
    const out = el('span', { class: 'muted' }, `${Math.round((c.volume ?? 1) * 100)}%`);
    vol.oninput = () => { out.textContent = `${Math.round(vol.value * 100)}%`; };
    vol.onchange = () => tryOp((q) => TL.setVolume(q, c.id, Number(vol.value)));
    kids.push(el('div', { class: 'row' }, el('label', {}, 'Səs səviyyəsi'), vol, out));
    if (!c.linkedTo) {
      const sel = el('select', {}, ...p.tracks.filter((t) => ['speech', 'music', 'sfx'].includes(t.kind)).map((t) =>
        el('option', { value: t.id, selected: t.id === c.track }, t.name)));
      sel.onchange = () => tryOp((q) => TL.changeTrack(q, c.id, sel.value));
      kids.push(el('div', { class: 'row' }, el('label', {}, 'Qat'), sel));
    }
  }
  if (kind === 'text') {
    const ta = el('textarea', {}, c.text || '');
    ta.onchange = () => tryOp((q) => TL.setText(q, c.id, { text: ta.value }));
    const pos = el('select', {}, ...[['top', 'Yuxarı'], ['center', 'Orta'], ['bottom', 'Aşağı']].map(([v, n]) =>
      el('option', { value: v, selected: (c.position || 'bottom') === v }, n)));
    pos.onchange = () => tryOp((q) => TL.setText(q, c.id, { position: pos.value }));
    const size = el('input', { type: 'range', min: 0.03, max: 0.15, step: 0.005, value: c.size || 0.06 });
    size.onchange = () => tryOp((q) => TL.setText(q, c.id, { size: Number(size.value) }));
    kids.push(el('div', { class: 'row' }, ta), el('div', { class: 'row' }, el('label', {}, 'Mövqe'), pos),
      el('div', { class: 'row' }, el('label', {}, 'Ölçü'), size));
  }
  if (partner) kids.push(el('div', { class: 'row' }, el('button', { onclick: () => $('#tUnlink').click() }, '⛓ Səsi videodan ayır')));
  if (kind !== 'text') {
    kids.push(el('div', { class: 'card' },
      el('p', {}, c.manual ? '✋ Əl ilə düzəldilib — AI təklifləri bu klipə toxunmayacaq.' : 'AI təklifləri bu klipi dəyişə bilər (yalnız sizin təsdiqinizlə).'),
      el('button', { onclick: () => tryOp((q) => TL.setProtected(q, c.id, !c.manual)) },
        c.manual ? 'AI-yə dəyişməyə icazə ver' : 'Qoru (AI dəyişməsin)')));
  }
  box.replaceChildren(...kids);
}

function capBadge(ok, text) { return el('span', { class: 'badge ' + (ok ? 'ok' : 'off') }, text); }

async function ensureStatus() {
  if (!S.status) {
    try { S.status = await api('/api/status'); } catch { S.status = null; }
  }
  return S.status;
}

async function renderAI() {
  const box = $('#tab-ai');
  const st = await ensureStatus();
  const p = P();
  const kids = [el('h3', {}, 'Təkliflər'),
    el('p', { class: 'muted' }, 'Təkliflər əvvəl storyboard kimi göstərilir. Siz təsdiqləməyincə montaja heç nə tətbiq olunmur. Əl ilə düzəldilmiş (✋) kliplər toxunulmaz qalır.')];
  if (!st) { box.replaceChildren(...kids, el('p', {}, 'Server statusu alınmadı.')); return; }

  const silBtn = el('button', { disabled: !st.silence.available }, 'Səssiz hissələri tap');
  silBtn.onclick = async () => {
    silBtn.disabled = true; silBtn.textContent = 'Analiz edilir…';
    try {
      await flushSave();
      const pr = await api(`/api/projects/${S.pid}/proposals/silence`, { method: 'POST', body: JSON.stringify({}) });
      commit(TL.addProposal(S.hist.present, pr), pr.summary);
    } catch (e) { toast(e.message, true); }
    renderAI();
  };
  kids.push(el('div', { class: 'card' },
    el('div', { class: 'row' }, el('b', {}, 'Səssizlik analizi'), capBadge(st.silence.available, st.silence.available ? 'işləyir · yerli' : 'əlçatmaz')),
    el('p', { class: 'muted' }, st.silence.engine), silBtn));

  // Transkripsiya
  const mids = [...new Set(p.clips.filter((c) => c.media && ['video', 'speech'].includes(TL.trackKind(p, c))).map((c) => c.media))]
    .filter((mid) => (S.mediaInfo[mid] || {}).hasAudio);
  const tr = st.transcription;
  const trCard = el('div', { class: 'card' },
    el('div', { class: 'row' }, el('b', {}, 'Transkripsiya'), capBadge(tr.available, tr.available ? `işləyir · ${tr.engine}` : 'quraşdırılmayıb')),
    el('p', { class: 'muted' }, tr.note));
  if (tr.available) {
    for (const mid of mids) {
      const m = S.mediaInfo[mid];
      const b = el('button', {}, `“${m.name}” transkripsiya et`);
      b.onclick = () => startTranscribe(mid, b);
      trCard.append(el('div', { class: 'row' }, b));
      loadTranscript(mid).then((t) => { if (t && S.tab === 'ai') renderTranscriptInto(trCard, mid, t); });
    }
    const fb = el('button', {}, 'Doldurucu sözləri (ee, ıı, hmm) çıxarmağı təklif et');
    fb.onclick = async () => {
      try {
        await flushSave();
        const pr = await api(`/api/projects/${S.pid}/proposals/fillers`, { method: 'POST', body: JSON.stringify({}) });
        commit(TL.addProposal(S.hist.present, pr), pr.summary);
      } catch (e) { toast(e.message, true); }
      renderAI();
    };
    trCard.append(el('div', { class: 'row' }, fb));
  }
  kids.push(trCard);

  kids.push(el('div', { class: 'card' },
    el('div', { class: 'row' }, el('b', {}, 'LLM ilə montaj təklifi'), el('span', { class: 'badge off' }, 'qoşulmayıb')),
    el('p', { class: 'muted' }, st.llm.note + (st.llm.keyPresent ? ' (API açarı mühitdə var, amma inteqrasiya hələ yazılmayıb.)' : ' API açarı da qurulmayıb.')),
    el('button', { disabled: true }, 'Ssenari üzrə təklif (əlçatmaz)')));

  const pending = (p.proposals || []).filter((x) => x.status === 'pending');
  const done = (p.proposals || []).filter((x) => x.status !== 'pending').slice(-5).reverse();
  for (const pr of pending) kids.push(storyboard(pr));
  if (done.length) {
    kids.push(el('h3', {}, 'Əvvəlki təkliflər'));
    for (const pr of done) {
      kids.push(el('p', { class: 'muted' }, `${pr.title} — ${pr.status === 'applied' ? `tətbiq olundu (${pr.result?.applied ?? 0} klip${pr.result?.skipped?.length ? `, ${pr.result.skipped.length} atlandı` : ''})` : 'rədd edildi'}`));
    }
  }
  box.replaceChildren(...kids);
}

function storyboard(pr) {
  const p = P();
  const checked = TL.previewProposal(p, pr);
  const card = el('div', { class: 'card' }, el('b', {}, `Storyboard: ${pr.title}`), el('p', {}, pr.summary));
  for (const it of checked) {
    const c = TL.clipById(p, it.clipId);
    const m = c && S.mediaInfo[c.media];
    card.append(el('p', { class: it.ok ? '' : 'muted' }, `${m ? m.name : 'klip'} ${it.ok ? '' : `— atlanacaq: ${it.reason}`}`));
    if (c) {
      const bar = el('div', { class: 'bar' });
      const d = c.srcOut - c.srcIn;
      for (const [a, b] of it.keep) {
        const s = el('span');
        s.style.left = `${((a - c.srcIn) / d) * 100}%`;
        s.style.width = `${((b - a) / d) * 100}%`;
        bar.append(s);
      }
      card.append(bar);
    }
    if (it.ok && m && m.hasVideo) {
      const sb = el('div', { class: 'storyboard' });
      const shots = [];
      for (const [a, b] of it.keep) shots.push({ a, b, cut: false });
      for (const [a, b] of it.removed || []) shots.push({ a, b, cut: true });
      shots.sort((x, y) => x.a - y.a);
      for (const s of shots.slice(0, 24)) {
        sb.append(el('div', { class: 'shot' + (s.cut ? ' cut' : '') },
          el('img', { loading: 'lazy', alt: '', src: `/api/projects/${S.pid}/media/${c.media}/frame?t=${((s.a + s.b) / 2).toFixed(1)}` }),
          el('div', { class: 'meta' }, `${s.cut ? '✕ silinir' : '✓ qalır'} ${fmt(s.a)}–${fmt(s.b)}`)));
      }
      card.append(sb);
    }
  }
  for (const s of pr.skippedManual || []) card.append(el('p', { class: 'muted' }, `✋ Klip qorunur (${s.reason}).`));
  const okCount = checked.filter((x) => x.ok).length;
  card.append(el('div', { class: 'row' },
    el('button', { class: 'primary', disabled: !okCount, onclick: () => {
      const r = TL.applyProposal(S.hist.present, pr);
      commit(r.project, `Təsdiqləndi: ${r.applied.length} klip dəyişdi${r.skipped.length ? `, ${r.skipped.length} atlandı` : ''}`);
    } }, 'Təsdiqlə və tətbiq et'),
    el('button', { onclick: () => commit(TL.rejectProposal(S.hist.present, pr.id), 'Təklif rədd edildi') }, 'Rədd et')));
  return card;
}

async function loadTranscript(mid) {
  if (S.transcripts[mid]) return S.transcripts[mid];
  try {
    S.transcripts[mid] = await api(`/api/projects/${S.pid}/transcripts/${mid}`);
    return S.transcripts[mid];
  } catch { return null; }
}

function renderTranscriptInto(card, mid, t) {
  const fillers = new Set(['ee', 'eee', 'ə', 'əə', 'ıı', 'hmm', 'hm', 'mm', 'ah', 'eh', 'ım']);
  const words = el('div', { class: 'words' }, ...t.words.map((w) => {
    const norm = w.w.toLowerCase().replace(/[^\p{L}]/gu, '');
    const b = el('button', { class: (fillers.has(norm) ? 'filler ' : '') + (w.p < 0.5 ? 'low' : ''), title: `${fmt(w.s)} · ehtimal ${w.p}` }, w.w);
    b.onclick = () => seekToSource(mid, w.s);
    return b;
  }));
  card.append(el('p', { class: 'muted' }, `Dil: ${t.language} (${Math.round(t.languageProbability * 100)}%), model: ${t.model}, ${t.words.length} söz. Sözə toxunun — həmin yerə keçir.`), words);
}

function seekToSource(mid, srcT) {
  const p = P();
  const lay = TL.layout(p);
  const c = p.clips.find((x) => x.media === mid && x.srcIn <= srcT && x.srcOut > srcT && TL.trackKind(p, x) !== 'text');
  if (!c) { toast('Bu söz hazırda montajda yoxdur (kəsilib)'); return; }
  pause();
  seek(lay.get(c.id).start + (srcT - c.srcIn));
}

async function startTranscribe(mid, btn) {
  btn.disabled = true;
  try {
    const { job } = await api(`/api/projects/${S.pid}/transcribe`, { method: 'POST', body: JSON.stringify({ mediaId: mid, language: 'az' }) });
    btn.textContent = 'Transkripsiya gedir… (CPU-da bir neçə dəqiqə çəkə bilər)';
    const j = await waitJob(job);
    if (j.status === 'done') { delete S.transcripts[mid]; toast(`Transkripsiya hazırdır: ${j.result.words} söz`); }
    else toast('Transkripsiya alınmadı: ' + j.error, true);
  } catch (e) { toast(e.message, true); }
  renderAI();
}

async function waitJob(id, onProgress) {
  for (;;) {
    const j = await api(`/api/jobs/${id}`);
    if (onProgress) onProgress(j);
    if (j.status !== 'running') return j;
    await new Promise((r) => setTimeout(r, 1000));
  }
}

function renderMedia() {
  const box = $('#tab-media');
  const p = P();
  const used = new Set(p.clips.map((c) => c.media));
  const list = el('ul', { class: 'media-list' }, ...p.media.map((m0) => {
    const m = S.mediaInfo[m0.id] || m0;
    const add = el('button', {}, 'Zaman xəttinə əlavə et');
    add.onclick = () => {
      if (m.hasVideo) {
        tryOp((q) => {
          const r = TL.clone(q);
          const vid = TL.uid('v');
          r.clips.push({ id: vid, track: 'v1', media: m.id, srcIn: 0, srcOut: m.duration, order: TL.videoClips(r).length, origin: 'manual', manual: true });
          if (m.hasAudio) r.clips.push({ id: TL.uid('a'), track: 'a1', media: m.id, srcIn: 0, srcOut: m.duration, linkedTo: vid, volume: 1, origin: 'manual', manual: true });
          return r;
        }, 'Əlavə olundu');
      } else {
        const tr = selectedAudioTrack() || 'm1';
        tryOp((q) => {
          const r = TL.clone(q);
          r.clips.push({ id: TL.uid('a'), track: tr, media: m.id, srcIn: 0, srcOut: m.duration, start: S.t, volume: 1, origin: 'manual', manual: true });
          return r;
        }, 'Əlavə olundu');
      }
    };
    return el('li', {},
      el('div', {}, el('b', {}, m.name), ' ', used.has(m.id) ? capBadge(true, 'istifadədə') : capBadge(false, 'istifadə olunmur')),
      el('div', { class: 'muted' }, `${fmt(m.duration)} · ${m.hasVideo ? `${m.width}×${m.height} video` : 'yalnız səs'}${m.hasAudio && m.hasVideo ? ' + səs' : ''} · ${(m.size / 1048576).toFixed(1)} MB`),
      el('div', { class: 'muted' }, m.preview ? 'Önizləmə nüsxəsi hazırdır' : m.previewError ? 'Önizləmə nüsxəsi alınmadı — orijinal oynadılır' : 'Önizləmə nüsxəsi hazırlanır…'),
      el('div', { class: 'row' }, add));
  }));
  box.replaceChildren(
    el('h3', {}, 'Media'),
    el('p', { class: 'muted' }, 'Orijinal fayllar yalnız oxunur rejimində saxlanılır və heç vaxt dəyişdirilmir. Səs faylı seçilmiş səs qatına (yoxdursa musiqi qatına) əlavə olunur.'),
    p.media.length ? list : el('p', { class: 'muted' }, 'Hələ media yoxdur.'));
}

function renderExport() {
  const box = $('#tab-export');
  const btn = el('button', { class: 'primary' }, 'MP4 render et');
  btn.onclick = () => startRender();
  const kids = [el('h3', {}, 'MP4 ixrac'),
    el('p', { class: 'muted' }, 'Render önizləmə ilə eyni saxlanmış layihə məlumatından FFmpeg ilə hazırlanır. Remotion bu paneldə hələ qoşulmayıb.'), btn];
  for (const r of S.renders) {
    const row = el('div', { class: 'card render-out' }, el('p', {}, r.label));
    if (r.status === 'running') row.append(el('div', { class: 'progress' }, Object.assign(el('span'), { style: `width:${Math.round(r.progress * 100)}%` })));
    if (r.url) row.append(el('a', { href: r.url, download: r.file }, '⬇ Yüklə: ' + r.file), el('video', { src: r.url, controls: true, playsinline: true }));
    kids.push(row);
  }
  box.replaceChildren(...kids);
}

async function startRender() {
  setTab('export');
  if (!(await flushSave())) { toast('Layihə saxlanmadı — render dayandırıldı', true); return; }
  const entry = { label: `Versiya ${S.revision}: render gedir…`, status: 'running', progress: 0 };
  S.renders.unshift(entry);
  renderExport();
  try {
    const { job } = await api(`/api/projects/${S.pid}/render`, { method: 'POST', body: JSON.stringify({ revision: S.revision }) });
    const j = await waitJob(job, (x) => { entry.progress = x.progress || 0; if (S.tab === 'export') renderExport(); });
    if (j.status === 'done') {
      Object.assign(entry, { status: 'done', url: j.result.url, file: j.result.file, label: `Versiya ${j.result.revision}: hazırdır` });
      toast('MP4 hazırdır');
    } else {
      Object.assign(entry, { status: 'error', label: 'Render xətası: ' + j.error });
    }
  } catch (e) {
    Object.assign(entry, { status: 'error', label: 'Render xətası: ' + e.message });
  }
  renderExport();
}
$('#btnRender').onclick = startRender;

window.addEventListener('resize', () => { if (S.pid) { renderTimeline(); updatePlayhead(); syncPlayer(); } });

// Giriş: #/p/<id> varsa layihəni aç
const m = location.hash.match(/^#\/p\/([a-z0-9_-]+)/);
if (m) openProject(m[1]); else showHome();

// testlər üçün
window.__montaj = { S, TL, P, seek, play, pause, save: flushSave };
