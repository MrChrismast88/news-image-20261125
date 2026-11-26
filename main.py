#!/usr/bin/env python3
"""The World in One Day - a newspaper front page for 25 November 2026.

Draws a 1024x1024 front page summing up the day's world news and writes
it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Pure standard library only: a tiny bitmap canvas, a hand-made 5x7 pixel
font, and a hand-rolled PNG encoder. No network, no external files,
no randomness, no clock - every run writes byte-identical output.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- palette

PAPER = (247, 242, 231)      # newsprint off-white
INK = (20, 18, 16)           # near-black
RED = (163, 22, 33)          # accent red for kickers
BLUE = (29, 78, 137)         # chart bars
STEEL = (150, 150, 145)      # land masses on the map
WATER = (198, 220, 236)      # sea on the map
GREY = (107, 101, 92)        # secondary text
FLAME = (214, 90, 20)        # tanker fire

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 44

# ------------------------------------------------------------------- font
# A 5x7 pixel font, one tuple of seven 5-character rows per glyph.
# '#' is an inked pixel, '.' is blank.

FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    'g': (".....", ".....", ".####", "#...#", "#...#", ".####", ".###."),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    'j': ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", "#...#", ".####", ".###."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.#..", "#....", ".###."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
}

# Characters that never appear in the font get folded to a plain cousin.
NORMALISE = {
    "\u2014": "-", "\u2013": "-", "\u2019": "'", "\u2018": "'",
    "\u201c": '"', "\u201d": '"', "\u00b7": "-", "\u2022": "-",
}


def clean(text):
    """Fold fancy punctuation down to the glyphs the font can draw."""
    return "".join(NORMALISE.get(ch, ch) for ch in text)


def measure(text, scale):
    """Pixel width of text drawn at the given scale (6 units per glyph)."""
    text = clean(text)
    if not text:
        return 0
    return len(text) * 6 * scale - scale


# ------------------------------------------------------------------ canvas

class Canvas:
    """A plain RGB bitmap with a few drawing helpers."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(colour) * (width * height))

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.width + x0) * 3
            self.pixels[i:i + len(row)] = row

    def hline(self, x, y, length, colour):
        self.fill_rect(x, y, length, 1, colour)

    def vline(self, x, y, length, colour):
        self.fill_rect(x, y, 1, length, colour)

    def line(self, x0, y0, x1, y1, colour):
        """Bresenham line, one pixel thick."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, 1, 1, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def outline(self, x, y, w, h, colour, thick=1):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def triangle(self, cx, base_y, half_w, height, colour):
        """Small filled triangle pointing up, base at base_y."""
        for i in range(height):
            half = int(half_w * (height - i) / height)
            self.hline(cx - half, base_y - i, 2 * half + 1, colour)

    def disc(self, cx, cy, r, colour):
        """Filled circle by horizontal scanlines."""
        for dy in range(-r, r + 1):
            half = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - half, cy + dy, 2 * half + 1, colour)

    def draw_text(self, x, y, text, scale=1, colour=INK):
        """Draw text with the pixel font; returns the x just past the end."""
        cx = x
        for ch in clean(text):
            rows = FONT.get(ch)
            if rows is None:
                cx += 6 * scale
                continue
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == '#':
                        self.fill_rect(cx + rx * scale, y + ry * scale,
                                       scale, scale, colour)
            cx += 6 * scale
        return cx

    def centred(self, y, text, scale=1, colour=INK, x0=0, x1=None):
        """Draw text centred between x0 and x1 (defaults to the full page)."""
        if x1 is None:
            x1 = self.width
        w = measure(text, scale)
        self.draw_text(x0 + (x1 - x0 - w) // 2, y, text, scale, colour)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    current = ""
    for word in clean(text).split(" "):
        trial = word if not current else current + " " + word
        if measure(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# --------------------------------------------------------------------- png

def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def encode_png(canvas):
    """Encode the canvas as a PNG (truecolour, 8 bit, no filtering)."""
    header = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                         8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        raw += canvas.pixels[y * stride:(y + 1) * stride]
    body = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header) +
            _chunk(b"IDAT", body) + _chunk(b"IEND", b""))


# ------------------------------------------------------------------ layout

def story(cv, x, y, w, kicker, headline, body,
          head_scale=3, body_scale=2):
    """One news story: red kicker, wrapped headline, wrapped body text.

    Returns the y coordinate just below the story.
    """
    cv.draw_text(x, y, kicker, 1, RED)
    y += 16
    for line in wrap_text(headline, head_scale, w):
        cv.draw_text(x, y, line, head_scale, INK)
        y += head_scale * 7 + 8
    y += 2
    for line in wrap_text(body, body_scale, w):
        cv.draw_text(x, y, line, body_scale, INK)
        y += body_scale * 7 + 6
    return y


def tariff_chart(cv, x, y, w, h):
    """Bar chart of the proposed tariff rates, inside a ruled box."""
    cv.outline(x, y, w, h, INK)
    cv.centred(y + 8, "THE PROPOSED TARIFF WALL", 2, INK, x, x + w)
    cv.centred(y + 28, "DUTY PROPOSED, PER CENT", 1, GREY, x, x + w)
    values = [("CHINA", 20), ("EU", 20), ("INDIA", 18),
              ("JAPAN", 15), ("UK", 12), ("12 MORE", 10)]
    baseline = y + h - 24
    top = y + 48
    max_h = baseline - top
    slot = w // len(values)
    bar_w = 54
    for i, (name, val) in enumerate(values):
        bh = int(max_h * val / 20)
        bx = x + i * slot + (slot - bar_w) // 2
        cv.fill_rect(bx, baseline - bh, bar_w, bh, BLUE)
        label = str(val) + "%"
        cv.draw_text(bx + (bar_w - measure(label, 1)) // 2,
                     baseline - bh - 12, label, 1, INK)
        cv.draw_text(bx + (bar_w - measure(name, 1)) // 2,
                     baseline + 8, name, 1, INK)
    cv.hline(x + 8, baseline, w - 16, INK)


def strait_map(cv, x, y, w, h):
    """Schematic of the Strait of Hormuz: two land masses, a channel,
    and two tankers with flames. Deliberately diagrammatic, not a map."""
    cv.outline(x, y, w, h, INK)
    cv.centred(y + 8, "THE STRAIT AT A GLANCE", 1, INK, x, x + w)
    ix, iy = x + 8, y + 26
    iw, ih = w - 16, h - 34
    cv.fill_rect(ix, iy, iw, ih, WATER)
    # Iran, upper left; Oman, lower right. The water between is the strait.
    cv.fill_rect(ix, iy, 170, 38, STEEL)
    cv.fill_rect(ix + 116, iy + 54, iw - 116, ih - 54, STEEL)
    cv.draw_text(ix + 10, iy + 8, "IRAN", 1, INK)
    cv.draw_text(ix + iw - 34, iy + ih - 16, "OMAN", 1, INK)
    cv.draw_text(ix + 8, iy + ih - 16, "STRAIT OF HORMUZ", 1, INK)
    # Two tankers in the channel, each with a flame above its hull.
    for sx in (ix + 66, ix + 146):
        cv.fill_rect(sx, iy + 40, 26, 7, INK)
        cv.vline(sx + 12, iy + 32, 8, INK)
        cv.triangle(sx + 13, iy + 31, 7, 10, FLAME)
        cv.triangle(sx + 13, iy + 31, 4, 6, (255, 200, 60))


def brief_strip(cv, x, y, w):
    """'Also in brief' - eight one-liners in two columns."""
    cv.fill_rect(x, y, w, 2, INK)
    cv.draw_text(x, y + 10, "ALSO IN BRIEF", 2, RED)
    items = [
        "UKRAINE: war dead put at 490,334",
        "PACIFIC: Solomons bars foreign bases",
        "GAZA: Hamas colonel killed",
        "SUDAN: RSF strikes kill 19",
        "MARKETS: Wall Street slides",
        "COLOMBIA: bomb injures 23",
        "BANGLADESH: garment wage up 36%",
        "COP31: talks end without a deal",
    ]
    col_w = w // 2
    for i, item in enumerate(items):
        cx = x + (i % 2) * col_w
        cy = y + 34 + (i // 2) * 20
        cv.fill_rect(cx, cy + 3, 7, 7, RED)
        cv.draw_text(cx + 14, cy, item, 2, INK)
    return y + 34 + 4 * 20 + 8


def build_page():
    cv = Canvas(PAGE_W, PAGE_H, PAPER)
    right = PAGE_W - MARGIN
    content_w = right - MARGIN

    # ---- top furniture -------------------------------------------------
    cv.draw_text(MARGIN, 26, "VOL. I - NO. 329", 1, GREY)
    tail = "PRICE: ONE DAY OF HISTORY"
    cv.draw_text(right - measure(tail, 1), 26, tail, 1, GREY)
    cv.hline(MARGIN, 40, content_w, INK)

    # ---- masthead ------------------------------------------------------
    cv.centred(52, "THE WORLD IN ONE DAY", 7, INK)
    date = "WEDNESDAY 25 NOVEMBER 2026"
    cv.draw_text(MARGIN, 110, date, 2, INK)
    motto = "ONE DAY, THE WHOLE WORLD"
    cv.draw_text(right - measure(motto, 2), 110, motto, 2, INK)
    cv.fill_rect(MARGIN, 134, content_w, 3, INK)
    cv.hline(MARGIN, 140, content_w, INK)

    # ---- lead story ----------------------------------------------------
    cv.draw_text(MARGIN, 154, "LEAD - TRADE", 2, RED)
    y = 178
    for line in wrap_text(
            "US PROPOSES TARIFFS OF UP TO 20% ON CHINA, "
            "THE EU AND 12 MORE NATIONS", 4, content_w):
        cv.draw_text(MARGIN, y, line, 4, INK)
        y += 4 * 7 + 8
    y += 6
    for line in wrap_text(
            "After an eight-month probe, the White House unveiled a new "
            "tariff wall - the sharpest escalation of the trade war this "
            "year. Markets slid on the news.", 2, content_w):
        cv.draw_text(MARGIN, y, line, 2, INK)
        y += 2 * 7 + 6

    # ---- chart + map row ----------------------------------------------
    chart_x, chart_w = MARGIN, 556
    map_x, map_w = MARGIN + 572, 364
    tariff_chart(cv, chart_x, 292, chart_w, 136)
    strait_map(cv, map_x, 292, map_w, 136)

    # ---- two columns of stories ---------------------------------------
    col_w = 448
    left_x = MARGIN
    right_x = MARGIN + 488
    y = 444

    y = story(cv, left_x, y, col_w,
              "HORMUZ",
              "TWO TANKERS ABLAZE AFTER MINE STRIKES IN HORMUZ",
              "Two oil tankers were hit by naval mines and caught fire "
              "in the Strait of Hormuz, Iran said, as the US issued a "
              "fresh warning to shipping.")
    cv.hline(left_x, y + 8, col_w, INK)
    y = story(cv, left_x, y + 18, col_w,
              "YEMEN - SAUDI ARABIA",
              "HOUTHIS HIT SAUDI REFINERY AND RIYADH TOWER",
              "Missiles struck the Ras Tanura refinery and a Riyadh "
              "skyscraper, injuring 11 people, in the sharpest "
              "escalation in years.")

    y = 444
    y = story(cv, right_x, y, col_w,
              "TECH",
              "HUAWEI CONVICTED OF STEALING US TRADE SECRETS",
              "A US court found Huawei guilty of trade-secret theft "
              "and bank fraud. Beijing condemned the verdict.")
    cv.hline(right_x, y + 8, col_w, INK)
    y = story(cv, right_x, y + 18, col_w,
              "SPACE",
              "FIRST FOREIGN ASTRONAUT BOARDS TIANGONG",
              "Shenzhou-24 carried Pakistan's Zeeshan Ali to "
              "Tiangong, the first foreign astronaut aboard the "
              "station.")
    cv.hline(right_x, y + 8, col_w, INK)
    y += 12
    cv.draw_text(right_x, y, "BY THE NUMBERS", 1, RED)
    y += 12
    for line in wrap_text(
            "20% top tariff rate proposed. 490,334 Russian war dead. "
            "11 hurt in Riyadh.", 2, col_w):
        cv.draw_text(right_x, y, line, 2, INK)
        y += 2 * 7 + 6

    # ---- also in brief --------------------------------------------------
    brief_strip(cv, MARGIN, 806, content_w)

    # ---- footer ---------------------------------------------------------
    cv.hline(MARGIN, 946, content_w, INK)
    cv.centred(958, "Sources: Reuters, AP, AFP, Just Security. "
                    "All events from Wednesday 25 November 2026.", 1, GREY)
    cv.centred(974, "THE WORLD IN ONE DAY - drawn entirely in code, "
                    "no photographs.", 1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(build_page())
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
