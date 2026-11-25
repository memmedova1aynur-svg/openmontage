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
    const VW = (doc.defaultView && doc.defaultView.innerWidth) || H * 0.5625;  // kadr eni (px) — tam enli elementlər üçün
    const shown = (items) => (tl == null ? items.length : items.filter((it) => tl >= (it.at || 0)).length);
    if (type === 'frame') {  // üslub dəsti: nazik çərçivə + künc nişanları (tam kadr, şəffaf; bleed) — festival/sənədli görünüş
      const NS = 'http://www.w3.org/2000/svg';
      const m = VW * (clip.m ?? 0.04), tick = VW * 0.045, sw = Math.max(1, VW * 0.0035);
      const e = doc.createElementNS(NS, 'svg');
      e.setAttribute('width', VW); e.setAttribute('height', H); e.setAttribute('viewBox', `0 0 ${VW} ${H}`);
      const c = clip.color || '#FFFFFF';
      const corners = [[m, m, 1, 1], [VW - m, m, -1, 1], [m, H - m, 1, -1], [VW - m, H - m, -1, -1]]
        .map(([x, y, sx, sy]) => `<path d="M${x + sx * tick} ${y} L${x} ${y} L${x} ${y + sy * tick}" fill="none" stroke="${c}" stroke-opacity="0.8" stroke-width="${sw * 1.8}" stroke-linecap="square"/>`).join('');
      e.innerHTML = `<rect x="${m}" y="${m}" width="${VW - 2 * m}" height="${H - 2 * m}" fill="none" stroke="${c}" stroke-opacity="0.32" stroke-width="${sw}"/>${corners}`;
      e.style.display = 'block'; e.style.filter = 'drop-shadow(0 1px 2px rgba(0,0,0,0.35))';
      return e;
    }
    if (type === 'slate') {  // üslub dəsti: intertitle — tam kadr krem kart (ekspert görünmür, səsi davam edir): kicker, iri serif yazı və ya sıralanmış sətirlər
      const bg = rgba(clip.bg, th.accentSoft || '#F2E4D6'), ink = clip.ink || '#3C262C', acc = clip.accent || th.primaryDeep || '#9E3D5E';
      const s = node(doc, 'div', { width: `${VW}px`, height: `${H}px`, background: bg, position: 'relative', fontFamily: '"Lora","DejaVu Serif",Georgia,serif', color: ink, boxSizing: 'border-box' });
      const rule = Math.max(2, H * 0.0021), mt = H * 0.088;
      [mt, H - mt].forEach((y) => s.append(node(doc, 'div', { position: 'absolute', left: `${VW * 0.1}px`, right: `${VW * 0.1}px`, top: `${y}px`, height: `${rule}px`, background: acc })));
      if (clip.kicker) s.append(node(doc, 'div', { position: 'absolute', left: '0', right: '0', top: `${H * 0.15}px`, textAlign: 'center', fontFamily: font, fontWeight: '700',
        fontSize: `${H * 0.0187}px`, letterSpacing: '0.3em', textTransform: 'uppercase', color: acc }, clip.kicker));
      const body = node(doc, 'div', { position: 'absolute', left: `${VW * 0.08}px`, right: `${VW * 0.08}px`, top: `${H * 0.24}px`, bottom: `${H * 0.22}px`, display: 'flex', flexDirection: 'column',
        justifyContent: 'center', alignItems: 'center', textAlign: 'center', gap: `${fs * 0.5}px` });
      if (clip.items && clip.items.length) {
        const n = shown(clip.items);
        clip.items.forEach((it, i) => {
          if (i > 0) body.append(node(doc, 'div', { width: `${fs * 0.5}px`, height: `${Math.max(2, fs * 0.05)}px`, background: acc, opacity: i < n ? '0.7' : '0' }));
          body.append(node(doc, 'div', { fontWeight: '700', fontSize: `${fs}px`, lineHeight: '1.1', opacity: i < n ? '1' : '0' }, it.text || ''));
        });
      } else body.append(node(doc, 'div', { fontWeight: '700', fontSize: `${fs * (clip.big ? 1.5 : 1)}px`, lineHeight: '1.08', color: clip.big ? acc : ink }, clip.text || ''));
      s.append(body);
      if (clip.line) s.append(node(doc, 'div', { position: 'absolute', left: `${VW * 0.1}px`, right: `${VW * 0.1}px`, bottom: `${H * 0.125}px`, textAlign: 'center', fontStyle: 'italic', fontSize: `${H * 0.0156}px`, color: ink }, clip.line));
      return s;
    }
    if (type === 'viewfinder') {  // kamera vizör effekti: yuxarı küncdə ● REC (yanıb-sönür) və taymkod; YALNIZ yuxarı küncləri tutur, üzə/mərkəzə toxunmur
      const m = VW * (clip.m ?? 0.04), tick = VW * 0.045, t = tl == null ? 0 : tl, fsz = H * 0.0172;
      const wrap = node(doc, 'div', { width: `${VW}px`, height: `${H}px`, position: 'relative', fontFamily: font, color: '#FFFFFF', textShadow: '0 1px 3px rgba(0,0,0,0.55)' });
      const rec = node(doc, 'div', { position: 'absolute', left: `${m + tick * 0.5}px`, top: `${m + tick * 0.5}px`, display: 'flex', alignItems: 'center', gap: `${fsz * 0.5}px`, fontWeight: '700', fontSize: `${fsz}px`, letterSpacing: '0.16em' });
      const on = Math.floor(t / 0.5) % 2 === 0;
      rec.append(node(doc, 'div', { width: `${fsz * 0.8}px`, height: `${fsz * 0.8}px`, borderRadius: '50%', background: '#E5484D', opacity: on ? '1' : '0.18', boxShadow: on ? '0 0 8px rgba(229,72,77,0.75)' : 'none' }));
      rec.append(node(doc, 'div', {}, 'REC'));
      const sec = Math.floor(t + (clip.tc0 || 0)), p2 = (n) => String(n).padStart(2, '0');
      wrap.append(rec, node(doc, 'div', { position: 'absolute', right: `${m + tick * 0.5}px`, top: `${m + tick * 0.5}px`, fontFamily: '"DejaVu Sans Mono",monospace', fontWeight: '700', fontSize: `${fsz}px`, letterSpacing: '0.06em' },
        `00:${p2(Math.floor(sec / 60))}:${p2(sec % 60)}`));
      return wrap;
    }
    if (type === 'veil') {  // yazının arxasında kadrın yuxarısında tam enli, çox yumşaq tünd keçid (kinoda "title-safe" qradiyent) — ləkə yox
      const a = Number(clip.a ?? 0.42);
      return node(doc, 'div', { width: `${VW}px`, height: `${H * (clip.h ?? 0.4)}px`,
        background: `linear-gradient(to bottom, rgba(0,0,0,${a}) 0%, rgba(0,0,0,${a * 0.62}) 35%, rgba(0,0,0,${a * 0.2}) 72%, rgba(0,0,0,0) 100%)` });
    }
    if (type === 'type') {  // üslub dəsti: redaksiya tipoqrafiyası — kartsız böyük yazı, kicker, incə xətt, nömrəli sətirlər
      const fam = clip.font === 'serif' ? '"Lora", "DejaVu Serif", Georgia, serif' : font;
      const w = node(doc, 'div', { ...base, fontFamily: fam, width: `${VW * (clip.w ?? 0.9)}px`, textAlign: clip.align || 'left', lineHeight: '1.02',
        textShadow: clip.shadow === false ? 'none' : '0 1px 2px rgba(0,0,0,0.35), 0 4px 18px rgba(0,0,0,0.28)' });
      if (clip.kicker) w.append(node(doc, 'div', { fontFamily: font, fontSize: `${fs * 0.27}px`, fontWeight: '600', letterSpacing: '0.3em', textTransform: 'uppercase', marginBottom: `${fs * 0.16}px`, lineHeight: '1.2' }, clip.kicker));
      if (clip.rule !== false && clip.kicker) w.append(node(doc, 'div', { width: `${fs * 0.9}px`, height: `${Math.max(2, fs * 0.03)}px`, background: color, margin: clip.align === 'center' ? `0 auto ${fs * 0.22}px auto` : `0 0 ${fs * 0.22}px 0`, opacity: '0.9' }));
      if (clip.italic) w.style.fontStyle = 'italic';
      if (clip.items && clip.items.length && clip.inline) {  // bir sətirdə, nöqtə ilə ayrılmış; hər söz `at` anında görünür
        const n = shown(clip.items);
        const line = node(doc, 'div', { display: 'flex', justifyContent: clip.align === 'center' ? 'center' : 'flex-start', flexWrap: 'wrap', gap: `0 ${fs * 0.5}px` });
        clip.items.forEach((it, i) => {
          if (i > 0) line.append(node(doc, 'span', { opacity: i < n ? '0.7' : '0' }, '·'));
          line.append(node(doc, 'span', { opacity: i < n ? '1' : '0' }, it.text || ''));
        });
        w.append(line);
      } else if (clip.items && clip.items.length) {
        const n = shown(clip.items);
        clip.items.forEach((it, i) => {
          const row = node(doc, 'div', { display: 'flex', alignItems: 'baseline', gap: `${fs * 0.35}px`, margin: `${fs * 0.1}px 0`, opacity: i < n ? '1' : '0', fontSize: `${fs * 0.82}px` });
          row.append(node(doc, 'div', { fontFamily: font, fontSize: `${fs * 0.3}px`, fontWeight: '600', opacity: '0.85' }, String(i + 1).padStart(2, '0')));
          row.append(node(doc, 'div', {}, it.text || ''));
          w.append(row);
        });
      } else w.append(node(doc, 'div', {}, clip.text || ''));
      return w;
    }
    if (type === 'note') {  // üslub dəsti: əl yazısı qeyd — Caveat, əyilmiş; altından xətt / dairə / ox / ✓ işarələri (SVG)
      const NS = 'http://www.w3.org/2000/svg';
      const svg = (inner, css) => { const e = doc.createElementNS(NS, 'svg'); e.setAttribute('viewBox', '0 0 100 100'); e.setAttribute('preserveAspectRatio', 'none');
        Object.assign(e.style, { position: 'absolute', overflow: 'visible', pointerEvents: 'none', ...css }); e.innerHTML = inner; return e; };
      const stroke = `fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" vector-effect="non-scaling-stroke"`;
      const w = node(doc, 'div', { ...base, fontFamily: '"Caveat","DejaVu Sans",cursive', fontWeight: '700', position: 'relative', padding: `${fs * 0.35}px ${fs * 0.5}px`, textAlign: clip.align || 'left',
        transform: `rotate(${clip.rot ?? -3}deg)`, lineHeight: '1.05', textShadow: '0 1px 2px rgba(0,0,0,0.5), 0 3px 14px rgba(0,0,0,0.3)' });
      if (clip.items && clip.items.length) {
        const n = shown(clip.items);
        clip.items.forEach((it, i) => {
          const row = node(doc, 'div', { display: 'flex', alignItems: 'center', gap: `${fs * 0.3}px`, opacity: i < n ? '1' : '0', margin: `${fs * 0.05}px 0` });
          row.append(svg(`<path d="M10 55 L38 85 L92 15" ${stroke}/>`, { position: 'relative', width: `${fs * 0.7}px`, height: `${fs * 0.7}px`, flex: '0 0 auto' }));
          row.append(node(doc, 'div', {}, it.text || ''));
          w.append(row);
        });
      } else w.append(node(doc, 'div', { position: 'relative' }, clip.text || ''));
      const mark = clip.mark || 'none';
      if (mark === 'underline') w.append(svg(`<path d="M2 60 C30 40 55 85 98 45" ${stroke}/>`, { left: `${fs * 0.5}px`, width: `calc(100% - ${fs}px)`, bottom: `${fs * 0.37}px`, height: `${fs * 0.3}px` }));
      if (mark === 'circle') w.append(svg(`<ellipse cx="50" cy="50" rx="48" ry="46" ${stroke}/>`, { left: '0', top: '0', width: '100%', height: '100%' }));
      if (mark === 'arrow') w.append(svg(`<path d="M5 5 C30 10 60 40 85 85 M85 85 L62 78 M85 85 L88 60" ${stroke}/>`, { right: `${-fs * 1.2}px`, bottom: `${-fs * 1.3}px`, width: `${fs * 1.4}px`, height: `${fs * 1.4}px` }));
      return w;
    }
    if (type === 'block') {  // üslub dəsti: rəng bloku — kadrın yuxarısında tam enli rəngli panel (mətn, çip, nömrəli çiplər)
      const bh = H * (clip.h ?? 0.3);
      const b = node(doc, 'div', { ...base, width: `${VW}px`, height: `${bh}px`, background: rgba(clip.bg, th.primary || '#C9577D'), color: clip.color || '#FFFFFF',
        display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', padding: `0 ${VW * 0.07}px`, textAlign: 'left', lineHeight: '1.08', gap: `${fs * 0.22}px` });
      if (clip.chip) b.append(node(doc, 'div', { fontSize: `${fs * 0.42}px`, fontWeight: '800', letterSpacing: '0.12em', padding: `${fs * 0.12}px ${fs * 0.5}px`, borderRadius: '999px', background: rgba(clip.chipBg, th.accentSoft || '#F2E4D6'), color: clip.chipColor || th.primaryDeep || '#9E3D5E' }, clip.chip));
      if (clip.items && clip.items.length) {
        const n = shown(clip.items);
        clip.items.forEach((it, i) => {
          const row = node(doc, 'div', { display: 'flex', alignItems: 'center', gap: `${fs * 0.4}px`, opacity: i < n ? '1' : '0', fontSize: `${fs * 0.9}px` });
          row.append(node(doc, 'div', { width: `${fs * 1.2}px`, height: `${fs * 1.2}px`, borderRadius: '50%', background: rgba(clip.chipBg, th.primaryDeep || '#9E3D5E'), color: '#FFFFFF', fontSize: `${fs * 0.7}px`, display: 'flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 auto' }, String(i + 1)));
          row.append(node(doc, 'div', {}, it.text || ''));
          b.append(row);
        });
      } else b.append(node(doc, 'div', {}, clip.text || ''));
      return b;
    }
    if (type === 'bars') {  // üslub dəsti: sinema zolaqları — yuxarı/aşağı qara zolaq; aşağıda bir böyük söz (söz-söz), yuxarıda irəliləyiş xətti
      const wrap = node(doc, 'div', { width: `${VW}px`, height: `${H}px`, position: 'relative', fontFamily: font, boxSizing: 'border-box' });
      const topH = H * (clip.top ?? 0.05), botH = H * (clip.bottom ?? 0.24), ink = clip.barColor || '#0A0A0C';
      const top = node(doc, 'div', { position: 'absolute', left: '0', top: '0', width: '100%', height: `${topH}px`, background: ink });
      top.append(node(doc, 'div', { position: 'absolute', left: `${VW * 0.045}px`, right: `${VW * 0.045}px`, top: `${topH * 0.45}px`, height: `${Math.max(3, H * 0.003)}px`, background: 'rgba(255,255,255,0.18)' }));
      top.append(node(doc, 'div', { position: 'absolute', left: `${VW * 0.045}px`, width: `${(VW * 0.91) * (clip.progress ?? 0)}px`, top: `${topH * 0.45}px`, height: `${Math.max(3, H * 0.003)}px`, background: clip.accent || th.accent || '#C9577D' }));
      const bot = node(doc, 'div', { position: 'absolute', left: '0', bottom: '0', width: '100%', height: `${botH}px`, background: ink, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: `${fs * 0.1}px`, textAlign: 'center' });
      let word = clip.text || '';
      if (clip.seq && clip.seq.length) { const cur = clip.seq.filter((x) => tl == null || tl >= (x.s || 0)); word = (cur[cur.length - 1] || clip.seq[0]).w; }
      bot.append(node(doc, 'div', { fontSize: `${fs}px`, fontWeight: '800', color: clip.color || '#FFFFFF', lineHeight: '1', letterSpacing: '0.01em' }, word));
      if (clip.sub) bot.append(node(doc, 'div', { fontSize: `${fs * 0.42}px`, fontWeight: '700', color: clip.accent || th.accent || '#C9577D' }, clip.sub));
      wrap.append(top, bot);
      return wrap;
    }
    if (type === 'caption') {
      const wrap = node(doc, 'div', { ...base, maxWidth: `${H * (clip.maxW ?? 0.52)}px`, padding: `${fs * 0.15}px ${fs * 0.3}px`,
        borderRadius: `${fs * (clip.radius ?? 0.3)}px`, background: rgba(clip.bg, 'transparent'), textAlign: clip.align === 'left' ? 'left' : 'center' });
      const words = clip.words && clip.words.length ? clip.words : String(clip.text || '').split(/\s+/).map((w) => ({ w, s: 0, e: 0 }));
      const stroke = clip.bg && clip.bg !== 'none' ? null : (clip.stroke || 'rgba(0,0,0,0.85)');
      words.forEach((w, i) => {
        const spoken = clip.plain || tl == null || tl >= w.s;  // plain: sadə altyazı (dərs) — söz-söz effekti yoxdur
        const next = words[i + 1];
        const active = !clip.plain && tl != null && tl >= w.s && (next ? tl < next.s : true);
        const sp = node(doc, 'span', { display: 'inline-block', margin: `0 ${fs * 0.13}px`, opacity: spoken ? '1' : '0.55',
          color: active ? (clip.activeColor || th.accent || '#F2C94C') : color }, w.w);
        if (stroke) { sp.style.webkitTextStroke = `${Math.max(2, fs * 0.09)}px ${stroke}`; sp.style.paintOrder = 'stroke fill'; }
        wrap.append(sp);
      });
      if (clip.underline) {  // sola düzlənmiş Reels yazısı: altında qısa vurğu xətti
        const outer = node(doc, 'div', { display: 'inline-block', textAlign: clip.align === 'left' ? 'left' : 'center' });
        outer.append(wrap);
        outer.append(node(doc, 'div', { width: `${fs * 1.3}px`, height: `${Math.max(3, fs * 0.1)}px`, borderRadius: '99px',
          background: clip.activeColor || th.accent || '#F2C94C', margin: clip.align === 'left' ? `${fs * 0.18}px 0 0 ${fs * 0.13}px` : `${fs * 0.18}px auto 0` }));
        return outer;
      }
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
    if (type === 'lower') {  // ad-titul lövhəsi (bölüm açılışı): ad qalın, altında titul; solda vurğu xətti
      const box = node(doc, 'div', { ...base, textAlign: 'left', display: 'flex', alignItems: 'stretch', gap: `${fs * 0.5}px`,
        padding: `${fs * 0.45}px ${fs * 0.9}px ${fs * 0.5}px ${fs * 0.6}px`, borderRadius: `${fs * 0.25}px`,
        background: rgba(clip.bg, 'rgba(255,255,255,0.93)'), boxShadow: '0 6px 18px rgba(0,0,0,0.18)' });
      box.append(node(doc, 'div', { width: `${Math.max(4, fs * 0.16)}px`, borderRadius: '99px', background: clip.accent || th.primary || '#C9577D', flex: '0 0 auto' }));
      const col = node(doc, 'div', {});
      col.append(node(doc, 'div', { fontWeight: '800', fontSize: `${fs}px`, lineHeight: '1.15' }, clip.text || ''));
      if (clip.sub) col.append(node(doc, 'div', { fontWeight: '500', fontSize: `${fs * 0.6}px`, opacity: '0.85', marginTop: `${fs * 0.14}px` }, clip.sub));
      box.append(col);
      return box;
    }
    if (type === 'choice') {  // seçim: 2–3 variant; `at` anında doğrusu (correct) yaşıl çərçivə + ✓, qalanları solğun
      const reveal = tl == null || tl >= (clip.at ?? 1.5);
      // padding: ✓ nişanı və böyüyən kart elementin sərhədindən çıxmasın (PNG kəsilməsin)
      const wrap = node(doc, 'div', { ...base, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: `${fs * 0.55}px`, padding: `${fs * 0.7}px` });
      if (clip.heading) wrap.append(node(doc, 'div', { fontWeight: '800', fontSize: `${fs * 0.85}px`, padding: `${fs * 0.25}px ${fs * 0.75}px`, borderRadius: '999px',
        background: rgba(clip.bg, rgba(`${th.primary || '#222222'}@0.92`)), color: th.text || '#FFFFFF' }, clip.heading));
      const row = node(doc, 'div', { display: 'flex', gap: `${fs * 0.55}px`, justifyContent: 'center', alignItems: 'flex-end' });
      (clip.items || []).forEach((it, i) => {
        const ok = reveal && i === clip.correct;
        const dim = reveal && i !== clip.correct;
        const card = node(doc, 'div', { position: 'relative', width: `${fs * 5.2}px`, padding: `${fs * 0.35}px`, borderRadius: `${fs * 0.4}px`,
          background: 'rgba(255,255,255,0.97)', color: '#222222', border: `${Math.max(3, fs * 0.14)}px solid ${ok ? '#2EB872' : 'rgba(0,0,0,0.08)'}`,
          boxShadow: ok ? `0 0 ${fs * 0.9}px rgba(46,184,114,0.75)` : '0 4px 14px rgba(0,0,0,0.18)', opacity: dim ? '0.45' : '1', transform: ok ? 'scale(1.06)' : 'none' });
        if (it.img) card.append(node(doc, 'div', { width: '100%', height: `${fs * 4.2}px`, borderRadius: `${fs * 0.25}px`, background: `center/cover no-repeat url("${it.img}")`, marginBottom: `${fs * 0.25}px` }));
        card.append(node(doc, 'div', { fontSize: `${fs * 0.68}px`, fontWeight: '700', lineHeight: '1.2' }, it.text || ''));
        if (ok) card.append(node(doc, 'div', { position: 'absolute', top: `${-fs * 0.45}px`, right: `${-fs * 0.45}px`, width: `${fs * 1.2}px`, height: `${fs * 1.2}px`,
          borderRadius: '50%', background: '#2EB872', color: '#FFFFFF', fontSize: `${fs * 0.8}px`, fontWeight: '900', display: 'flex', alignItems: 'center', justifyContent: 'center' }, '✓'));
        row.append(card);
      });
      wrap.append(row);
      return wrap;
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
      lower: { size: 0.034, weight: 800, color: th.primaryDeep || '#222222' },
      choice: { size: 0.045, weight: 700, color: '#222222' },
      type: { size: 0.056, weight: 800, color: '#FFFFFF' },
      note: { size: 0.062, weight: 700, color: '#FFFFFF' },
      block: { size: 0.046, weight: 800, color: '#FFFFFF' },
      bars: { size: 0.05, weight: 800, color: '#FFFFFF' },
      veil: { size: 0.03, weight: 400, color: '#FFFFFF' },
      frame: { size: 0.03, weight: 400, color: '#FFFFFF' },
      slate: { size: 0.06, weight: 700, color: '#3C262C' },
      viewfinder: { size: 0.03, weight: 700, color: '#FFFFFF' },
    })[type] || { size: 0.06, weight: 700, color: '#FFFFFF' };
  }

  /** Altyazı/siyahı üçün vəziyyət dəyişmə anları (element daxili vaxtında) — render bu anlarda PNG dəyişir. */
  function statePoints(clip) {
    if (clip.type === 'caption' && clip.plain) return [0];
    if (clip.type === 'caption') return [0, ...(clip.words || []).map((w) => w.s)].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b);
    if (clip.type === 'viewfinder') { const n = Math.floor((clip.srcOut - clip.srcIn) / 0.5); return Array.from({ length: n + 1 }, (_, i) => i * 0.5).filter((v) => v < clip.srcOut - clip.srcIn); }
    if (clip.type === 'bars' && clip.seq) return [0, ...clip.seq.map((w) => w.s || 0)].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b);
    if (['list', 'type', 'note', 'block', 'slate'].includes(clip.type) && clip.items) return [0, ...clip.items.map((it) => it.at || 0)].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b);
    if (clip.type === 'list') return [0, ...(clip.items || []).map((it) => it.at || 0)].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b);
    if (clip.type === 'choice') return [0, clip.at ?? 1.5];
    return [0];
  }

  // Standart yer (x, y mərkəz, 0..1) — render (graphics.py DEFAULT_XY) ilə eyni
  const DEFAULT_XY = { caption: [0.5, 0.74], title: [0.5, 0.14], section: [0.5, 0.22], emphasis: [0.5, 0.62], list: [0.5, 0.42], card: [0.5, 0.42],
    offer: [0.5, 0.58], cta: [0.5, 0.585], badge: [0.5, 0.215], lower: [0.24, 0.82], choice: [0.5, 0.45],
    type: [0.5, 0.17], note: [0.5, 0.17], block: [0.5, 0.15], bars: [0.5, 0.5], veil: [0.5, 0.2], frame: [0.5, 0.5], slate: [0.5, 0.5], viewfinder: [0.5, 0.5] };  // reklam kartları üzün altında
  function pos(clip) { const d = DEFAULT_XY[clip.type] || [0.5, 0.5]; return [clip.x ?? d[0], clip.y ?? d[1]]; }

  root.MG = { ANIMS, animState, build, defaults, statePoints, rgba, pos, DEFAULT_XY };
})(typeof window !== 'undefined' ? window : globalThis);
