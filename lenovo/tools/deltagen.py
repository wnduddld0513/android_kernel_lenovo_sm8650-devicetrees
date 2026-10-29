#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# (C) 2026 The LineageOS Project
"""Write the source that turns tree B (built from the Qualcomm sources) into tree A (stock).

usage: deltagen.py STOCK.dtb BUILT.dtb OUT.dtsi [--skip PATH-PREFIX]...
Added nodes and changed/added properties are written as &{/path} blocks.
Nodes/properties that exist only in B cannot be expressed by an overlay; they
are listed on stderr and must be removed in the Qualcomm sources.
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fdtlib, dtcompare as D, dtb2dts as G

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stock'); ap.add_argument('built'); ap.add_argument('out')
    ap.add_argument('--skip', action='append', default=[])
    ap.add_argument('--header', default='')
    o = ap.parse_args()
    ta, tb = G.Tree(o.stock), G.Tree(o.built)
    oa, ob, d = D.compare(ta.root, tb.root)
    blocks = []
    skip = lambda p: p.startswith('/__') or any(p.startswith(s) for s in o.skip)
    for p in D.top_only(oa):
        if skip(p): continue
        parent = p.rsplit('/', 1)[0] or '/'
        blocks.append((p, ['&{%s} {' % parent] + ['\t' + l if l else l for l in G.render_node(ta, ta.nodes[p], 0)] + ['};']))
    byn = {}
    for (p, k, kind, _) in d:
        if skip(p): continue
        if kind.startswith('only-B'):
            sys.stderr.write('REMOVE %s : %s\n' % (p, k)); continue
        byn.setdefault(p, []).append(k)
    for p in D.top_only(ob):
        if not skip(p): sys.stderr.write('REMOVE-NODE %s\n' % p)
    for p, ks in sorted(byn.items()):
        n = ta.nodes[p]
        body = ['\t' + G.render_prop(ta, k, n.prop(k)) for k in ks]
        blocks.append((p, ['&{%s} {' % p] + body + ['};']))
    blocks.sort(key=lambda b: b[0])
    with open(o.out, 'w') as f:
        f.write(o.header)
        for _, ls in blocks:
            f.write('\n'.join(ls) + '\n\n')

if __name__ == '__main__':
    main()
