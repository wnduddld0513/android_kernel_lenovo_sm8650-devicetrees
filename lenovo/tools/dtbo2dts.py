#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# (C) 2026 The LineageOS Project
"""Turn (a range of) the fragments of an overlay blob back into source.

usage: dtbo2dts.py ENTRY.dtbo [--frags A-B] [--root] [--labels PREFIX]

Writes `&label { ... };` blocks (or `&{/path}` for target-path fragments) in
fragment order.  References to labels of the base tree come from __fixups__,
references to nodes inside the overlay come from __local_fixups__ and are
written as labels on those nodes.  Used to reconstruct the Lenovo specific
overlay sources from the stock dtbo.
"""
import sys, os, struct, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fdtlib, dtbolib


class Ctx:
    def __init__(self, blob, prefix):
        self.root = fdtlib.parse(blob)
        self.ext, self.loc = dtbolib._fixups(self.root)
        self.ph = {}
        for n in fdtlib.walk(self.root):
            v = n.prop('phandle')
            if v is not None: self.ph[struct.unpack('>I', v)[0]] = n.path()
        self.syms = {}
        sy = self.root.child('__symbols__')
        if sy:
            for k, v in sy.props:
                if k != 'name': self.syms[v.rstrip(b'\0').decode().split(':')[0]] = k
        # nodes that are the target of a local reference
        self.refd = set()
        for (p, pn, off) in self.loc:
            n = self.find(p)
            v = n.prop(pn) if n else None
            if v is not None and off + 4 <= len(v):
                h = struct.unpack('>I', v[off:off+4])[0]
                if h in self.ph: self.refd.add(self.ph[h])
        self.names = {}
        self.prefix = prefix
        for p in sorted(self.refd):
            self.names[p] = self.syms.get(p) or '%s%d' % (prefix, len(self.names))
        self._idx = {}
        for n in fdtlib.walk(self.root): self._idx[n.path()] = n

    def find(self, p):
        if not hasattr(self, '_idx') or not self._idx:
            self._idx = {n.path(): n for n in fdtlib.walk(self.root)}
        return self._idx.get(p)


def is_str(v):
    return bool(v) and v[-1] == 0 and b'\0\0' not in v and all(32 <= c < 127 or c == 0 for c in v)


def cells_text(c, path, name, v):
    toks = []
    for i in range(0, len(v), 4):
        k = (path, name, i)
        if k in c.ext: toks.append('&' + c.ext[k])
        elif k in c.loc:
            h = struct.unpack('>I', v[i:i+4])[0]
            toks.append('&' + c.names[c.ph[h]])
        else: toks.append('0x%x' % struct.unpack('>I', v[i:i+4])[0])
    return '<' + ' '.join(toks) + '>'


def prop_text(c, path, name, v):
    if len(v) == 0: return '%s;' % name
    has_fix = any(((path, name, i) in c.ext or (path, name, i) in c.loc) for i in range(0, len(v), 4))
    if not has_fix and is_str(v):
        return '%s = %s;' % (name, ', '.join('"%s"' % s.replace('\\', '\\\\').replace('"', '\\"') for s in v[:-1].decode().split('\0')))
    if len(v) % 4 == 0: return '%s = %s;' % (name, cells_text(c, path, name, v))
    return '%s = [%s];' % (name, ' '.join('%02x' % b for b in v))


def node_text(c, n, ind, top=False):
    pad = '\t' * ind
    out = []
    p = n.path()
    lab = c.names.get(p)
    head = ('%s: ' % lab if lab else '') + n.name
    out.append('%s%s {' % (pad, head))
    for k, v in n.props:
        if k in ('phandle', 'linux,phandle'): continue
        out.append('%s\t%s' % (pad, prop_text(c, p, k, v)))
    for ch in n.children:
        out.append('')
        out += node_text(c, ch, ind + 1)
    out.append('%s};' % pad)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dtbo'); ap.add_argument('--frags'); ap.add_argument('--root', action='store_true')
    ap.add_argument('--labels', default='lapis_l')
    o = ap.parse_args()
    c = Ctx(open(o.dtbo, 'rb').read(), o.labels)
    frags = [x for x in c.root.children if x.name.startswith('fragment')]
    lo, hi = 0, len(frags) - 1
    if o.frags:
        a, _, b = o.frags.partition('-'); lo = int(a); hi = int(b or a)
    out = []
    if o.root:
        out.append('/ {')
        for k, v in c.root.props:
            if k == 'name': continue
            out.append('\t' + prop_text(c, '/', k, v))
        out.append('};'); out.append('')
    for f in frags:
        idx = int(f.name.split('@')[1]) if f.name.split('@')[1].isdigit() else -1
        if o.frags and (idx < lo or idx > hi): continue
        fp = f.path()
        tp = f.prop('target-path')
        if tp is not None: tgt = '&{%s}' % tp.rstrip(b'\0').decode()
        else: tgt = '&' + c.ext[(fp, 'target', 0)]
        ov = f.child('__overlay__')
        out.append('%s {' % tgt)
        for k, v in ov.props:
            if k == 'name': continue
            out.append('\t' + prop_text(c, ov.path(), k, v))
        for ch in ov.children:
            out.append('')
            out += node_text(c, ch, 1)
        out.append('};'); out.append('')
    print('\n'.join(out))

if __name__ == '__main__':
    main()
