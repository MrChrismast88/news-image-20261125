#!/usr/bin/env python3
"""News in one image: Wednesday 25 November 2026.

A pure-stdlib (Python 3.13) renderer. It draws a newspaper front page that
sums up the world's news of 25 November 2026 and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Everything is drawn procedurally: no image files, no fonts on disk, no
network, no randomness, no clock. Two runs produce byte-identical output.

Stories (all reported on 25 November 2026, sources: Reuters, AP, AFP,
Just Security, Korea Herald, Daily Mirror):
  1. The Trump administration proposes new tariffs of up to 20% on
     China, the EU and 12 more nations, after an eight-month probe
     into excess factory capacity; a hearing is set for 25 January.
  2. Two oil tankers hit naval mines and caught fire in the Strait of
     Hormuz, Iran's IRGC said; the US issued a fresh alert for
     Americans across the Middle East.
  3. Yemen's Houthis attacked Saudi Arabia's Ras Tanura refinery and
     struck a Riyadh skyscraper, injuring 11 people.
  4. A US federal court convicted Huawei of conspiracy to steal trade
     secrets and bank fraud (not racketeering); China condemned it.
  5. China's Shenzhou-24 launched with Pakistan's Muhammad Zeeshan Ali,
     the first foreign astronaut to board the Tiangong space station.
  6. Australia and the Solomon Islands signed a treaty barring any
     foreign military base in the Solomons.
  7. Leaked Russian statistics put Russian soldiers dead in Ukraine at
     490,334; Russian strikes hit Odesa and Kyiv.
  8. Also: Israel killed Hamas colonel Mohammad Abuelouf in Gaza; RSF
     drone strikes killed 19 civilians in Sudan; Wall Street slid
     (S&P -2.2%, Nasdaq -3.2%); a bomb in Villavicencio, Colombia,
     injured 23; Bangladesh raised the garment minimum wage 36%;
     Pope Leo XIV lamented the COP31 talks' failure.
"""

import binascii
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# --- palette: newsprint -------------------------------------------------
PAPER = (247, 243, 234)
INK = (16, 35, 63)        # deep navy, masthead + headlines
RED = (178, 34, 34)       # lead / urgency
GOLD = (214, 158, 46)     # date line
WHITE = (255, 255, 255)
GREY = (90, 96, 104)
LIGHT = (232, 226, 214)   # card background
TEAL = (18, 110, 105)
STEEL = (70, 110, 150)
AMBER = (176, 106, 20)

