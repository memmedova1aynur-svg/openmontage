// Montaj paneli — zaman xətti modeli (saf funksiyalar).
//
// Bu modul həm brauzerdə (önizləmə, redaktə), həm də Node testlərində işləyir.
// Bütün əməliyyatlar layihəni dəyişmir — yeni layihə qaytarır.
//
// Əsas qaydalar:
//  * Orijinal fayl heç vaxt dəyişmir. Klip yalnız media id + srcIn/srcOut saxlayır.
//  * Video qatı "maqnitlidir": kliplər `order` ilə ardıcıl düzülür, başlanğıc
//    vaxtı hesablanır. Digər qatlarda klipin öz `start` vaxtı var.
//  * Videonun öz səsi `linkedTo` ilə bağlı danışıq klipidir: bölmə, silmə,
//    kəsmə və yer dəyişmə ikisinə birlikdə tətbiq olunur. Ayırmaq (unlink)
//    ayrıca əməliyyatdır.
//  * Əl ilə dəyişdirilən klip `manual: true` alır; AI təklifləri belə klipləri
//    dəyişmir.

export const MIN_CLIP = 0.1;
export const SCHEMA_VERSION = 1;

export const TRACKS = [
  { id: 'v1', kind: 'video', name: 'Video' },
  { id: 'a1', kind: 'speech', name: 'Danışıq' },
  { id: 'm1', kind: 'music', name: 'Musiqi' },
  { id: 's1', kind: 'sfx', name: 'Səs effekti' },
  { id: 't1', kind: 'text', name: 'Mətn' },
  { id: 'c1', kind: 'text', name: 'Subtitr' },
];

export const IMAGE_SECONDS = 3;

const EPS = 1e-6;
const round = (x) => Math.round(x * 1000) / 1000;

let _seq = 0;
export function uid(prefix = 'c') {
  _seq += 1;
  const rnd = Math.random().toString(36).slice(2, 7);
  return `${prefix}_${Date.now().toString(36)}${_seq.toString(36)}${rnd}`;
}

export function clone(x) {
  return JSON.parse(JSON.stringify(x));
}

export function newProject({ id, title }) {
  return {
    schema: SCHEMA_VERSION,
    id,
    title: title || 'Yeni layihə',
    revision: 0,
    width: 1280,
    height: 720,
    fps: 30,
    tracks: clone(TRACKS),
    media: [],
    clips: [],
    proposals: [],
  };
}

export function trackOf(p, trackId) {
  return p.tracks.find((t) => t.id === trackId);
}

export function trackKind(p, clip) {
  const t = trackOf(p, clip.track);
  return t ? t.kind : null;
}

export function mediaById(p, id) {
  return p.media.find((m) => m.id === id);
}

export function clipById(p, id) {
  return p.clips.find((c) => c.id === id);
}

export function clipDur(c) {
  return c.srcOut - c.srcIn;
}

export function videoClips(p) {
  return p.clips
    .filter((c) => trackKind(p, c) === 'video')
    .sort((a, b) => a.order - b.order);
}

/** Bağlı tərəfdaş klipi (video <-> onun səsi). */
export function partnerOf(p, clip) {
  if (!clip) return null;
  if (clip.linkedTo) return clipById(p, clip.linkedTo) || null;
  return p.clips.find((c) => c.linkedTo === clip.id) || null;
}

/** Hər klipin zaman xəttindəki {start, end} dəyərləri. */
export function layout(p) {
  const out = new Map();
  let t = 0;
  for (const c of videoClips(p)) {
    out.set(c.id, { start: round(t), end: round(t + clipDur(c)) });
    t += clipDur(c);
  }
  for (const c of p.clips) {
    if (out.has(c.id)) continue;
    if (c.linkedTo && out.has(c.linkedTo)) {
      const v = out.get(c.linkedTo);
      out.set(c.id, { start: v.start, end: round(v.start + clipDur(c)) });
    } else {
      const s = c.start || 0;
      out.set(c.id, { start: round(s), end: round(s + clipDur(c)) });
    }
  }
  return out;
}

export function duration(p) {
  let d = 0;
  for (const v of layout(p).values()) d = Math.max(d, v.end);
  return round(d);
}

