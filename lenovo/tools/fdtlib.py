# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
"""Minimal flattened device tree reader shared by the lenovo/tools scripts."""
import struct

class Node:
    __slots__ = ('name', 'props', 'children', 'parent')
    def __init__(self, name, parent=None):
        self.name = name; self.props = []; self.children = []; self.parent = parent
    def prop(self, n):
        for k, v in self.props:
            if k == n: return v
        return None
    def child(self, n):
        for c in self.children:
            if c.name == n: return c
        return None
    def path(self):
        if self.parent is None: return '/'
        p = self.parent.path()
        return (p if p != '/' else '') + '/' + self.name

def parse(b):
    magic, total, off_struct, off_str, off_rsv, ver, lcv, bootcpu, size_str, size_struct = struct.unpack('>10I', b[:40])
    assert magic == 0xd00dfeed
    st = b[off_struct:off_struct + size_struct]
    strs = b[off_str:off_str + size_str]
    i = 0; root = None; cur = None
    while True:
        t = struct.unpack('>I', st[i:i+4])[0]; i += 4
        if t == 1:
            e = st.index(b'\0', i); name = st[i:e].decode(); i = (e + 4) & ~3
            n = Node(name, cur)
            if cur is None: root = n
            else: cur.children.append(n)
            cur = n
        elif t == 2:
            cur = cur.parent
        elif t == 3:
            ln, no = struct.unpack('>II', st[i:i+8]); i += 8
            e = strs.index(b'\0', no); pn = strs[no:e].decode()
            cur.props.append((pn, bytes(st[i:i+ln]))); i += (ln + 3) & ~3
        elif t == 4: pass
        elif t == 9: break
        else: raise Exception('bad tag %d' % t)
    return root

def walk(n):
    yield n
    for c in n.children:
        yield from walk(c)
