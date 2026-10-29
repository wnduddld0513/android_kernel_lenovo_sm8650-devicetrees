#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
"""Split stock dtbo entries into per-function dtsi files.

usage: split_dtbo.py OUTDIR NAME=ENTRY.dtbo:CLASS=A-B[,C-D];CLASS=... ...

Every CLASS becomes <NAME>-<class>.dtsi, or common-<class>.dtsi when all
entries produce the same text.  The root properties are written to
<NAME>.rootprops (printed as a dts root node) for the top level .dts.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtbo2dts as T

HDR = ('// SPDX-License-Identifier: GPL-2.0-only\n'
       '/*\n * (C) 2026 The LineageOS Project\n *\n'
       ' * %s\n'
       ' * Reconstructed from the Lenovo TB520FU stock dtbo (ZUI 18.5.10.037).\n */\n\n')

def frag_texts(c):
    out = {}
    for f in c.root.children:
        if not f.name.startswith('fragment'): continue
        idx = f.name.split('@')[1]
        fp = f.path()
        tp = f.prop('target-path')
        tgt = '&{%s}' % tp.rstrip(b'\0').decode() if tp is not None else '&' + c.ext[(fp, 'target', 0)]
        ov = f.child('__overlay__')
        lines = ['%s {' % tgt]
        for k, v in ov.props:
            if k != 'name': lines.append('\t' + T.prop_text(c, ov.path(), k, v))
        for ch in ov.children:
            lines.append('')
            lines += T.node_text(c, ch, 1)
        lines.append('};')
        out[int(idx)] = '\n'.join(lines) + '\n'
    return out

def parse_spec(s):
    r = {}
    for part in s.split(';'):
        k, _, v = part.partition('=')
        rng = []
        for x in v.split(','):
            a, _, b = x.partition('-'); rng += list(range(int(a), int(b or a) + 1))
        r[k] = rng
    return r

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    ents = {}
    for a in sys.argv[2:]:
        name, _, rest = a.partition('=')
        path, _, spec = rest.partition(':')
        c = T.Ctx(open(path, 'rb').read(), 'tb_l')
        ft = frag_texts(c)
        spec = parse_spec(spec)
        used = set()
        classes = {}
        for k, idxs in spec.items():
            classes[k] = '\n'.join(ft[i] for i in idxs if i in ft)
            used |= set(idxs)
        missing = sorted(set(ft) - used)
        if missing: sys.stderr.write('%s: unassigned fragments %s\n' % (name, missing))
        ents[name] = classes
        roots = ['/ {']
        for k, v in c.root.props:
            if k != 'name': roots.append('\t' + T.prop_text(c, '/', k, v))
        roots.append('};')
        open('%s/%s.rootprops' % (out, name), 'w').write('\n'.join(roots) + '\n')
    names = list(ents)
    allc = []
    for n in names:
        for k in ents[n]:
            if k not in allc: allc.append(k)
    for k in allc:
        texts = {n: ents[n].get(k) for n in names if k in ents[n]}
        vals = set(texts.values())
        if len(vals) == 1 and len(texts) == len(names):
            fn = 'common-%s.dtsi' % k
            open('%s/%s' % (out, fn), 'w').write(HDR % ('Lenovo TB520 family: %s' % k) + list(vals)[0])
            sys.stdout.write('%s common %s\n' % (k, ','.join(names)))
        else:
            for n, t in texts.items():
                fn = '%s-%s.dtsi' % (n, k)
                open('%s/%s' % (out, fn), 'w').write(HDR % ('%s: %s' % (n, k)) + t)
                sys.stdout.write('%s %s %d lines\n' % (k, n, t.count('\n')))

if __name__ == '__main__':
    main()
