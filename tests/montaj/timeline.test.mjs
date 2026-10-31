// node --test tests/montaj/timeline.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import * as TL from '../../montaj/ui/timeline.js';

const media = (id, dur, extra = {}) => ({ id, name: `${id}.mp4`, file: `media/originals/${id}.mp4`, duration: dur, hasVideo: true, hasAudio: true, width: 1280, height: 720, fps: 30, ...extra });

function base() {
  let p = TL.newProject({ id: 't', title: 'Test' });
  p = TL.addMedia(p, media('A', 10));
  p = TL.addMedia(p, media('B', 6));
  return p;
}

const vids = (p) => TL.videoClips(p);
const audioOf = (p, v) => TL.partnerOf(p, v);

test('addMedia: video + bağlı səs, maqnitli ardıcıllıq', () => {
  const p = base();
  assert.equal(vids(p).length, 2);
  const [a, b] = vids(p);
  const lay = TL.layout(p);
  assert.deepEqual(lay.get(a.id), { start: 0, end: 10 });
  assert.deepEqual(lay.get(b.id), { start: 10, end: 16 });
  assert.equal(audioOf(p, a).linkedTo, a.id);
  assert.deepEqual(lay.get(audioOf(p, b).id), { start: 10, end: 16 });
  assert.equal(TL.duration(p), 16);
});

test('split: video və öz səsi birlikdə bölünür, mənbə istinadları düzgündür', () => {
  const p0 = base();
  const a = vids(p0)[0];
  const p = TL.split(p0, a.id, 4);
  const v = vids(p);
  assert.equal(v.length, 3);
  assert.deepEqual([v[0].srcIn, v[0].srcOut, v[1].srcIn, v[1].srcOut], [0, 4, 4, 10]);
  for (const c of v.slice(0, 2)) {
    const au = audioOf(p, c);
    assert.ok(au, 'hər video hissəsinin öz səsi var');
    assert.equal(au.srcIn, c.srcIn);
    assert.equal(au.srcOut, c.srcOut);
  }
  assert.equal(TL.duration(p), 16);
  // orijinal layihə dəyişməyib
  assert.equal(vids(p0).length, 2);
});

test('trim: kəsilmiş material kənarı uzatmaqla geri qayıdır', () => {
  let p = base();
  const a = vids(p)[0];
  p = TL.split(p, a.id, 4);
  const right = vids(p)[1];
  p = TL.deleteClip(p, right.id); // 4..10 silindi
  assert.equal(TL.duration(p), 10);
  const left = vids(p)[0];
  assert.equal(left.srcOut, 4);
  // sağ kənarı 8-ə qədər uzat: 4..8 materialı geri gəlir
  p = TL.trim(p, left.id, 'out', 8);
  const l2 = TL.clipById(p, left.id);
  assert.equal(l2.srcOut, 8);
  assert.equal(audioOf(p, l2).srcOut, 8, 'səs də birlikdə uzanır');
  // mənbə faylından artıq uzatmaq olmaz
  p = TL.trim(p, left.id, 'out', 50);
  assert.equal(TL.clipById(p, left.id).srcOut, 10);
  // sol kənar 0-dan geri gedə bilməz
  p = TL.trim(p, left.id, 'in', -5);
  assert.equal(TL.clipById(p, left.id).srcIn, 0);
  assert.ok(TL.clipById(p, left.id).manual, 'əl ilə düzəliş işarələnir');
});

test('moveVideo: sıra dəyişir, bağlı səs videonu izləyir', () => {
  let p = base();
  const [a, b] = vids(p);
  p = TL.moveVideo(p, b.id, 0);
  const lay = TL.layout(p);
  assert.equal(lay.get(b.id).start, 0);
  assert.equal(lay.get(a.id).start, 6);
  assert.equal(lay.get(audioOf(p, a).id).start, 6);
});

