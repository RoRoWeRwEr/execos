#!/usr/bin/env python3
"""Generate PNG icons for ExecOS PWA using stdlib only (no Pillow)."""
import struct, zlib, math

def make_png(width, height, pixels):
    """pixels: list of (R,G,B,A) tuples, row-major."""
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter type None
        for x in range(width):
            r, g, b, a = pixels[y * width + x]
            raw += bytes([r, g, b, a])

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    # RGBA is color type 6
    ihdr = struct.pack('>II', width, height) + bytes([8, 6, 0, 0, 0])
    idat = zlib.compress(raw, 9)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', idat)
    png += chunk(b'IEND', b'')
    return png


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_icon(size):
    """Draw ExecOS icon: navy gradient bg + white lightning bolt."""
    pixels = []

    # Colors
    navy_top = (36, 81, 160)    # #2451A0
    navy_bot = (14, 35, 68)     # #0E2344
    bolt_color = (255, 255, 255)
    gold_accent = (255, 196, 57)  # #FFC439

    cx = size / 2
    cy = size / 2
    radius = size / 2

    # Lightning bolt path (normalized 0-1 coords, then scaled)
    # Classic lightning bolt: upper-right body + lower-left tail
    # Designed to fill ~55% of the icon height
    def bolt_poly(s):
        m = s * 0.55  # scale factor — bolt occupies 55% of icon
        ox = s * 0.5  # center x
        oy = s * 0.5  # center y
        # Points relative to center, scaled
        pts = [
            (0.08 * m, -0.5 * m),   # top-left
            (0.08 * m, 0.04 * m),   # mid-left upper
            (-0.28 * m, 0.04 * m),  # mid-left lower (hook left)
            (0.16 * m, 0.5 * m),    # bottom-right
            (0.16 * m, 0.06 * m),   # mid-right lower
            (0.52 * m, 0.06 * m),   # mid-right upper (hook right)
        ]
        return [(ox + p[0], oy + p[1]) for p in pts]

    def point_in_poly(px, py, poly):
        """Ray casting algorithm."""
        n = len(poly)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    bolt = bolt_poly(size)

    for y in range(size):
        for x in range(size):
            # Circular clip (squircle handled by iOS)
            dx = x - cx
            dy = y - cy
            if dx*dx + dy*dy > radius*radius:
                pixels.append((0, 0, 0, 0))
                continue

            # Gradient background
            t = y / (size - 1)
            bg = lerp_color(navy_top, navy_bot, t)

            # Check if in bolt
            in_bolt = point_in_poly(x + 0.5, y + 0.5, bolt)

            if in_bolt:
                # Slight drop shadow effect: if adjacent pixels outside bolt, shade
                pixels.append((*bolt_color, 255))
            else:
                pixels.append((*bg, 255))

    return pixels


for size in [180, 192, 512]:
    px = draw_icon(size)
    data = make_png(size, size, px)
    fname = f'/home/user/execos/icon-{size}.png'
    with open(fname, 'wb') as f:
        f.write(data)
    print(f'Written {fname} ({len(data)} bytes)')

print('Done.')