function normalizeOrder(p) {
  videoClips(p).forEach((c, i) => {
    c.order = i;
  });
  return p;
}

function markManual(...clips) {
  for (const c of clips) if (c) {
    c.manual = true;
    c.origin = c.origin || 'manual';
  }
}

function fail(msg) {
  throw new Error(msg);
}

function mustClip(p, id) {
  return clipById(p, id) || fail('Klip tapılmadı');
}

// ---------------------------------------------------------------------------
// Media əlavə etmək
// ---------------------------------------------------------------------------

/**
 * Yüklənmiş medianı layihəyə əlavə edir.
 * Video faylı -> video qatının sonuna klip + (səs varsa) bağlı danışıq klipi.
 * Yalnız səs -> seçilmiş qata (`targetTrack`, susmaya görə musiqi) `at` vaxtında.
 */
export function addMedia(p0, media, { targetTrack = null, at = 0 } = {}) {
  const p = clone(p0);
  if (p.media.some((m) => m.id === media.id)) fail('Bu media artıq əlavə olunub');
  p.media.push(clone(media));
  const dur = media.duration;
  if (!(dur > 0)) fail('Media müddəti məlum deyil');
  if (media.hasVideo) {
    if (videoClips(p).length === 0 && media.width && media.height && !media.isImage) {
      p.width = media.width;
      p.height = media.height;
      if (media.fps && media.fps > 0 && media.fps <= 120) p.fps = Math.round(media.fps);
      if (media.fpsRate) p.fpsRate = media.fpsRate;
    }
    const vid = uid('v');
    p.clips.push({
      id: vid, track: 'v1', media: media.id, srcIn: 0, srcOut: round(media.isImage ? IMAGE_SECONDS : dur),
      order: videoClips(p).length, origin: 'import', manual: false,
    });
    if (media.hasAudio) {
      p.clips.push({
        id: uid('a'), track: 'a1', media: media.id, srcIn: 0, srcOut: round(dur),
        linkedTo: vid, volume: 1, origin: 'import', manual: false,
      });
    }
  } else if (media.hasAudio) {
    const track = targetTrack || 'm1';
    const kind = trackOf(p, track)?.kind;
    if (!['speech', 'music', 'sfx'].includes(kind)) fail('Səs faylı yalnız səs qatına qoyula bilər');
    p.clips.push({
      id: uid('a'), track, media: media.id, srcIn: 0, srcOut: round(dur),
      start: round(Math.max(0, at)), volume: kind === 'music' ? 0.5 : 1,
      origin: 'import', manual: false,
    });
  } else {
    fail('Faylda nə video, nə səs var');
  }
  return p;
}

// ---------------------------------------------------------------------------
// Redaktə əməliyyatları
// ---------------------------------------------------------------------------

/** Klipi zaman xəttindəki `t` anında bölür (bağlı səs də bölünür). */
export function splitAt(p0, clipId, t) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const lay = layout(p);
  const { start, end } = lay.get(c.id);
  if (t <= start + MIN_CLIP - EPS || t >= end - MIN_CLIP + EPS) {
    fail('Bölmə nöqtəsi klipin kənarına çox yaxındır');
  }
  const offset = t - start;
  const group = [c, partnerOf(p, c)].filter(Boolean);
  // Video klipi əvvəl böl ki, bağlı səs yeni video hissəyə bağlansın.
  const rank = (x) => (trackKind(p, x) === 'video' ? 0 : 1);
  group.sort((a, b) => rank(a) - rank(b));
  const created = new Map();
  for (const g of group) {
    const cut = round(g.srcIn + offset);
    const right = { ...clone(g), id: uid(g.id[0] || 'c'), srcIn: cut };
    g.srcOut = cut;
    if (trackKind(p, g) === 'video') {
      right.order = g.order + 0.5;
    } else if (!g.linkedTo) {
      right.start = round((g.start || 0) + offset);
    }
    created.set(g.id, right);
    markManual(g, right);
    p.clips.push(right);
  }
  // Bağlı səsin sağ hissəsi videonun sağ hissəsinə bağlansın.
  for (const g of group) {
    if (g.linkedTo && created.has(g.linkedTo)) {
      created.get(g.id).linkedTo = created.get(g.linkedTo).id;
    }
  }
  return settle(normalizeOrder(p));
}

