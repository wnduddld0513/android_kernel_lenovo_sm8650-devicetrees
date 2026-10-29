#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
# (C) 2026 The LineageOS Project
"""Render nodes of a flattened base dtb as device tree source.

usage: dtb2dts.py FILE.dtb PATH [PATH...]
Phandle cells of well known properties (supplies, clocks, gpios, pinctrl-N,
interconnects, ...) are written as &label (from __symbols__) or &{/path}.
"""
import sys, os, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fdtlib

STRIDE = {  # property -> (cells property on the target)
    'clocks': '#clock-cells', 'assigned-clocks': '#clock-cells', 'assigned-clock-parents': '#clock-cells',
    'gpios': '#gpio-cells', 'resets': '#reset-cells', 'iommus': '#iommu-cells',
    'interconnects': '#interconnect-cells', 'power-domains': '#power-domain-cells',
    'thermal-sensors': '#thermal-sensor-cells', 'phys': '#phy-cells', 'mboxes': '#mbox-cells',
    'dmas': '#dma-cells', 'pwms': '#pwm-cells', 'io-channels': '#io-channel-cells',
    'nvmem-cells': None, 'memory-region': None, 'interrupt-parent': None,
    'pinctrl-0': None, 'pinctrl-1': None, 'pinctrl-2': None, 'pinctrl-3': None, 'pinctrl-4': None,
    'qcom,smmu-pagetable-reserved': None,
}

class Tree:
    def __init__(self, path):
        self.root = fdtlib.parse(open(path, 'rb').read())
        self.nodes = {}; self.ph = {}
        for n in fdtlib.walk(self.root):
            self.nodes[n.path()] = n
            v = n.prop('phandle')
            if v is not None: self.ph[struct.unpack('>I', v)[0]] = n.path()
        self.label = {}
        sy = self.root.child('__symbols__')
        if sy:
            for k, v in sy.props:
                if k != 'name': self.label.setdefault(v.rstrip(b'\0').decode(), k)

    def ref(self, h):
        p = self.ph.get(h)
        if p is None: return None
        return '&' + self.label[p] if p in self.label else '&{%s}' % p

    def cellsof(self, h, prop):
        p = self.ph.get(h)
        if p is None: return None
        v = self.nodes[p].prop(prop)
        return struct.unpack('>I', v)[0] if v and len(v) == 4 else None

def is_str(v):
    if not v or v[-1] != 0: return False
    return all(32 <= c < 127 or c == 0 for c in v) and b'\0\0' not in v

def render_cells(t, name, v):
    cs = list(struct.unpack('>%dI' % (len(v) // 4), v))
    out = []
    key = name if name in STRIDE else ('pinctrl-0' if re.match(r'pinctrl-\d+$', name) else None)
    if name.endswith('-supply') or name in ('interrupt-parent', 'memory-region') or key == 'pinctrl-0' or name.endswith('-gpios') or name.endswith('-gpio'):
        pass
    if name.endswith('-supply') or name in ('interrupt-parent', 'memory-region') or (key and STRIDE.get(key, 1) is None):
        for c in cs: out.append(t.ref(c) or '0x%x' % c)
        return '<' + ' '.join(out) + '>'
    cellprop = STRIDE.get(name) if name in STRIDE else ('#gpio-cells' if ('gpio' in name and 'pinctrl' not in name and 'reserved' not in name) else None)
    if cellprop:
        i = 0; ok = True; res = []
        while i < len(cs):
            n = t.cellsof(cs[i], cellprop)
            if n is None or i + 1 + n > len(cs): ok = False; break
            res.append(t.ref(cs[i]) + ' ' + ' '.join('0x%x' % c for c in cs[i+1:i+1+n]) if n else t.ref(cs[i]))
            i += 1 + n
        if ok: return '<' + '>, <'.join(res) + '>'
    return '<' + ' '.join('0x%x' % c for c in cs) + '>'

def render_prop(t, name, v):
    if len(v) == 0: return '%s;' % name
    if is_str(v):
        return '%s = %s;' % (name, ', '.join('"%s"' % s.replace('\\', '\\\\').replace('"', '\\"') for s in v[:-1].decode().split('\0')))
    if len(v) % 4 == 0: return '%s = %s;' % (name, render_cells(t, name, v))
    return '%s = [%s];' % (name, ' '.join('%02x' % b for b in v))

def render_node(t, n, ind, skip=('phandle', 'linux,phandle')):
    out = []
    pad = '\t' * ind
    lab = t.label.get(n.path())
    out.append('%s%s%s {' % (pad, lab + ': ' if lab else '', n.name))
    for k, v in n.props:
        if k in skip: continue
        out.append('%s\t%s' % (pad, render_prop(t, k, v)))
    for c in n.children:
        out.append('')
        out += render_node(t, c, ind + 1)
    out.append('%s};' % pad)
    return out

if __name__ == '__main__':
    t = Tree(sys.argv[1])
    for p in sys.argv[2:]:
        print('\n'.join(render_node(t, t.nodes[p], 0))); print()
