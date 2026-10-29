#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
"""Work out which Qualcomm overlay sources make up every merged stock dtbo entry.

usage: infer_entries.py POOL_DIR STOCK_DBTO_DIR OUT_DIR [IDX...]
POOL_DIR has every overlay source of the tree compiled on its own
(<dir>__<name>.dtbo).  For each stock entry the overlay sources are picked
greedily by how many of the entry's (target, node, property) values they
reproduce; OUT_DIR/dtbo.list and OUT_DIR/ids/NN.dts (root properties) are
written.  Entries that no source combination explains are reported.
"""
import sys, os, glob, re, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dtbolib

def flat(path):
    props, fr = dtbolib.normalize(open(path, 'rb').read())
    d = {}; pos = {}
    for i, x in enumerate(fr):
        for l in x['lines']:
            k, _, v = l.partition('=')
            d[(x['target'], k)] = v; pos.setdefault((x['target'], k), i)
    return props, d, pos

BOARDS = ['atp', 'cdp', 'mtp', 'qrd', 'rcm', 'rumi', 'hdk', 'aim500', 'idp', 'dpm']

def main():
    pool_dir, stock_dir, out = sys.argv[1:4]
    only = set(int(x) for x in sys.argv[4:])
    pool = {}
    for f in sorted(glob.glob(pool_dir + '/*.dtbo')):
        _, d, _ = flat(f); pool[os.path.basename(f)[:-5]] = d
    os.makedirs(out + '/ids', exist_ok=True)
    lines = []
    for f in sorted(glob.glob(stock_dir + '/*.dtbo')):
        idx = int(os.path.basename(f)[:-5])
        if only and idx not in only: continue
        props, st, pos = flat(f)
        model = props.get('model', b'').rstrip(b'\0').decode().lower()
        fam = next((x for x in ('pineapple', 'cliffs', 'volcano') if x in model), None)
        board = next((b for b in BOARDS if re.search(r'\b%s\b' % b, model)), None)
        if not fam or not props: continue
        remaining = dict(st)
        sel = []
        while True:
            best = None
            for n, d in pool.items():
                if fam not in n and not (fam == 'pineapple' and 'pineapple' in n): continue
                nb = [b for b in BOARDS if re.search(r'(^|[-_])%s([-_.]|$)' % b, n)]
                if nb and board not in nb: continue
                new = sum(1 for k in d if k in remaining and remaining[k] == d[k])
                if new < 4: continue
                bad = sum(1 for k in d if k not in st) + sum(1 for k in d if k in st and st[k] != d[k])
                sc = new - 2 * bad
                if best is None or (sc, new) > best[0]: best = ((sc, new), n)
            if best is None or best[0][0] <= 0: break
            n = best[1]; sel.append(n)
            for k in pool[n]:
                if k in remaining and remaining[k] == pool[n][k]: del remaining[k]
        # a source that adds nothing to its predecessors was picked for a different reason; keep order by first position
        def first(n):
            return min([pos[k] for k in pool[n] if k in pos] or [10**6])
        sel.sort(key=first)
        srcs = [n.replace('__', '/') + '.dts' for n in sel]
        unexplained = len(remaining)
        print('%2d %-44s explained %5d/%5d  %s' % (idx, model[:44], len(st) - unexplained, len(st), ' '.join(s.split('/')[-1][:-4] for s in srcs)))
        if not srcs: continue
        # root properties
        def cells(k):
            v = props.get(k)
            return ' '.join('0x%x' % c for c in struct.unpack('>%dI' % (len(v) // 4), v))
        def strs(k):
            return ', '.join('"%s"' % s for s in props[k].rstrip(b'\0').decode().split('\0'))
        open('%s/ids/%02d.dts' % (out, idx), 'w').write(
            '// SPDX-License-Identifier: GPL-2.0-only\n/*\n * (C) 2026 The LineageOS Project\n *\n * Board identification of stock dtbo entry %d.\n */\n\n/dts-v1/;\n/plugin/;\n\n/ {\n\tmodel = %s;\n\tcompatible = %s;\n\tqcom,msm-id = <%s>;\n\tqcom,board-id = <%s>;\n};\n'
            % (idx, strs('model'), strs('compatible'), cells('qcom,msm-id'), cells('qcom,board-id')))
        lines.append('%d %s ../lenovo/dtbo-ids/%02d.dts' % (idx, ' '.join(srcs), idx))
    open(out + '/dtbo.list.gen', 'w').write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