/** Mətn klipi üçün bölmə ayrıca: müddət əsaslıdır. */
export function splitText(p0, clipId, t) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const s = c.start || 0;
  const d = clipDur(c);
  if (t <= s + MIN_CLIP || t >= s + d - MIN_CLIP) fail('Bölmə nöqtəsi klipin kənarına çox yaxındır');
  const right = { ...clone(c), id: uid('t'), start: round(t), srcIn: 0, srcOut: round(s + d - t) };
  c.srcOut = round(t - s);
  c.srcIn = 0;
  markManual(c, right);
  p.clips.push(right);
  return settle(p);
}

export function split(p, clipId, t) {
  const c = mustClip(p, clipId);
  return trackKind(p, c) === 'text' ? splitText(p, clipId, t) : splitAt(p, clipId, t);
}

/** Klipi silir (bağlı səs də silinir). Orijinal media qalır. */
export function deleteClip(p0, clipId) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const partner = partnerOf(p, c);
  const kill = new Set([c.id, partner?.id].filter(Boolean));
  p.clips = p.clips.filter((x) => !kill.has(x.id));
  return settle(normalizeOrder(p));
}

/** Video klipinin sırasını dəyişir (bağlı səs onunla birlikdə gedir). */
export function moveVideo(p0, clipId, newIndex) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  if (trackKind(p, c) !== 'video') fail('Bu klip video qatında deyil');
  const seq = videoClips(p).filter((x) => x.id !== c.id);
  const idx = Math.max(0, Math.min(seq.length, Math.round(newIndex)));
  seq.splice(idx, 0, c);
  seq.forEach((x, i) => {
    x.order = i;
  });
  markManual(c, partnerOf(p, c));
  return settle(p);
}

/** Sərbəst klipi (musiqi, effekt, mətn, ayrılmış səs) yeni vaxta aparır. */
export function moveFree(p0, clipId, start) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const kind = trackKind(p, c);
  if (kind === 'video') fail('Video klipləri sıra ilə yerdəyişir');
  if (c.linkedTo) fail('Bağlı səs videoya bağlıdır — əvvəl ayırın');
  c.start = round(Math.max(0, start));
  markManual(c);
  return settle(p);
}

/** Sərbəst klipi başqa uyğun qata keçirir (məs. danışıq -> səs effekti). */
export function changeTrack(p0, clipId, trackId) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const from = trackKind(p, c);
  const to = trackOf(p, trackId)?.kind;
  const audio = ['speech', 'music', 'sfx'];
  if (!(audio.includes(from) && audio.includes(to))) fail('Bu qata keçirmək olmaz');
  if (c.linkedTo) fail('Bağlı səs videoya bağlıdır — əvvəl ayırın');
  c.track = trackId;
  markManual(c);
  return p;
}

/**
 * Klipin kənarını dəyişir. `edge` = 'in' | 'out', `value` mənbə faylındakı
 * yeni vaxtdır. Kənarı geri uzatmaq əvvəl kəsilmiş materialı qaytarır.
 * Mənbə sərhədləri: 0 .. media.duration. Bağlı səs eyni qədər dəyişir.
 */
export function trim(p0, clipId, edge, value) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const kind = trackKind(p, c);
  const group = [c, partnerOf(p, c)].filter(Boolean);
  if (kind === 'text') {
    // mətn: in -> start dəyişir, out -> müddət
    const s = c.start || 0;
    const end = s + clipDur(c);
    if (edge === 'in') {
      const ns = round(Math.max(0, Math.min(value, end - MIN_CLIP)));
      c.start = ns;
      c.srcIn = 0;
      c.srcOut = round(end - ns);
    } else {
      c.srcIn = 0;
      c.srcOut = round(Math.max(MIN_CLIP, value - s));
    }
    markManual(c);
    return p;
  }
  // bütün qrup üçün icazə verilən intervalı hesabla
  let lo = -Infinity;
  let hi = Infinity;
  for (const g of group) {
    const m = mediaById(p, g.media);
    const max = m ? m.duration : g.srcOut;
    if (edge === 'in') {
      lo = Math.max(lo, -g.srcIn); // srcIn >= 0
      hi = Math.min(hi, g.srcOut - MIN_CLIP - g.srcIn);
    } else {
      lo = Math.max(lo, g.srcIn + MIN_CLIP - g.srcOut);
      hi = Math.min(hi, max - g.srcOut);
    }
  }
  const base = edge === 'in' ? c.srcIn : c.srcOut;
  const delta = Math.max(lo, Math.min(hi, value - base));
  for (const g of group) {
    if (edge === 'in') {
      g.srcIn = round(g.srcIn + delta);
      // sərbəst klipdə sağ kənar yerində qalsın
      if (trackKind(p, g) !== 'video' && !g.linkedTo) {
        g.start = round(Math.max(0, (g.start || 0) + delta));
      }
    } else {
      g.srcOut = round(g.srcOut + delta);
    }
  }
  markManual(...group);
  return settle(p);
}