# --- 5x7 bitmap font (rows top to bottom, bit 4 = leftmost pixel) -------
# Classic public-domain 5x7 face, typed in by hand for this entry.
FONT = {
    ' ': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '%': (0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x18),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    '+': (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    '-': (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    '/': (0x01, 0x02, 0x02, 0x04, 0x08, 0x10, 0x10),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ';': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    '<': (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '>': (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    '|': (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    '@': (0x0E, 0x11, 0x01, 0x0D, 0x15, 0x15, 0x0E),
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x01, 0x01, 0x01, 0x01, 0x11, 0x11, 0x0E),
    'K': (0x11, 0x12, 0x14, 0x1C, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
}


class Canvas:
    """An RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            n = min(self.w, x + w) - max(0, x)
            if n > 0:
                self.px[base:base + n * 3] = bytes(color) * n

    def hline(self, x0, x1, y, color, thick=1):
        for t in range(thick):
            self.rect(x0, y + t, x1 - x0, 1, color)

    def vline(self, x, y0, y1, color, thick=1):
        for t in range(thick):
            self.rect(x + t, y0, 1, y1 - y0, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                elif (r - 1) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        # outline only, parametric
        for deg in range(0, 360):
            a = math.radians(deg)
            self.set(round(cx + rx * math.cos(a)),
                     round(cy + ry * math.sin(a)), color)

    def text(self, x, y, s, scale, color):
        """Draw upper-case text; unknown chars become '?'."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT['?'])
            for row, bits in enumerate(glyph):
                for col in range(5):
                    if bits & (0x10 >> col):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def center(self, y, s, scale, color, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        x = x0 + (x1 - x0 - self.text_w(s, scale)) // 2
        self.text(x, y, s, scale, color)


def wrap(text, max_chars):
    """Greedy word wrap; returns a list of lines."""
    lines, cur = [], ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    return lines


def png_bytes(cv):
    """Encode the canvas as a deterministic PNG (filter 0, zlib level 9)."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    return data


# --- layout -----------------------------------------------------------------

LEAD_HEAD = ["US PROPOSES TARIFFS",
             "OF UP TO 20% ON CHINA,",
             "THE EU AND 12 NATIONS"]
LEAD_BODY = ("The Trump administration proposed tariffs of up to 20% on "
             "China, the EU and 12 more nations after an eight-month "
             "probe into excess factory capacity. A hearing is set for "
             "25 January.")

# (tag, tag colour, headline lines, body)
STORIES = [
    ("HORMUZ", RED,
     ["TANKERS HIT BY MINES",
      "IN STRAIT OF HORMUZ"],
     "Two tankers hit mines and caught fire in the strait, Tehran said."),
    ("YEMEN - SAUDI ARABIA", RED,
     ["HOUTHIS HIT SAUDI",
      "REFINERY, RIYADH TOWER"],
     "Ras Tanura refinery hit; a Riyadh tower strike injured 11."),
    ("TECH - US COURT", AMBER,
     ["US COURT CONVICTS",
      "HUAWEI OF TRADE THEFT"],
     "Huawei convicted of trade-secret theft and bank fraud."),
    ("SPACE", TEAL,
     ["PAKISTAN'S FIRST",
      "ASTRONAUT REACHES ORBIT"],
     "Shenzhou-24 carried Muhammad Zeeshan Ali to Tiangong, "
     "a first for Pakistan."),
    ("PACIFIC", STEEL,
     ["AUSTRALIA, SOLOMONS",
      "SIGN SECURITY TREATY"],
     "The treaty bars foreign military bases in the "
     "Solomons. China is shut out."),
    ("UKRAINE", STEEL,
     ["RUSSIA'S WAR DEAD",
      "NEAR 500,000, LEAK SHOWS"],
     "Leaked figures put Russian dead at 490,334; strikes "
     "hit Odesa and Kyiv."),
]

ALSO_1 = "ALSO: HAMAS COLONEL KILLED IN GAZA - RSF STRIKES KILL 19 IN SUDAN - S&P -2.2%"
ALSO_2 = "BOMB IN COLOMBIA INJURES 23 - BANGLADESH WAGE UP 36% - COP31 TALKS FAIL"


def draw_globe(cv, cx, cy, r):
    """A simple wireframe globe with three flashpoint dots."""
    cv.circle(cx, cy, r, INK)
    cv.ellipse(cx, cy, r, r // 2, INK)
    cv.ellipse(cx, cy, r // 2, r, INK)
    cv.hline(cx - r, cx + r, cy, INK)
    cv.vline(cx, cy - r, cy + r, INK)
    for dx, dy in ((-38, -30), (30, -42), (-52, 28)):
        cv.circle(cx + dx, cy + dy, 7, RED, fill=True)
        cv.circle(cx + dx, cy + dy, 7, WHITE)
        cv.circle(cx + dx, cy + dy, 4, RED, fill=True)
    cv.text(cx - r - 6, cy + r + 10, "HORMUZ - RIYADH - BEIJING", 1, GREY)


def draw(cv):
    cv.rect(0, 0, W, H, PAPER)

    # --- masthead -------------------------------------------------------
    cv.rect(0, 0, W, 128, INK)
    cv.text(24, 18, "THE WORLD IN ONE DAY", 5, WHITE)
    cv.text(24, 72, "WEDNESDAY, 25 NOVEMBER 2026", 3, GOLD)
    cv.text(24, 104, "THE DAY'S BIGGEST STORIES - IN ONE PICTURE", 2, (200, 208, 220))
    cv.rect(0, 128, W, 6, RED)

    # --- lead story -----------------------------------------------------
    lx, ly, lw, lh = 24, 146, 976, 252
    cv.rect(lx, ly, lw, lh, WHITE)
    cv.rect(lx, ly, 10, lh, RED)
    cv.text(lx + 26, ly + 14, "LEAD  -  WASHINGTON  -  TRADE", 2, RED)
    y = ly + 44
    for line in LEAD_HEAD:
        cv.text(lx + 26, y, line, 4, INK)
        y += 36
    y += 6
    for line in wrap(LEAD_BODY, 52):
        cv.text(lx + 26, y, line, 2, (40, 44, 52))
        y += 20
    draw_globe(cv, 884, 262, 74)

    # --- story grid: 2 columns x 3 rows ---------------------------------
    gx, gy = 24, 414
    cw, chh, gap = 480, 152, 16
    for i, (tag, tcol, head, body) in enumerate(STORIES):
        x = gx + (i % 2) * (cw + gap)
        y0 = gy + (i // 2) * (chh + gap)
        cv.rect(x, y0, cw, chh, WHITE)
        cv.rect(x, y0, cw, 30, tcol)
        cv.text(x + 12, y0 + 8, tag, 2, WHITE)
        cv.text(x + cw - 12 - cv.text_w("25 NOV", 2), y0 + 8, "25 NOV", 2,
                (235, 235, 235))
        yy = y0 + 42
        for line in head:
            cv.text(x + 12, yy, line, 3, INK)
            yy += 28
        for line in wrap(body, 38):
            cv.text(x + 12, yy, line, 2, (40, 44, 52))
            yy += 19

    # --- also strip ------------------------------------------------------
    ay = 902
    cv.rect(24, ay, 976, 62, INK)
    cv.center(ay + 8, ALSO_1, 2, WHITE)
    cv.center(ay + 34, ALSO_2, 2, GOLD)

    # --- footer ----------------------------------------------------------
    cv.center(978, "SOURCES: REUTERS - AP - AFP - JUST SECURITY  |  ALL EVENTS FROM 25 NOVEMBER 2026",
              2, GREY)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw(cv)
    data = png_bytes(cv)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes, {W}x{H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
