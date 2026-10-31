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
];

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
    if (videoClips(p).length === 0 && media.width && media.height) {
      p.width = media.width;
      p.height = media.height;
      if (media.fps && media.fps > 0 && media.fps <= 60) p.fps = Math.round(media.fps);
    }
    const vid = uid('v');
    p.clips.push({
      id: vid, track: 'v1', media: media.id, srcIn: 0, srcOut: round(dur),
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
  return normalizeOrder(p);
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
  return p;
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
  return normalizeOrder(p);
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
  return p;
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
  return p;
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
  return p;
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
  return p;
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