/** Videonu öz səsindən ayırır — səs klipi sərbəst olur, eyni yerdə qalır. */
export function unlink(p0, clipId) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const partner = partnerOf(p, c);
  if (!partner) fail('Bu klipin bağlı səsi yoxdur');
  const audio = c.linkedTo ? c : partner;
  const lay = layout(p);
  audio.start = lay.get(audio.id).start;
  delete audio.linkedTo;
  markManual(c, partner);
  return settle(p);
}

export function setVolume(p0, clipId, volume) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  c.volume = round(Math.max(0, Math.min(2, volume)));
  markManual(c);
  return p;
}

export function addText(p0, { start, dur = 3, text = 'Mətn' }) {
  const p = clone(p0);
  p.clips.push({
    id: uid('t'), track: 't1', media: null, srcIn: 0, srcOut: round(Math.max(MIN_CLIP, dur)),
    start: round(Math.max(0, start)), text, size: 0.06, position: 'bottom',
    origin: 'manual', manual: true,
  });
  return p;
}

export function setText(p0, clipId, patch) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  if (trackKind(p, c) !== 'text') fail('Bu klip mətn deyil');
  for (const k of ['text', 'size', 'position']) if (k in patch) c[k] = patch[k];
  markManual(c);
  return p;
}

/** AI-nin dəyişə bilməsi üçün qoruma bayrağını dəyişir. */
export function setProtected(p0, clipId, isProtected) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  for (const g of [c, partnerOf(p, c)].filter(Boolean)) g.manual = !!isProtected;
  return p;
}

// ---------------------------------------------------------------------------
// Təkliflər (AI / avtomatik analiz) — təsdiqdən əvvəl heç nə dəyişmir
// ---------------------------------------------------------------------------

/**
 * Təklif elementi: { clipId, expect: {srcIn, srcOut}, keep: [[a,b], ...] }
 * `keep` mənbə vaxtındadır. Klip əl ilə dəyişibsə, yoxdursa və ya təklifdən
 * sonra dəyişibsə, element atlanır.
 */
export function previewProposal(p, proposal) {
  const items = [];
  for (const it of proposal.items || []) {
    const c = clipById(p, it.clipId);
    let reason = null;
    if (!c) reason = 'klip artıq yoxdur';
    else if (c.manual) reason = 'əl ilə düzəliş qorunur';
    else if (Math.abs(c.srcIn - it.expect.srcIn) > 0.002 || Math.abs(c.srcOut - it.expect.srcOut) > 0.002) {
      reason = 'klip təklifdən sonra dəyişib';
    } else if (!(it.keep || []).length) reason = null;
    items.push({ ...it, ok: !reason, reason });
  }
  return items;
}

export function applyProposal(p0, proposal) {
  let p = clone(p0);
  const checked = previewProposal(p, proposal);
  const applied = [];
  const skipped = [];
  for (const it of checked) {
    if (!it.ok) {
      skipped.push({ clipId: it.clipId, reason: it.reason });
      continue;
    }
    p = replaceWithSegments(p, it.clipId, it.keep);
    applied.push(it.clipId);
  }
  const pr = p.proposals.find((x) => x.id === proposal.id);
  if (pr) {
    pr.status = 'applied';
    pr.result = { applied: applied.length, skipped };
  }
  return { project: p, applied, skipped };
}

export function rejectProposal(p0, proposalId) {
  const p = clone(p0);
  const pr = p.proposals.find((x) => x.id === proposalId);
  if (pr) pr.status = 'rejected';
  return p;
}