test('unlink: səs ayrılır, yerində qalır, sonra ayrıca hərəkət edir', () => {
  let p = base();
  const b = vids(p)[1];
  const au = audioOf(p, b);
  p = TL.unlink(p, b.id);
  const au2 = TL.clipById(p, au.id);
  assert.equal(au2.linkedTo, undefined);
  assert.equal(au2.start, 10);
  p = TL.moveFree(p, au.id, 2);
  assert.equal(TL.layout(p).get(au.id).start, 2);
  assert.equal(TL.layout(p).get(b.id).start, 10, 'video yerində qalır');
  // ayrılmış səsi kəsmək videoya təsir etmir
  p = TL.trim(p, au.id, 'out', 3);
  assert.equal(TL.clipById(p, b.id).srcOut, 6);
});

test('bağlı səsi ayırmadan sərbəst hərəkət etdirmək olmur', () => {
  const p = base();
  const au = audioOf(p, vids(p)[0]);
  assert.throws(() => TL.moveFree(p, au.id, 3), /ayırın/);
});

test('qatlar: musiqi, effekt, mətn ayrıdır', () => {
  let p = base();
  p = TL.addMedia(p, { id: 'M', name: 'm.mp3', file: 'x', duration: 30, hasVideo: false, hasAudio: true }, { targetTrack: 'm1', at: 1 });
  p = TL.addMedia(p, { id: 'X', name: 'x.wav', file: 'x', duration: 1, hasVideo: false, hasAudio: true }, { targetTrack: 's1', at: 5 });
  p = TL.addText(p, { start: 2, dur: 3, text: 'Salam' });
  const kinds = p.clips.map((c) => TL.trackKind(p, c)).sort();
  assert.deepEqual([...new Set(kinds)].sort(), ['music', 'sfx', 'speech', 'text', 'video']);
  assert.equal(TL.duration(p), 31);
  const a = TL.activeAt(p, 2.5);
  assert.equal(a.text.length, 1);
  assert.ok(a.video);
});

test('undo/redo tarixçəsi', () => {
  const p0 = base();
  const h = new TL.History(p0);
  const p1 = TL.split(p0, vids(p0)[0].id, 3);
  h.commit(p1);
  const p2 = TL.deleteClip(p1, vids(p1)[0].id);
  h.commit(p2);
  assert.equal(vids(h.present).length, 2);
  assert.equal(vids(h.undo()).length, 3);
  assert.equal(vids(h.undo()).length, 2);
  assert.equal(h.undo(), null);
  assert.equal(vids(h.redo()).length, 3);
  assert.equal(vids(h.redo()).length, 2);
  assert.equal(h.redo(), null);
});

test('AI təklifi: təsdiqdən əvvəl heç nə dəyişmir, əl ilə düzəlişlər qorunur', () => {
  let p = base();
  const [a, b] = vids(p);
  // B əl ilə kəsilib
  p = TL.trim(p, b.id, 'in', 1);
  const proposal = {
    id: 'p1', kind: 'silence', title: 't',
    items: [
      { clipId: a.id, expect: { srcIn: 0, srcOut: 10 }, keep: [[0, 3], [5, 10]] },
      { clipId: b.id, expect: { srcIn: 0, srcOut: 6 }, keep: [[0, 2]] },
    ],
  };
  const withProp = TL.addProposal(p, proposal);
  assert.equal(vids(withProp).length, 2, 'təklif əlavə etmək montajı dəyişmir');
  assert.equal(TL.duration(withProp), TL.duration(p));
  const r = TL.applyProposal(withProp, proposal);
  assert.deepEqual(r.applied, [a.id]);
  assert.equal(r.skipped[0].clipId, b.id);
  assert.match(r.skipped[0].reason, /əl ilə/);
  const v = vids(r.project);
  assert.equal(v.length, 3);
  assert.deepEqual(v.map((c) => [c.srcIn, c.srcOut]), [[0, 3], [5, 10], [1, 6]]);
  for (const c of v.slice(0, 2)) assert.equal(audioOf(r.project, c).srcIn, c.srcIn);
  assert.equal(r.project.proposals[0].status, 'applied');
  // AI hissələri sonradan yenə geri uzadıla bilər
  const first = v[0];
  const back = TL.trim(r.project, first.id, 'out', 5);
  assert.equal(TL.clipById(back, first.id).srcOut, 5);
});

