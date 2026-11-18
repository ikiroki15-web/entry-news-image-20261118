#!/usr/bin/env python3
"""World News, Wednesday 18 November 2026 -- one-page newspaper front.

Draws a 1024x1024 newspaper front page entirely at runtime with the
standard library only (zlib + struct for the PNG encoder, no network,
no clock, no randomness), so two runs write byte-identical files.

Stories (all reported on 18 Nov 2026, verified against Reuters/AP/AFP
wire copy the same day):
  1. Gulf: US jets hit an IRGC missile site on Qeshm Island; Iran
     drones target US bases in Bahrain and Kuwait; attacks intercepted.
  2. Kerch Bridge: Ukraine hits it a second day; road arch collapses
     into the sea; 2 killed; traffic halted.
  3. Alaska: Mary Peltola wins the Senate seat; Democrats 56-44;
     first Alaska Native in the US Senate.
  4. Nvidia: record $115.8bn quarterly revenue, up 103%; $130bn guide.
  5. Ebola: DR Congo toll passes 11,500 cases and 5,600 deaths.
  6. Cyclone Xavier: Category 5, gusts 315 km/h, Northern Cook Islands.
  7. Russian An-12 military plane crashes in Siberia; all 19 aboard dead.
  8. Also: magnitude 6.0 quake in Papua New Guinea, 5.3 in Romania.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 229)
INK = (20, 20, 20)
WHITE = (253, 252, 246)
RED = (176, 30, 36)
NAVY = (29, 53, 87)
TEAL = (14, 107, 107)
GOLD = (214, 158, 32)
ORANGE = (224, 110, 30)
SKY = (120, 170, 205)
GREY = (110, 104, 92)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, "#" = on. Hand-drawn for this entry.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    # bullet: small centred square
    "\u2022": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
    # em dash: full-width bar
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    lines = []
    for raw in text.split("\n"):
        line = ""
        for word in raw.split(" "):
            trial = word if not line else line + " " + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(thick):
                for b in range(thick):
                    self.set(x0 + a, y0 + b, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, thick=2, filled=False):
        # Mid-point circle; filled variant paints scanlines.
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            if filled:
                for xx in range(cx - x, cx + x + 1):
                    self.set(xx, cy + y, color)
                    self.set(xx, cy - y, color)
                for xx in range(cx - y, cx + y + 1):
                    self.set(xx, cy + x, color)
                    self.set(xx, cy - x, color)
            else:
                for _ in range(thick):
                    pass
                for px, py in (
                    (cx + x, cy + y), (cx - x, cy + y),
                    (cx + x, cy - y), (cx - x, cy - y),
                    (cx + y, cy + x), (cx - y, cy + x),
                    (cx + y, cy - x), (cx - y, cy - x),
                ):
                    for a in range(thick):
                        self.set(px + a, py, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def poly(self, points, color, filled=True):
        if not filled:
            for i in range(len(points)):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % len(points)]
                self.line(x0, y0, x1, y1, color, 2)
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(points)):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % len(points)]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(xx, y, color)

    def star(self, cx, cy, r_out, r_in, points, color):
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / points - math.pi / 2
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.poly(pts, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_centred(self, y, s, scale, color, cx_mid=512):
        self.text(cx_mid - text_width(s, scale) // 2, y, s, scale, color)


# -------------------------------------------------------------- pictograms
def pic_gulf(cv, x, y, s):
    # Sea, island, explosion burst, jet overhead.
    cv.rect(x, y + int(0.72 * s), s, int(0.28 * s), SKY)
    for k in range(3):
        yy = y + int(0.78 * s) + k * int(0.07 * s)
        for xx in range(x, x + s, 14):
            cv.line(xx, yy, xx + 7, yy - 4, WHITE, 2)
    cv.poly([(x + int(0.30 * s), y + int(0.72 * s)),
             (x + int(0.55 * s), y + int(0.55 * s)),
             (x + int(0.72 * s), y + int(0.72 * s))], (96, 140, 90))
    cv.star(x + int(0.42 * s), y + int(0.38 * s), int(0.34 * s),
            int(0.16 * s), 8, GOLD)
    cv.star(x + int(0.42 * s), y + int(0.38 * s), int(0.20 * s),
            int(0.09 * s), 8, ORANGE)
    # jet: small delta jet flying right, clear of the blast
    jx, jy = x + int(0.02 * s), y + int(0.06 * s)
    cv.poly([(jx, jy + 8), (jx + 46, jy), (jx + 54, jy + 3),
             (jx + 30, jy + 9)], INK)
    cv.poly([(jx + 24, jy + 9), (jx + 40, jy + 22),
             (jx + 32, jy + 22), (jx + 18, jy + 11)], INK)
    cv.poly([(jx + 6, jy + 8), (jx - 2, jy - 4),
             (jx + 4, jy - 4), (jx + 12, jy + 6)], INK)


def pic_bridge(cv, x, y, s):
    # Bridge deck with the middle span dropped into the water.
    cv.rect(x, y + int(0.78 * s), s, int(0.22 * s), SKY)
    for k in range(2):
        yy = y + int(0.84 * s) + k * int(0.07 * s)
        for xx in range(x, x + s, 14):
            cv.line(xx, yy, xx + 7, yy - 4, WHITE, 2)
    cv.rect(x + int(0.10 * s), y + int(0.42 * s), 8, int(0.38 * s), INK)
    cv.rect(x + int(0.80 * s), y + int(0.42 * s), 8, int(0.38 * s), INK)
    # left deck + arch
    cv.rect(x + int(0.05 * s), y + int(0.40 * s), int(0.32 * s), 8, INK)
    cv.line(x + int(0.10 * s), y + int(0.40 * s),
            x + int(0.21 * s), y + int(0.28 * s), INK, 4)
    cv.line(x + int(0.21 * s), y + int(0.28 * s),
            x + int(0.32 * s), y + int(0.40 * s), INK, 4)
    # right deck
    cv.rect(x + int(0.63 * s), y + int(0.40 * s), int(0.32 * s), 8, INK)
    cv.line(x + int(0.68 * s), y + int(0.40 * s),
            x + int(0.79 * s), y + int(0.28 * s), INK, 4)
    cv.line(x + int(0.79 * s), y + int(0.28 * s),
            x + int(0.90 * s), y + int(0.40 * s), INK, 4)
    # fallen span, tilted into the strait
    cv.line(x + int(0.37 * s), y + int(0.44 * s),
            x + int(0.52 * s), y + int(0.74 * s), RED, 7)
    cv.line(x + int(0.52 * s), y + int(0.74 * s),
            x + int(0.60 * s), y + int(0.48 * s), RED, 7)
    cv.star(x + int(0.48 * s), y + int(0.16 * s), 16, 7, 8, GOLD)


def pic_ballot(cv, x, y, s):
    # Capitol dome + ballot box with a tick.
    cv.poly([(x + int(0.50 * s), y + int(0.06 * s)),
             (x + int(0.66 * s), y + int(0.22 * s)),
             (x + int(0.34 * s), y + int(0.22 * s))], NAVY)
    cv.rect(x + int(0.34 * s), y + int(0.22 * s), int(0.32 * s), 8, NAVY)
    for k in range(4):
        xx = x + int(0.36 * s) + k * int(0.08 * s)
        cv.rect(xx, y + int(0.26 * s), 5, int(0.16 * s), NAVY)
    cv.rect(x + int(0.30 * s), y + int(0.42 * s), int(0.40 * s), 8, NAVY)
    # ballot box
    bx, by = x + int(0.18 * s), y + int(0.58 * s)
    cv.rect(bx, by, int(0.64 * s), int(0.34 * s), WHITE)
    cv.rect(bx, by, int(0.64 * s), int(0.34 * s), INK)  # placeholder fix below
    cv.rect(bx + 4, by + 4, int(0.64 * s) - 8, int(0.34 * s) - 8, (210, 220, 235))
    cv.rect(bx + int(0.22 * s), by - 6, int(0.20 * s), 8, INK)
    cv.line(bx + int(0.22 * s), by + int(0.20 * s),
            bx + int(0.34 * s), by + int(0.28 * s), RED, 5)
    cv.line(bx + int(0.34 * s), by + int(0.28 * s),
            bx + int(0.52 * s), by + int(0.06 * s), RED, 5)


def pic_chip(cv, x, y, s):
    # AI chip + rising arrow.
    cx, cy = x + int(0.42 * s), y + int(0.48 * s)
    side = int(0.52 * s)
    cv.rect(cx - side // 2, cy - side // 2, side, side, NAVY)
    cv.rect(cx - side // 2 + 10, cy - side // 2 + 10, side - 20, side - 20,
            (60, 110, 170))
    cv.rect(cx - 12, cy - 12, 24, 24, GOLD)
    for k in range(5):
        off = -side // 2 + 8 + k * (side - 16) // 4
        cv.rect(cx + off - 2, cy - side // 2 - 12, 4, 12, INK)
        cv.rect(cx + off - 2, cy + side // 2, 4, 12, INK)
        cv.rect(cx - side // 2 - 12, cy + off - 2, 12, 4, INK)
        cv.rect(cx + side // 2, cy + off - 2, 12, 4, INK)
    # rising arrow
    ax = x + int(0.06 * s)
    ay = y + int(0.86 * s)
    cv.line(ax, ay, ax + int(0.20 * s), ay - int(0.22 * s), RED, 5)
    cv.line(ax + int(0.20 * s), ay - int(0.22 * s),
            ax + int(0.38 * s), ay - int(0.44 * s), RED, 5)
    cv.poly([(ax + int(0.38 * s), ay - int(0.44 * s)),
             (ax + int(0.30 * s), ay - int(0.44 * s)),
             (ax + int(0.38 * s), ay - int(0.34 * s))], RED)


def pic_virus(cv, x, y, s):
    # Spiky virus ball + medical cross.
    cx, cy = x + s // 2, y + int(0.46 * s)
    r = int(0.26 * s)
    for k in range(10):
        a = 2 * math.pi * k / 10
        x1 = int(cx + r * math.cos(a))
        y1 = int(cy + r * math.sin(a))
        x2 = int(cx + (r + 14) * math.cos(a))
        y2 = int(cy + (r + 14) * math.sin(a))
        cv.line(x1, y1, x2, y2, RED, 4)
        cv.circle(x2, y2, 4, RED, filled=True)
    cv.circle(cx, cy, r, RED, filled=True)
    cv.circle(cx, cy, r - 8, (200, 60, 60), filled=True)
    # cross badge bottom-right
    bx, by = x + int(0.62 * s), y + int(0.66 * s)
    cv.rect(bx, by, 34, 34, WHITE)
    cv.rect(bx + 13, by + 4, 8, 26, TEAL)
    cv.rect(bx + 4, by + 13, 26, 8, TEAL)


def pic_cyclone(cv, x, y, s):
    # Spiral storm + wind streaks.
    cx, cy = x + s // 2, y + int(0.44 * s)
    for k, r in enumerate((14, 24, 34, 44)):
        cv.circle(cx, cy, r, NAVY, thick=5)
        # erase a wedge so the rings read as a spiral
        a0 = -0.4 + k * 0.9
        for t in range(40):
            a = a0 + t * 0.05
            xx = int(cx + r * math.cos(a))
            yy = int(cy + r * math.sin(a))
            cv.rect(xx - 3, yy - 3, 7, 7, PAPER)
    cv.circle(cx, cy, 8, GOLD, filled=True)
    for k in range(3):
        yy = y + int(0.80 * s) + k * int(0.06 * s)
        cv.line(x + int(0.10 * s) + k * 12, yy,
                x + int(0.90 * s) - k * 8, yy, SKY, 4)


def pic_plane(cv, x, y, s):
    # An-12 nose-down with flame and smoke.
    cv.circle(x + int(0.72 * s), y + int(0.30 * s), 10, GREY, filled=True)
    cv.circle(x + int(0.80 * s), y + int(0.20 * s), 14, GREY, filled=True)
    cv.circle(x + int(0.88 * s), y + int(0.34 * s), 8, GREY, filled=True)
    # flame
    cv.poly([(x + int(0.55 * s), y + int(0.72 * s)),
             (x + int(0.68 * s), y + int(0.52 * s)),
             (x + int(0.80 * s), y + int(0.72 * s))], ORANGE)
    cv.poly([(x + int(0.60 * s), y + int(0.72 * s)),
             (x + int(0.68 * s), y + int(0.60 * s)),
             (x + int(0.76 * s), y + int(0.72 * s))], GOLD)
    # fuselage: one clean nose-down bar, tail fin, swept wing
    cv.line(x + int(0.10 * s), y + int(0.26 * s),
            x + int(0.56 * s), y + int(0.54 * s), INK, 9)
    cv.poly([(x + int(0.10 * s), y + int(0.26 * s)),
             (x + int(0.02 * s), y + int(0.12 * s)),
             (x + int(0.10 * s), y + int(0.12 * s)),
             (x + int(0.18 * s), y + int(0.28 * s))], INK)
    cv.poly([(x + int(0.30 * s), y + int(0.38 * s)),
             (x + int(0.46 * s), y + int(0.56 * s)),
             (x + int(0.36 * s), y + int(0.58 * s)),
             (x + int(0.22 * s), y + int(0.42 * s))], INK)
    # ground
    cv.rect(x, y + int(0.86 * s), s, 6, INK)


# ------------------------------------------------------------------- layout
PANELS = [
    dict(kicker="UKRAINE", color=NAVY,
         head="KERCH BRIDGE\nROAD ARCH FALLS",
         sub="UKRAINE HITS BRIDGE 2ND DAY;\n2 KILLED, TRAFFIC HALTED",
         pic=pic_bridge),
    dict(kicker="USA", color=RED,
         head="PELTOLA WINS\nALASKA SENATE",
         sub="DEMOCRATS TAKE 56-44 SENATE;\nFIRST ALASKA NATIVE SENATOR",
         pic=pic_ballot),
    dict(kicker="MARKETS", color=TEAL,
         head="NVIDIA: $115.8BN\nRECORD QUARTER",
         sub="REVENUE DOUBLES, UP 103%;\nNEXT QUARTER GUIDED $130BN",
         pic=pic_chip),
    dict(kicker="HEALTH", color=(122, 30, 30),
         head="EBOLA TOLL\nPASSES 11,500",
         sub="CONGO CASES TOP 11,500;\n5,600 DEAD; STILL SPREADING",
         pic=pic_virus),
    dict(kicker="PACIFIC", color=(20, 90, 120),
         head="CYCLONE XAVIER\nCAT 5 PACIFIC",
         sub="GUSTS 315 KM/H BATTER\nNORTHERN COOK ISLANDS",
         pic=pic_cyclone),
    dict(kicker="RUSSIA", color=(70, 70, 70),
         head="PLANE CRASH\n19 KILLED",
         sub="RUSSIAN AN-12 DOWN IN SIBERIA;\nTECHNICAL FAULT SUSPECTED",
         pic=pic_plane),
]


def build():
    cv = Canvas(W, H, PAPER)
    # outer frame
    cv.rect(0, 0, W, 6, INK)
    cv.rect(0, H - 6, W, 6, INK)
    cv.rect(0, 0, 6, H, INK)
    cv.rect(W - 6, 0, 6, H, INK)

    # ---- masthead
    cv.text_centred(26, "WORLD NEWS", 10, INK)
    cv.rect(24, 112, 976, 6, RED)
    cv.text_centred(130, "WEDNESDAY, 18 NOVEMBER 2026", 4, RED)
    cv.rect(24, 166, 976, 3, INK)

    # ---- lead story: the Gulf
    lx, ly, lw, lh = 24, 180, 976, 216
    cv.rect(lx, ly, lw, lh, WHITE)
    cv.rect(lx, ly, lw, 34, RED)
    cv.text(lx + 16, ly + 7, "LEAD STORY - THE GULF", 3, WHITE)
    cv.text(lx + 20, ly + 52, "US JETS STRIKE IRAN", 5, INK)
    cv.text(lx + 20, ly + 94, "IRAN HITS US BASES", 5, INK)
    sub = ("MISSILE SITE ON QESHM ISLAND HIT AFTER IRAN "
           "TARGETED US BASES IN BAHRAIN; DRONES AIMED "
           "AT KUWAIT BASE WERE INTERCEPTED")
    for i, line in enumerate(wrap_text(sub, 2, 640)):
        cv.text(lx + 20, ly + 146 + i * 18, line, 2, (60, 56, 48))
    pic_gulf(cv, lx + 716, ly + 40, 180)
    # frame around lead
    cv.hline(lx, ly, lw, INK, 3)
    cv.hline(lx, ly + lh - 3, lw, INK, 3)
    cv.vline(lx, ly, lh, INK, 3)
    cv.vline(lx + lw - 3, ly, lh, INK, 3)

    # ---- six panels, 2 columns x 3 rows
    pw, ph = 482, 168
    for idx, p in enumerate(PANELS):
        col = idx % 2
        row = idx // 2
        px = 24 + col * (pw + 12)
        py = 408 + row * (ph + 8)
        cv.rect(px, py, pw, ph, WHITE)
        cv.rect(px, py, pw, 30, p["color"])
        cv.text(px + 12, py + 6, p["kicker"], 2, WHITE)
        for i, line in enumerate(p["head"].split("\n")):
            cv.text(px + 14, py + 42 + i * 26, line, 3, INK)
        sub_lines = []
        for raw in p["sub"].split("\n"):
            sub_lines += wrap_text(raw, 2, pw - 128 - 28)
        for i, line in enumerate(sub_lines[:3]):
            cv.text(px + 14, py + 102 + i * 18, line, 2, (60, 56, 48))
        p["pic"](cv, px + pw - 128, py + 36, 116)
        cv.hline(px, py, pw, INK, 2)
        cv.hline(px, py + ph - 2, pw, INK, 2)
        cv.vline(px, py, ph, INK, 2)
        cv.vline(px + pw - 2, py, ph, INK, 2)

    # ---- footer strip: the day's other quakes
    fy = 940
    cv.rect(24, fy, 976, 60, NAVY)
    cv.text_centred(fy + 12, "ALSO TODAY: M6.0 QUAKE IN PAPUA NEW GUINEA - M5.3 IN ROMANIA", 2, WHITE)
    cv.text_centred(fy + 36, "SOURCES: REUTERS - AP - AFP - 18 NOVEMBER 2026", 2, (200, 205, 215))
    return cv


# -------------------------------------------------------------- PNG writer
def png_bytes(cv):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