export function addProposal(p0, proposal) {
  const p = clone(p0);
  p.proposals = (p.proposals || []).filter((x) => x.id !== proposal.id);
  p.proposals.push({ ...clone(proposal), status: 'pending' });
  return p;
}

function replaceWithSegments(p0, clipId, keep) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  const kind = trackKind(p, c);
  const partner = partnerOf(p, c);
  const segs = (keep || [])
    .map(([a, b]) => [Math.max(c.srcIn, a), Math.min(c.srcOut, b)])
    .filter(([a, b]) => b - a >= MIN_CLIP - EPS);
  p.clips = p.clips.filter((x) => x.id !== c.id && x.id !== partner?.id);
  if (kind === 'video') {
    const base = c.order;
    // sonrakı klipləri yer açmaq üçün sürüşdür
    for (const x of p.clips) if (trackKind(p, x) === 'video' && x.order > base) x.order += segs.length;
    segs.forEach(([a, b], i) => {
      const v = { ...clone(c), id: uid('v'), srcIn: round(a), srcOut: round(b), order: base + i * 0.01, origin: 'ai', manual: false };
      p.clips.push(v);
      if (partner) {
        p.clips.push({ ...clone(partner), id: uid('a'), srcIn: round(a), srcOut: round(b), linkedTo: v.id, origin: 'ai', manual: false });
      }
    });
    return normalizeOrder(p);
  }
  let t = c.start || 0;
  for (const [a, b] of segs) {
    p.clips.push({ ...clone(c), id: uid('a'), srcIn: round(a), srcOut: round(b), start: round(t), origin: 'ai', manual: false });
    t += b - a;
  }
  return p;
}

// ---------------------------------------------------------------------------
// Undo / redo
// ---------------------------------------------------------------------------

export class History {
  constructor(initial, cap = 100) {
    this.present = initial;
    this.past = [];
    this.future = [];
    this.cap = cap;
  }
  commit(next) {
    if (next === this.present) return this.present;
    this.past.push(this.present);
    if (this.past.length > this.cap) this.past.shift();
    this.future = [];
    this.present = next;
    return next;
  }
  undo() {
    if (!this.past.length) return null;
    this.future.push(this.present);
    this.present = this.past.pop();
    return this.present;
  }
  redo() {
    if (!this.future.length) return null;
    this.past.push(this.present);
    this.present = this.future.pop();
    return this.present;
  }
  get canUndo() {
    return this.past.length > 0;
  }
  get canRedo() {
    return this.future.length > 0;
  }
}

// ---------------------------------------------------------------------------
// Önizləmə üçün: verilən vaxtda nə görünür / səslənir
// ---------------------------------------------------------------------------

export function activeAt(p, t) {
  const lay = layout(p);
  const res = { video: null, audio: [], text: [] };
  for (const c of p.clips) {
    const { start, end } = lay.get(c.id);
    if (t < start - EPS || t >= end - EPS) continue;
    const kind = trackKind(p, c);
    const local = c.srcIn + (t - start);
    if (kind === 'video') res.video = { clip: c, start, end, local };
    else if (kind === 'text') res.text.push({ clip: c, start, end });
    else res.audio.push({ clip: c, start, end, local });
  }
  return res;
}

// ---------------------------------------------------------------------------
// Köhnə layihələri yeni sahələrlə tamamlamaq
// ---------------------------------------------------------------------------

export const DEFAULT_MIX = { speech: 1, music: 1, sfx: 1, voice: 1, duck: false };

export function migrate(p0) {
  const p = clone(p0);
  for (const t of TRACKS) if (!p.tracks.some((x) => x.id === t.id)) p.tracks.push(clone(t));
  p.mix = { ...DEFAULT_MIX, ...(p.mix || {}) };
  p.branding = p.branding || { logo: { enabled: false, position: 'top-right', size: 0.18, opacity: 1 }, end: { enabled: false, duration: 3, showLogo: true, cta: '', contact: '', bg: '#000000', color: '#FFFFFF' } };
  p.options = p.options || null;
  p.aspect = p.aspect || 'source';
  p.proposals = p.proposals || [];
  return p;
}

