#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# (C) 2026 The LineageOS Project
"""Semantic comparison of two flattened device trees (base dtb).

Phandle values are not compared numerically: a 32-bit cell that is a valid
phandle in both blobs is compared by the path of the node it points to.

usage: dtcompare.py A.dtb B.dtb [--ignore-prop NAME]... [--summary]
exit status 0 when the trees are semantically identical.
"""
import struct, sys, argparse, collections
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import fdtlib


def index(root):
    nodes = {}
    ph = {}
    for n in fdtlib.walk(root):
        nodes[n.path()] = n
        v = n.prop('phandle')
        if v is None: v = n.prop('linux,phandle')
        if v is not None and len(v) == 4:
            ph[struct.unpack('>I', v)[0]] = n.path()
    return nodes, ph


def cells(v):
    return list(struct.unpack('>%dI' % (len(v) // 4), v)) if len(v) % 4 == 0 else None


def propdiff(va, vb, pha, phb):
    if va == vb:
        # identical bytes: numerically equal cells are assumed to be the same value
        return None
    ca, cb = cells(va), cells(vb)
    if ca is None or cb is None or len(ca) != len(cb):
        return 'value'
    for x, y in zip(ca, cb):
        if x == y:
            continue
        if x in pha and y in phb:
            if pha[x] == phb[y]: continue
            return 'phandle-target %s != %s' % (pha[x], phb[y])
        return 'value'
    return None


def fmt(v):
    if v and v[-1] == 0 and all(32 <= c < 127 or c == 0 for c in v):
        return '"' + v[:-1].decode().replace('\0', '","') + '"'
    c = cells(v)
    if c is not None: return '<' + ' '.join('%#x' % x for x in c) + '>'
    return '[' + v.hex() + ']'


def compare(a, b, ignore=(), out=None):
    na, pha = index(a); nb, phb = index(b)
    only_a = sorted(set(na) - set(nb)); only_b = sorted(set(nb) - set(na))
    diffs = []
    for p in sorted(set(na) & set(nb)):
        da = dict(na[p].props); db = dict(nb[p].props)
        for k in sorted(set(da) | set(db)):
            if k in ignore or k in ('phandle', 'linux,phandle'): continue
            if k not in db: diffs.append((p, k, 'only-A', fmt(da[k])[:100]))
            elif k not in da: diffs.append((p, k, 'only-B', fmt(db[k])[:100]))
            else:
                d = propdiff(da[k], db[k], pha, phb)
                if d: diffs.append((p, k, d, fmt(da[k])[:60] + ' | ' + fmt(db[k])[:60]))
        # property order is not significant; child order is not either
    return only_a, only_b, diffs


def top_only(paths):
    s = set(paths); r = []
    for p in paths:
        q = p.rsplit('/', 1)[0] or '/'
        if q not in s: r.append(p)
    return r


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('a'); ap.add_argument('b')
    ap.add_argument('--ignore-prop', action='append', default=[])
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--limit', type=int, default=40)
    o = ap.parse_args()
    a = fdtlib.parse(open(o.a, 'rb').read()); b = fdtlib.parse(open(o.b, 'rb').read())
    oa, ob, d = compare(a, b, o.ignore_prop)
    ta, tb = top_only(oa), top_only(ob)
    kc = collections.Counter(x[2].split(' ')[0] for x in d)
    print('nodes only in A: %d (%d subtree roots); only in B: %d (%d roots); property diffs: %d %s' % (len(oa), len(ta), len(ob), len(tb), len(d), dict(kc)))
    if not o.summary:
        for p in ta[:o.limit]: print('A-only', p)
        for p in tb[:o.limit]: print('B-only', p)
        for x in d[:o.limit]: print('diff', *x)
    sys.exit(0 if not (oa or ob or d) else 1)
