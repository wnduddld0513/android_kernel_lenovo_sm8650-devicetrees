#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# (C) 2026 The LineageOS Project
"""Semantic comparison of two overlay blobs (dtbo entries).

usage: dtbo_cmp.py A.dtbo B.dtbo [--limit N] [--summary]
Fragments are matched by their canonical content (see dtbolib); the remaining
ones are paired by target and printed as line differences.
exit status 0 when identical.
"""
import sys, os, collections, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtbolib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a'); ap.add_argument('b')
    ap.add_argument('--limit', type=int, default=30)
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--ignore-root', action='append', default=[])
    ap.add_argument('--effect', action='store_true', help='compare the flattened effect, not the fragment structure')
    o = ap.parse_args()
    pa, fa = dtbolib.normalize(open(o.a, 'rb').read())
    pb, fb = dtbolib.normalize(open(o.b, 'rb').read())
    rc = 0
    if o.effect:
        def flat(fr):
            d = {}
            for x in fr:
                for l in x['lines']:
                    k, _, v = l.partition('=')
                    d[(x['target'], k)] = v
            return d
        da, db = flat(fa), flat(fb)
        for k in sorted(set(pa) | set(pb)):
            if k in ('name',): continue
            if pa.get(k) != pb.get(k):
                rc = 1; print('root property %s differs' % k)
        oa = sorted(set(da) - set(db)); ob = sorted(set(db) - set(da))
        dv = sorted(k for k in set(da) & set(db) if da[k] != db[k])
        print('effect: A=%d B=%d keys; A-only=%d B-only=%d value-diff=%d' % (len(da), len(db), len(oa), len(ob), len(dv)))
        if oa or ob or dv: rc = 1
        if not o.summary:
            for k in oa[:o.limit]: print('A-only', k[0], k[1][:200], '=', da[k][:80])
            for k in ob[:o.limit]: print('B-only', k[0], k[1][:200], '=', db[k][:80])
            for k in dv[:o.limit]: print('diff', k[0], k[1][:200], '\n   A', da[k][:120], '\n   B', db[k][:120])
        return rc
    for k in sorted(set(pa) | set(pb)):
        if k in o.ignore_root or k in ('name',): continue
        if pa.get(k) != pb.get(k):
            rc = 1; print('root property %s differs' % k)
            if not o.summary: print('   A', pa.get(k)); print('   B', pb.get(k))
    ca = collections.Counter(x['hash'] for x in fa); cb = collections.Counter(x['hash'] for x in fb)
    ra = [x for x in fa if ca[x['hash']] > cb[x['hash']]]
    rb = [x for x in fb if cb[x['hash']] > ca[x['hash']]]
    # drop surplus duplicates only once
    seen = collections.Counter()
    ra2 = []
    for x in ra:
        seen[x['hash']] += 1
        if seen[x['hash']] > cb[x['hash']]: ra2.append(x)
    seen = collections.Counter(); rb2 = []
    for x in rb:
        seen[x['hash']] += 1
        if seen[x['hash']] > ca[x['hash']]: rb2.append(x)
    print('fragments: A=%d B=%d identical=%d  A-only=%d B-only=%d  root-props-differ=%s' % (len(fa), len(fb), sum((ca & cb).values()), len(ra2), len(rb2), 'yes' if rc else 'no'))
    if ra2 or rb2: rc = 1
    if not o.summary:
        used = set()
        for x in ra2:
            best = None
            for j, y in enumerate(rb2):
                if j in used: continue
                sc = (y['target'] == x['target']) * 1000 + len(set(x['lines']) & set(y['lines']))
                if best is None or sc > best[0]: best = (sc, j, y)
            sa = set(x['lines'])
            if best and best[0] >= 1000:
                used.add(best[1]); sb = set(best[2]['lines'])
                print('~ %s: %d lines only in A, %d only in B' % (x['target'], len(sa - sb), len(sb - sa)))
                for l in sorted(sa - sb)[:o.limit]: print('   A', l[:220])
                for l in sorted(sb - sa)[:o.limit]: print('   B', l[:220])
            else:
                print('- A-only fragment %s (%d lines) e.g. %s' % (x['target'], len(sa), x['lines'][0][:120] if x['lines'] else ''))
        for j, y in enumerate(rb2):
            if j not in used: print('+ B-only fragment %s (%d lines) e.g. %s' % (y['target'], len(y['lines']), y['lines'][0][:120] if y['lines'] else ''))
    return rc

if __name__ == '__main__':
    sys.exit(main())