// ---------------------------------------------------------------------------
// Layihə parametrləri (undo/redo ilə)
// ---------------------------------------------------------------------------

export function setProjectField(p0, key, value) {
  const p = clone(p0);
  p[key] = clone(value);
  return p;
}

export function patchProject(p0, key, patch) {
  const p = clone(p0);
  p[key] = { ...(p[key] || {}), ...clone(patch) };
  return p;
}

/** Kadraj (klip + bağlı səs dəyişmir). manual=true -> AI dəyişmir. */
export function setFrame(p0, clipId, frame, { manual = true } = {}) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  if (trackKind(p, c) !== 'video') fail('Kadraj yalnız video klipə aiddir');
  if (frame == null) delete c.frame;
  else c.frame = clone(frame);
  if (manual) markManual(c, partnerOf(p, c));
  return p;
}

/** Rəng/güzgü düzəlişi. `all=true` -> bütün video kliplərə eyni dəyər. */
export function setAdjust(p0, clipId, patch, { all = false } = {}) {
  const p = clone(p0);
  const targets = all ? videoClips(p) : [mustClip(p, clipId)];
  for (const c of targets) {
    c.adjust = { ...(c.adjust || {}), ...clone(patch) };
    for (const [k, v] of Object.entries(c.adjust)) if (v === null) delete c.adjust[k];
  }
  return p;
}

export function resetAdjust(p0, clipId, { all = false } = {}) {
  const p = clone(p0);
  const targets = all ? videoClips(p) : [mustClip(p, clipId)];
  for (const c of targets) delete c.adjust;
  return p;
}

// ---------------------------------------------------------------------------
// Storyboard -> montaj (yalnız təsdiqdən sonra çağırılır)
// ---------------------------------------------------------------------------

function subtitleChunks(words, maxWords = 4, maxDur = 1.8) {
  const out = [];
  let cur = [];
  for (const w of words || []) {
    if (cur.length && (cur.length >= maxWords || w.e - cur[0].s > maxDur)) { out.push(cur); cur = []; }
    cur.push(w);
  }
  if (cur.length) out.push(cur);
  return out.map((ws) => ({ s: ws[0].s, e: ws[ws.length - 1].e, text: ws.map((w) => w.w).join(' ').trim() }));
}

export function applyStoryboard(p0, sb, { frames = {}, brand = null } = {}) {
  let p = migrate(p0);
  const cards = (sb.cards || []).filter((c) => c.include);
  const mediaIds = [...new Set(cards.map((c) => c.mediaId))];
  const skipped = [];
  const protectedMedia = new Set();
  for (const mid of mediaIds) {
    const manual = p.clips.find((c) => c.media === mid && trackKind(p, c) === 'video' && c.manual);
    if (manual) { protectedMedia.add(mid); skipped.push({ mediaId: mid, reason: 'əl ilə düzəldilmiş kliplər qorunur' }); }
  }
  const touched = new Set(mediaIds.filter((m) => !protectedMedia.has(m)));
  // köhnə avtomatik klipləri (əl ilə olmayan) çıxar
  const drop = new Set();
  for (const c of p.clips) {
    if (c.manual) continue;
    if (touched.has(c.media) && (trackKind(p, c) === 'video' || c.linkedTo)) drop.add(c.id);
    if (trackKind(p, c) === 'text' && c.origin === 'ai') drop.add(c.id);
  }
  p.clips = p.clips.filter((c) => !drop.has(c.id));
  normalizeOrder(p);
  const media = new Map(p.media.map((m) => [m.id, m]));
  let order = videoClips(p).length;
  const created = [];
  for (const card of cards) {
    if (protectedMedia.has(card.mediaId)) continue;
    const m = media.get(card.mediaId);
    if (!m) continue;
    const v = { id: uid('v'), track: 'v1', media: m.id, srcIn: round(card.srcIn), srcOut: round(card.srcOut), order: order++, origin: 'ai', manual: false, cardId: card.id };
    if (frames[m.id]) v.frame = clone(frames[m.id]);
    p.clips.push(v);
    if (m.hasAudio) p.clips.push({ id: uid('a'), track: 'a1', media: m.id, srcIn: v.srcIn, srcOut: v.srcOut, linkedTo: v.id, volume: 1, origin: 'ai', manual: false });
    created.push({ card, v });
  }
  const lay = layout(p);
  const color = brand && brand.colors && brand.colors[0] ? brand.colors[0] : null;
  for (const { card, v } of created) {
    const l = lay.get(v.id);
    if (card.onScreenText && card.onScreenText.trim()) {
      p.clips.push({ id: `txt_${v.id}`, track: 't1', media: null, srcIn: 0, srcOut: round(Math.min(3, l.end - l.start)), start: l.start, text: card.onScreenText.trim(), size: 0.055, position: 'top', bg: color ? `${color}@0.85` : null, origin: 'ai', manual: false, anchor: { clip: v.id, offset: 0 } });
    }
  }
  // Subtitrlər söz vaxtlarından yaradılır və klip dəyişəndə yenidən hesablanır
  const words = {};
  for (const [mid, segs] of Object.entries(sb.candidates || {})) {
    words[mid] = segs.flatMap((sg) => sg.words || []).map((w) => ({ w: w.w, s: w.s, e: w.e }));
  }
  for (const card of cards) if (!words[card.mediaId] && card.words) words[card.mediaId] = card.words.map((w) => ({ w: w.w, s: w.s, e: w.e }));
  p.subtitles = { enabled: !!sb.subtitles, words, size: 0.045, position: 'bottom' };
  p.storyboard = { ...clone(sb), status: 'approved', approvedAt: Date.now() };
  return { project: settle(p), applied: created.length, skipped };
}

