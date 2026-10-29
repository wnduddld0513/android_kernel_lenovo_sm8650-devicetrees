#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# (C) 2026 The LineageOS Project
"""Split a concatenated dtb (vendor_boot) and a dtbo.img into single blobs.

usage: split_stock.py DTB_CONCAT DTBO_IMG OUTDIR     ->  OUTDIR/dtb/NN.dtb, OUTDIR/dtbo/NN.dtbo
"""
import struct, sys, os

def split_dtb(data, out):
    os.makedirs(out, exist_ok=True)
    o = n = 0
    while o + 8 <= len(data):
        magic, size = struct.unpack('>II', data[o:o + 8])
        if magic != 0xd00dfeed: break
        open('%s/%02d.dtb' % (out, n), 'wb').write(data[o:o + size]); o += size; n += 1
    return n

def split_dtbo(data, out):
    os.makedirs(out, exist_ok=True)
    magic, total, hsize, esize, cnt, eoff, page, ver = struct.unpack('>8I', data[:32])
    assert magic == 0xd7b7ab1e
    for i in range(cnt):
        size, off = struct.unpack('>II', data[eoff + i * esize:eoff + i * esize + 8])
        open('%s/%02d.dtbo' % (out, i), 'wb').write(data[off:off + size])
    return cnt

if __name__ == '__main__':
    d, b, out = sys.argv[1:4]
    print('dtb  entries:', split_dtb(open(d, 'rb').read(), out + '/dtb'))
    print('dtbo entries:', split_dtbo(open(b, 'rb').read(), out + '/dtbo'))
