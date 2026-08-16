#!/usr/bin/env python3
"""Скриншот экрана :0 через python3-xlib -> BMP (для проверки OSD)."""
import struct
import sys
from Xlib import display, X

d = display.Display(':0')
root = d.screen().root
geom = root.get_geometry()
w, h = geom.width, geom.height
img = root.get_image(0, 0, w, h, X.ZPixmap, 0xffffffff)
data = img.data
depth = geom.depth
bpp = 4 if depth > 24 else 3
row_size = (w * 3 + 3) & ~3
file_size = 54 + row_size * h

with open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/shot.bmp', 'wb') as f:
    f.write(b'BM')
    f.write(struct.pack('<IHHI', file_size, 0, 0, 54))
    f.write(struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0, row_size * h, 2835, 2835, 0, 0))
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            off = (y * w + x) * bpp
            b, g, r = data[off], data[off + 1], data[off + 2]
            row += bytes((b, g, r))
        row += b'\x00' * (row_size - w * 3)
        f.write(row)

print(f'OK {w}x{h} -> {sys.argv[1] if len(sys.argv) > 1 else "/tmp/shot.bmp"}')