// ---------------------------------------------------------------------------
// Bağlı mətnlər və avtomatik subtitrlər (klip dəyişəndə uyğunlaşır)
// ---------------------------------------------------------------------------

/** Anchor-lu mətnləri klipinə görə yerləşdirir, avtomatik subtitrləri söz vaxtlarından yenidən qurur. */
export function settle(p) {
  const lay = layout(p);
  for (const c of p.clips) {
    if (!c.anchor) continue;
    const l = lay.get(c.anchor.clip);
    if (!l) { c.hidden = true; continue; }
    c.hidden = false;
    c.start = round(l.start + (c.anchor.offset || 0));
    c.srcOut = round(Math.max(MIN_CLIP, Math.min(c.srcOut, l.end - c.start)));
  }
  rebuildSubtitles(p, lay);
  return p;
}

function rebuildSubtitles(p, lay = layout(p)) {
  const st = p.subtitles;
  if (!st || !st.enabled) return;
  const keepManual = new Map(p.clips.filter((c) => c.track === 'c1' && c.autoSub && c.manual).map((c) => [c.id, c]));
  p.clips = p.clips.filter((c) => !(c.track === 'c1' && c.autoSub && !c.manual));
  const seen = new Set();
  for (const v of videoClips(p)) {
    const ws = (st.words[v.media] || []).filter((w) => w.s >= v.srcIn - 0.01 && w.e <= v.srcOut + 0.01);
    const l = lay.get(v.id);
    for (const ch of subtitleChunks(ws)) {
      const id = `sub_${v.id}_${Math.round(ch.s * 1000)}`;
      seen.add(id);
      const start = round(l.start + (ch.s - v.srcIn));
      const dur = round(Math.max(MIN_CLIP, ch.e - ch.s));
      const old = keepManual.get(id);
      if (old) { old.start = start; old.srcIn = 0; old.srcOut = dur; old.hidden = false; continue; }
      p.clips.push({ id, track: 'c1', media: null, srcIn: 0, srcOut: dur, start, text: ch.text, size: st.size || 0.045,
        position: st.position || 'bottom', origin: 'auto', autoSub: true, manual: false, src: { clip: v.id, s: ch.s } });
    }
  }
  // əl ilə yerini dəyişdiyiniz subtitrin sözü kəsilibsə — gizlədilir (silinmir, geri qayıda bilər)
  for (const [id, c] of keepManual) if (!seen.has(id)) c.hidden = true;
}

/** Yazının ekrandakı yerini dəyişir (normallaşdırılmış mərkəz 0..1). Yalnız bu element dəyişir. */
export function setTextPos(p0, clipId, x, y) {
  const p = clone(p0);
  const c = mustClip(p, clipId);
  if (trackKind(p, c) !== 'text') fail('Bu element yazı deyil');
  c.x = round(Math.max(0.02, Math.min(0.98, x)));
  c.y = round(Math.max(0.02, Math.min(0.98, y)));
  c.manual = true;
  return p;
}