test('təklifdən sonra dəyişmiş klip atlanır', () => {
  let p = base();
  const a = vids(p)[0];
  const proposal = { id: 'p2', items: [{ clipId: a.id, expect: { srcIn: 0, srcOut: 9 }, keep: [[0, 2]] }] };
  const r = TL.applyProposal(p, proposal);
  assert.equal(r.applied.length, 0);
  assert.match(r.skipped[0].reason, /dəyişib/);
});

test('JSON serializasiyası və yenidən açma eyni nəticə verir', () => {
  let p = base();
  p = TL.split(p, vids(p)[0].id, 2.5);
  const re = JSON.parse(JSON.stringify(p));
  assert.deepEqual([...TL.layout(re)], [...TL.layout(p)]);
});

test('applyStoryboard: yalnız təsdiqdə tətbiq olunur, əl ilə düzəldilmiş mənbə qorunur, subtitr söz vaxtına uyğundur', () => {
  let p = TL.migrate(base());
  const [a, b] = vids(p);
  p = TL.trim(p, b.id, 'out', 5); // B əl ilə düzəldilib
  const words = [{ w: 'Salam', s: 1.0, e: 1.4 }, { w: 'dostlar', s: 1.5, e: 2.0 }, { w: 'bu', s: 2.1, e: 2.2 }, { w: 'gün', s: 2.3, e: 2.6 }, { w: 'danışaq', s: 2.7, e: 3.2 }];
  const sb = {
    subtitles: true,
    cards: [
      { id: 'c1', mediaId: 'A', srcIn: 0.8, srcOut: 3.5, include: true, onScreenText: 'Açılış', words },
      { id: 'c2', mediaId: 'A', srcIn: 6, srcOut: 8, include: false, words: [] },
      { id: 'c3', mediaId: 'B', srcIn: 0, srcOut: 2, include: true, words: [] },
    ],
  };
  const r = TL.applyStoryboard(p, sb, { frames: { A: { aspect: '9:16', mode: 'auto', keys: [{ t: 0, cx: 0.4, cy: 0.5 }] } } });
  const v = TL.videoClips(r.project);
  assert.equal(r.skipped.length, 1);
  assert.equal(r.skipped[0].mediaId, 'B');
  assert.ok(v.some((c) => c.media === 'B' && c.srcOut === 5 && c.manual), 'əl ilə düzəldilmiş B toxunulmaz');
  const ai = v.filter((c) => c.media === 'A');
  assert.equal(ai.length, 1, 'söndürülmüş kart tətbiq olunmur');
  assert.deepEqual([ai[0].srcIn, ai[0].srcOut], [0.8, 3.5]);
  assert.equal(ai[0].frame.mode, 'auto');
  assert.ok(TL.partnerOf(r.project, ai[0]), 'video öz səsi ilə');
  const lay = TL.layout(r.project);
  const subs = r.project.clips.filter((c) => c.track === 'c1');
  assert.equal(subs.length, 2);
  const s0 = lay.get(subs[0].id);
  assert.ok(Math.abs(s0.start - (lay.get(ai[0].id).start + (1.0 - 0.8))) < 1e-6, 'subtitr sözün başladığı anda');
  assert.ok(r.project.clips.some((c) => c.track === 't1' && c.text === 'Açılış'));
  // kəsilmiş material yenə geri qaytarıla bilər
  const back = TL.trim(r.project, ai[0].id, 'in', 0);
  assert.equal(TL.clipById(back, ai[0].id).srcIn, 0);
});
