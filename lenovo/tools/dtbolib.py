# SPDX-License-Identifier: GPL-2.0
# (C) 2026 The LineageOS Project
"""Canonical, order independent form of a (merged) device tree overlay.

An overlay fragment is reduced to a target symbol plus a set of
"node|property=value" lines in which phandle cells are replaced by the label
they resolve to (__fixups__) or by the symbolic path of the overlay node they
point to (__local_fixups__).  Numeric phandles, fragment numbers and node
order therefore do not matter.
"""
import struct, hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fdtlib


def _fixups(root):
    ext = {}
    fx = root.child('__fixups__')
    if fx:
        for label, v in fx.props:
            if label == 'name': continue
            for ent in v.rstrip(b'\0').split(b'\0'):
                p, pn, off = ent.decode().rsplit(':', 2)
                ext[(p, pn, int(off))] = label
    loc = set()
    lf = root.child('__local_fixups__')
    if lf:
        def rec(n, path):
            for pn, v in n.props:
                if pn == 'name': continue
                for i in range(0, len(v), 4):
                    loc.add((path or '/', pn, struct.unpack('>I', v[i:i+4])[0]))
            for c in n.children:
                rec(c, (path if path != '/' else '') + '/' + c.name)
        rec(lf, '')
    return ext, loc


def normalize(blob):
    root = fdtlib.parse(blob)
    ext, loc = _fixups(root)
    nodes = {}
    ph = {}
    for n in fdtlib.walk(root):
        nodes[n.path()] = n
        v = n.prop('phandle')
        if v is not None: ph[struct.unpack('>I', v)[0]] = n.path()
    frags = [c for c in root.children if c.name.startswith('fragment') or c.name.startswith('__overlay__')]
    tsym = {}
    for f in frags:
        fp = f.path()
        t = f.prop('target-path')
        if t is not None: tsym[fp] = t.rstrip(b'\0').decode()
        else: tsym[fp] = '&' + ext.get((fp, 'target', 0), '?')
    def sym_of_path(p):
        for fp, s in tsym.items():
            pre = fp + '/__overlay__'
            if p == pre or p.startswith(pre + '/'):
                return s + p[len(pre):]
        return '?' + p
    own = {}
    sy = root.child('__symbols__')
    if sy:
        for k, v in sy.props:
            if k != 'name': own[k] = v.rstrip(b'\0').decode().split(':')[0]
    out = []
    for f in frags:
        fp = f.path(); ov = f.child('__overlay__')
        lines = []
        if ov is not None:
            for n in fdtlib.walk(ov):
                np_ = n.path(); rel = np_[len(fp) + len('/__overlay__'):] or '.'
                for pn, v in n.props:
                    if pn == 'phandle': continue
                    b = bytearray(v); toks = []
                    for off in range(0, len(v) - 3):
                        k = (np_, pn, off)
                        if k in ext:
                            lab = ext[k]
                            toks.append((off, '{@%s}' % sym_of_path(own[lab]) if lab in own else '{&%s}' % lab))
                        elif k in loc:
                            h = struct.unpack('>I', v[off:off+4])[0]
                            toks.append((off, '{@%s}' % sym_of_path(ph.get(h, '?%x' % h))))
                    s = ''; last = 0
                    for off, t in toks:
                        s += v[last:off].hex() + t; last = off + 4
                    s += v[last:].hex()
                    lines.append('%s|%s=%s' % (rel, pn, s))
        lines.sort()
        h = hashlib.sha1((tsym[fp] + '\n' + '\n'.join(lines)).encode()).hexdigest()[:12]
        out.append({'name': f.name, 'target': tsym[fp], 'lines': lines, 'hash': h})
    props = {k: v for k, v in root.props}
    return props, out


def describe(props):
    def s(k):
        v = props.get(k)
        return v.rstrip(b'\0').decode().replace('\0', ',') if v else ''
    def c(k):
        v = props.get(k)
        return ' '.join('%x' % x for x in struct.unpack('>%dI' % (len(v) // 4), v)) if v else ''
    return '%s | %s | msm-id %s | board-id %s' % (s('model'), s('compatible'), c('qcom,msm-id'), c('qcom,board-id'))