/** Klipin kənarını dəyişir + bağlı mətnləri və subtitrləri uyğunlaşdırır. */
export function trimSettled(p0, clipId, edge, value) {
  return settle(trim(p0, clipId, edge, value));
}

// ---------------------------------------------------------------------------
// Düzəliş faylı: telefondakı redaktordan gələn dəyişikliklər
// ---------------------------------------------------------------------------

export const EDITS_SCHEMA = 1;

/** Baza layihə ilə cari vəziyyət arasındakı əl düzəlişləri (yalnız dəyişən elementlər). */
export function diffEdits(base, cur) {
  const clips = {}; const texts = {};
  for (const c of cur.clips) {
    const b = clipById(base, c.id);
    if (!b) continue;
    const kind = trackKind(cur, c);
    if (kind === 'video' && (b.srcIn !== c.srcIn || b.srcOut !== c.srcOut)) {
      clips[c.id] = { srcIn: c.srcIn, srcOut: c.srcOut, base: { srcIn: b.srcIn, srcOut: b.srcOut } };
    }
    if (kind === 'text' && (b.x !== c.x || b.y !== c.y) && c.x != null) {
      texts[c.id] = { x: c.x, y: c.y, base: { x: b.x ?? null, y: b.y ?? null } };
    }
  }
  return { schema: EDITS_SCHEMA, projectId: base.id, baseRevision: base.revision, clips, texts };
}

/** Düzəliş faylını layihəyə tətbiq edir. Yanlış/köhnə layihə və dəyişmiş elementlər aşkarlanır. */
export function applyEdits(p0, edits) {
  if (!edits || edits.schema !== EDITS_SCHEMA) fail('Düzəliş faylının formatı tanınmadı');
  if (edits.projectId !== p0.id) fail(`Bu düzəliş başqa layihəyə aiddir (${edits.projectId})`);
  let p = clone(p0);
  const applied = []; const rejected = []; const already = [];
  const sameBase = Number(edits.baseRevision) === Number(p0.revision);
  for (const [id, e] of Object.entries(edits.clips || {})) {
    const c = clipById(p, id);
    if (!c) { rejected.push({ id, reason: 'klip artıq yoxdur' }); continue; }
    if (Math.abs(c.srcIn - e.srcIn) < 0.002 && Math.abs(c.srcOut - e.srcOut) < 0.002) { already.push(id); continue; }
    if (!sameBase && (Math.abs(c.srcIn - e.base.srcIn) > 0.002 || Math.abs(c.srcOut - e.base.srcOut) > 0.002)) {
      rejected.push({ id, reason: 'klip redaktordan sonra başqa yerdə dəyişib' }); continue;
    }
    try {
      if (Math.abs(c.srcIn - e.srcIn) > 1e-4) p = trim(p, id, 'in', e.srcIn);
      if (Math.abs(clipById(p, id).srcOut - e.srcOut) > 1e-4) p = trim(p, id, 'out', e.srcOut);
      const now = clipById(p, id);
      if (Math.abs(now.srcIn - e.srcIn) > 0.002 || Math.abs(now.srcOut - e.srcOut) > 0.002) {
        rejected.push({ id, reason: `mənbə sərhədi: ${now.srcIn}–${now.srcOut}` });
      } else applied.push(id);
    } catch (err) { rejected.push({ id, reason: err.message }); }
  }
  p = settle(p);
  for (const [id, e] of Object.entries(edits.texts || {})) {
    const c = clipById(p, id);
    if (!c) { rejected.push({ id, reason: 'yazı artıq yoxdur' }); continue; }
    if (c.x === e.x && c.y === e.y) { already.push(id); continue; }
    if (!sameBase && ((c.x ?? null) !== e.base.x || (c.y ?? null) !== e.base.y)) {
      rejected.push({ id, reason: 'yazı redaktordan sonra başqa yerdə dəyişib' }); continue;
    }
    p = setTextPos(p, id, e.x, e.y);
    applied.push(id);
  }
  return { project: p, applied, rejected, already, sameBase };
}
