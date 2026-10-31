// Montaj qrafikası: başlıq, bölmə, vurğu, siyahı, kart, söz-söz altyazı; reklam üçün qiymət (offer), çağırış (cta), nişan (badge).
// EYNİ kod həm telefondakı redaktor önizləməsində, həm də yekun render üçün
// sessiyadakı Chromium rasterizasiyasında işləyir (şrift, ölçü, yer eyni olsun).
// Üslub expert-reels şablonundakı uğurlu qaydalardan götürülüb:
//   altyazı — Montserrat 800, deyilmiş söz tam, deyilməmiş 0.55 şəffaf, aktiv söz brend vurğu rəngində;
//   kartlar — brend əsas rəngi fonunda, yumşaq künclər, vurğu xətti; açar sözlər — vurğu rəngli “pill”.
(function (root) {
  const ANIMS = ['none', 'fade', 'pop', 'slide-up', 'slide-left'];

  /** Giriş/çıxış animasiyası: {opacity, tx, ty, scale}. Render (ffmpeg) eyni formulu işlədir. */
  function animState(clip, tl, W, H) {
    const dur = clip.srcOut - clip.srcIn;
    const a = clip.anim || {};
    const kind = a.in || 'none';
    const din = Math.max(0.05, a.d ?? 0.35);
    const dout = Math.max(0.05, a.dOut ?? 0.25);
    let opacity = 1, tx = 0, ty = 0, scale = 1;
    if (kind !== 'none' && tl < din) {
      const k = Math.max(0, tl / din);
      const e = 1 - Math.pow(1 - k, 3);
      opacity = k;
      if (kind === 'pop') scale = 0.86 + 0.14 * e;
      if (kind === 'slide-up') ty = (1 - e) * 0.04 * H;
      if (kind === 'slide-left') tx = -(1 - e) * 0.08 * W;
    }
    if ((a.out || 'fade') === 'fade' && tl > dur - dout) opacity = Math.min(opacity, Math.max(0, (dur - tl) / dout));
    return { opacity, tx, ty, scale };
  }

  function rgba(bg, fallback) {
    if (!bg) return fallback;
    if (bg === 'none') return 'transparent';
    const [hex, a] = String(bg).split('@');
    const h = hex.replace('#', '');
    const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${a == null ? 1 : Number(a)})`;
  }

  function node(doc, tag, css, text) {
    const n = doc.createElement(tag);
    if (css) Object.assign(n.style, css);
    if (text != null) n.textContent = text;
    return n;
  }

  /** Elementin DOM-u (mövqe xaric — onu çağıran qoyur). tl: elementin daxili vaxtı (altyazı sözləri üçün). */
  function build(doc, clip, H, theme, tl) {
    const th = theme || {};
    const type = clip.type || 'text';
    const fs = H * (clip.size || defaults(type).size);
    const font = `"${clip.font || 'Montserrat'}", "DejaVu Sans", sans-serif`;
    const weight = clip.weight || defaults(type).weight;
    const color = clip.color || defaults(type, th).color;
    const base = { fontFamily: font, fontWeight: String(weight), fontSize: `${fs}px`, lineHeight: '1.18', color, whiteSpace: 'pre-wrap', textAlign: 'center', boxSizing: 'border-box' };
    if (type === 'caption') {
      const wrap = node(doc, 'div', { ...base, maxWidth: `${H * 0.52}px`, padding: `${fs * 0.15}px ${fs * 0.3}px`, borderRadius: `${fs * 0.3}px`, background: rgba(clip.bg, 'transparent') });
      const words = clip.words && clip.words.length ? clip.words : String(clip.text || '').split(/\s+/).map((w) => ({ w, s: 0, e: 0 }));
      const stroke = clip.bg && clip.bg !== 'none' ? null : (clip.stroke || 'rgba(0,0,0,0.85)');
      words.forEach((w, i) => {
        const spoken = tl == null || tl >= w.s;
        const next = words[i + 1];
        const active = tl != null && tl >= w.s && (next ? tl < next.s : true);
        const sp = node(doc, 'span', { display: 'inline-block', margin: `0 ${fs * 0.13}px`, opacity: spoken ? '1' : '0.55',
          color: active ? (clip.activeColor || th.accent || '#F2C94C') : color }, w.w);
        if (stroke) { sp.style.webkitTextStroke = `${Math.max(2, fs * 0.09)}px ${stroke}`; sp.style.paintOrder = 'stroke fill'; }
        wrap.append(sp);
      });
      return wrap;
    }
    if (type === 'title') {
      const card = node(doc, 'div', { ...base, maxWidth: `${H * 0.5}px`, padding: `${fs * 0.5}px ${fs * 0.75}px ${fs * 0.6}px`, borderRadius: `${fs * 0.32}px`, background: rgba(clip.bg, rgba(`${th.primary || '#222222'}@${th.cardAlpha ?? 0.94}`)) });
      card.append(node(doc, 'div', {}, clip.text || ''));
      card.append(node(doc, 'div', { width: `${fs * 1.6}px`, height: `${Math.max(3, fs * 0.09)}px`, margin: `${fs * 0.28}px auto 0`, borderRadius: '99px', background: clip.accent || th.accent || '#F2C94C' }));
      return card;
    }
    if (type === 'section') {
      return node(doc, 'div', { ...base, padding: `${fs * 0.32}px ${fs * 0.75}px`, borderRadius: '999px', background: rgba(clip.bg, rgba(th.accent || '#F2C94C')), letterSpacing: '0.02em' }, clip.text || '');
    }
    if (type === 'emphasis') {
      return node(doc, 'div', { ...base, padding: `${fs * 0.22}px ${fs * 0.5}px`, borderRadius: `${fs * 0.28}px`, background: rgba(clip.bg, rgba(th.accent || '#F2C94C')), transform: `rotate(${clip.rot ?? -2}deg)` }, clip.text || '');
    }
    if (type === 'list' || type === 'card') {
      const card = node(doc, 'div', { ...base, textAlign: 'left', width: `${H * 0.47}px`, padding: `${fs * 0.75}px ${fs * 0.85}px`, borderRadius: `${fs * 0.45}px`, background: rgba(clip.bg, rgba(`${th.primary || '#222222'}@${th.cardAlpha ?? 0.94}`)) });
      if (clip.heading) card.append(node(doc, 'div', { fontSize: `${fs * 0.82}px`, fontWeight: '700', color: clip.headColor || th.accent || '#F2C94C', marginBottom: `${fs * 0.45}px` }, clip.heading));
      if (type === 'card') { card.append(node(doc, 'div', {}, clip.text || '')); return card; }
      const items = clip.items || [];
      const shown = tl == null ? items.length : items.filter((it) => tl >= (it.at || 0)).length;
      items.forEach((it, i) => {
        const row = node(doc, 'div', { display: 'flex', alignItems: 'center', gap: `${fs * 0.45}px`, margin: `${fs * 0.28}px 0`, opacity: i < shown ? '1' : '0' });
        row.append(node(doc, 'div', { flex: '0 0 auto', width: `${fs * 1.25}px`, height: `${fs * 1.25}px`, borderRadius: '50%', background: th.accent || '#F2C94C', color: th.onAccent || '#222', fontSize: `${fs * 0.7}px`, fontWeight: '800', display: 'flex', alignItems: 'center', justifyContent: 'center' }, String(i + 1)));
        row.append(node(doc, 'div', { minWidth: '0' }, it.text || ''));
        card.append(row);
      });
      return card;
    }
    if (type === 'offer') {  // qiymət kartı: başlıq, köhnə qiymət (üstündən xətt), yeni qiymət, qeyd — mətn yalnız danışıqdan
      const card = node(doc, 'div', { ...base, padding: `${fs * 0.7}px ${fs * 1.0}px ${fs * 0.8}px`, borderRadius: `${fs * 0.5}px`, background: rgba(clip.bg, rgba(`${th.primary || '#222222'}@${th.cardAlpha ?? 0.94}`)), minWidth: `${H * 0.22}px` });
      if (clip.heading) card.append(node(doc, 'div', { fontSize: `${fs * 0.72}px`, fontWeight: '700', letterSpacing: '0.04em', color: clip.headColor || th.accent || '#F2C94C', marginBottom: `${fs * 0.2}px` }, clip.heading));
      if (clip.oldPrice) card.append(node(doc, 'div', { fontSize: `${fs * 0.95}px`, fontWeight: '600', opacity: '0.7', textDecoration: 'line-through', textDecorationThickness: `${Math.max(2, fs * 0.08)}px` }, clip.oldPrice));
      card.append(node(doc, 'div', { fontSize: `${fs * 2.0}px`, fontWeight: '900', lineHeight: '1.05', color: clip.priceColor || clip.color || th.text || '#FFFFFF' }, clip.price || clip.text || ''));
      if (clip.note) card.append(node(doc, 'div', { fontSize: `${fs * 0.68}px`, fontWeight: '600', marginTop: `${fs * 0.3}px`, opacity: '0.9' }, clip.note));
      return card;
    }
    if (type === 'cta') {  // çağırış: "Şərhlərdə yazın" + açar söz böyük çipdə + əlaqə (istəyə görə)
      const box = node(doc, 'div', { ...base, maxWidth: `${H * 0.46}px`, padding: `${fs * 0.55}px ${fs * 0.8}px ${fs * 0.65}px`, borderRadius: `${fs * 0.5}px`, background: rgba(clip.bg, rgba(`${th.primary || '#222222'}@${th.cardAlpha ?? 0.94}`)) });
      if (clip.text) box.append(node(doc, 'div', { fontSize: `${fs * 0.85}px`, fontWeight: '700', marginBottom: `${fs * 0.35}px` }, clip.text));
      if (clip.keyword) box.append(node(doc, 'div', { display: 'inline-block', fontSize: `${fs * 1.55}px`, fontWeight: '900', letterSpacing: '0.06em', padding: `${fs * 0.18}px ${fs * 0.7}px`, borderRadius: `${fs * 0.35}px`, background: clip.accent || th.accent || '#F2C94C', color: th.onAccent || '#222222' }, clip.keyword));
      if (clip.sub) box.append(node(doc, 'div', { fontSize: `${fs * 0.62}px`, fontWeight: '600', marginTop: `${fs * 0.4}px`, opacity: '0.9' }, clip.sub));
      return box;
    }
    if (type === 'badge') {  // qısa nişan: tarix, yer sayı, endirim
      const b = node(doc, 'div', { ...base, display: 'inline-flex', alignItems: 'center', gap: `${fs * 0.4}px`, padding: `${fs * 0.3}px ${fs * 0.75}px`, borderRadius: '999px', background: rgba(clip.bg, rgba(`${th.primary || '#222222'}@${th.cardAlpha ?? 0.94}`)), border: `${Math.max(2, fs * 0.08)}px solid ${clip.accent || th.accent || '#F2C94C'}` });
      b.append(node(doc, 'div', { width: `${fs * 0.45}px`, height: `${fs * 0.45}px`, borderRadius: '50%', background: clip.accent || th.accent || '#F2C94C', flex: '0 0 auto' }));
      b.append(node(doc, 'div', {}, clip.text || ''));
      return b;
    }
    // sadə yazı (köhnə layihələr): drawtext ilə eyni görünüş
    return node(doc, 'div', { ...base, whiteSpace: 'pre', padding: '.25em', background: rgba(clip.bg, 'rgba(0,0,0,.55)'), textShadow: clip.bg === 'none' ? '2px 2px 0 rgba(0,0,0,.7)' : 'none' }, clip.text || '');
  }

  function defaults(type, th = {}) {
    return ({
      caption: { size: 0.036, weight: 800, color: '#FFFFFF' },
      title: { size: 0.034, weight: 800, color: th.text || '#FFFFFF' },
      section: { size: 0.024, weight: 700, color: th.onAccent || '#222222' },
      emphasis: { size: 0.034, weight: 800, color: th.onAccent || '#222222' },
      list: { size: 0.026, weight: 600, color: th.text || '#FFFFFF' },
      card: { size: 0.026, weight: 600, color: th.text || '#FFFFFF' },
      offer: { size: 0.03, weight: 700, color: th.text || '#FFFFFF' },
      cta: { size: 0.032, weight: 700, color: th.text || '#FFFFFF' },
      badge: { size: 0.022, weight: 800, color: th.text || '#FFFFFF' },
    })[type] || { size: 0.06, weight: 700, color: '#FFFFFF' };
  }

  /** Altyazı/siyahı üçün vəziyyət dəyişmə anları (element daxili vaxtında) — render bu anlarda PNG dəyişir. */
  function statePoints(clip) {
    if (clip.type === 'caption') return [0, ...(clip.words || []).map((w) => w.s)].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b);
    if (clip.type === 'list') return [0, ...(clip.items || []).map((it) => it.at || 0)].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b);
    return [0];
  }

  // Standart yer (x, y mərkəz, 0..1) — render (graphics.py DEFAULT_XY) ilə eyni
  const DEFAULT_XY = { caption: [0.5, 0.74], title: [0.5, 0.14], section: [0.5, 0.22], emphasis: [0.5, 0.62], list: [0.5, 0.42], card: [0.5, 0.42],
    offer: [0.5, 0.58], cta: [0.5, 0.585], badge: [0.5, 0.215] };  // reklam kartları üzün altında, altyazının üstündə
  function pos(clip) { const d = DEFAULT_XY[clip.type] || [0.5, 0.5]; return [clip.x ?? d[0], clip.y ?? d[1]]; }

  root.MG = { ANIMS, animState, build, defaults, statePoints, rgba, pos, DEFAULT_XY };
})(typeof window !== 'undefined' ? window : globalThis);
