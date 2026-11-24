"""Whisper söz vaxtlarını səssizlik aralıqlarına görə düzəlt + səssizlik əsaslı seqmentlər qur.
İstifadə: prep.py <pid-nömrə> <plan.json> keep='[[a,b],...]'"""
import json, glob, os, sys
n, plan, keep = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
a = json.load(open(glob.glob(os.path.expanduser(f'~/montaj-data/projects/xeyyam-yeni-{n}/analysis/*.json'))[0]))
sil = [(x, y) for x, y in a['silences'] if y - x >= 0.45]
W = []
for w in a['words']:
    s, e = w['s'], w['e']
    for x, y in sil:
        if x <= s < y: s = y - 0.10
    for x, y in sil:
        if s < x and x < e <= y + 0.05: e = x + 0.12
        elif s < x and e > y: e = x + 0.12  # söz səssizliyi əhatə edir: əvvəlki hissədə qalır
    W.append({"type": "word", "text": w['w'], "start": round(s, 3), "end": round(max(e, s + 0.08), 3)})
json.dump({"words": W}, open(f'w{n}.json', 'w'), ensure_ascii=False)
segs = []
for a0, b0 in keep:
    cur = a0
    for x, y in sil:
        if x > cur + 0.3 and y < b0:
            segs.append([cur, x + 0.18]); cur = y - 0.14
    segs.append([cur, b0])
segs = [s for s in segs if any(w['start'] >= s[0] - 0.02 and w['end'] <= s[1] + 0.02 for w in W)]
p = json.load(open(plan)); z = p.get('zooms', [1.0, 1.18]); p.pop('keep', None); p['words'] = f'w{n}.json'
p['segs'] = [[round(s, 2), round(e, 2), z[i % 2]] for i, (s, e) in enumerate(segs)]
json.dump(p, open(plan, 'w'), ensure_ascii=False, indent=1)
print(len(p['segs']), 'seqment', round(sum(e - s for s, e, _ in p['segs']), 1), 's')
