# -*- coding: utf-8 -*-
"""Arka planlar (paralaks), rekvizitler, yazı. Hepsi cairo ile 1920x1080."""
import os, io, math, random
import numpy as np
from PIL import Image, ImageFilter
import cairosvg
import cairocffi as cairo
from karakter import rgb, shade, ellipse, fill, clip, PI

W, H = 1920, 1080
GROUND = 735            # karakter ayak çizgisi
HERE = os.path.dirname(os.path.abspath(__file__))
SVG_DIRS = [os.path.join(HERE, "node_modules/@twemoji/svg"), os.path.join(HERE, "../cocuk_videolari/node_modules/@twemoji/svg")]

# ------------------------------------------------------------ emoji / şekil rekvizitleri
_surf = {}
def _to_surface(im):
    a = np.array(im.convert("RGBA")).astype(np.float32)
    al = a[..., 3:4] / 255.0
    a[..., :3] *= al
    bgra = np.dstack([a[..., 2], a[..., 1], a[..., 0], a[..., 3]]).astype(np.uint8)
    buf = bytearray(np.ascontiguousarray(bgra).tobytes())
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
    return s, buf

def _sticker(im, pad=26, grow=23):
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); big.paste(im, (pad, pad))
    a = big.split()[3].filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(1.2))
    white = Image.new("RGBA", big.size, (255, 255, 255, 255)); white.putalpha(a); white.alpha_composite(big)
    return white

def emoji_surface(ch):
    if ch in _surf: return _surf[ch][0]
    base = "-".join(f"{ord(c):x}" for c in ch)
    for d in SVG_DIRS:
        for name in (base, "-".join(f"{ord(c):x}" for c in ch if c != "️")):
            p = os.path.join(d, name + ".svg")
            if os.path.exists(p):
                png = cairosvg.svg2png(url=p, output_width=620, output_height=620)
                s, buf = _to_surface(_sticker(Image.open(io.BytesIO(png))))
                _surf[ch] = (s, buf, s.get_width()); return s
    raise FileNotFoundError("emoji yok: %r" % ch)

def draw_prop(ctx, ch, x, y, size, rot=0.0, alpha=1.0):
    if size < 3: return
    s = emoji_surface(ch); w = s.get_width(); k = size / (w - 52)
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(k, k); ctx.translate(-w / 2, -w / 2)
    ctx.set_source_surface(s, 0, 0); ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
    ctx.paint_with_alpha(alpha); ctx.restore()

SHAPE_COL = {"circle": "#FF5252", "square": "#2979FF", "triangle": "#FFC400", "rectangle": "#00C853", "star": "#FFB300", "heart": "#F50057",
             "diamond": "#00B8D4", "oval": "#AA00FF", "hexagon": "#FF6D00", "pentagon": "#26A69A", "crescent": "#7C4DFF"}
def draw_shape(ctx, name, x, y, size, rot=0.0, T=0.0):
    if size < 3: return
    c = rgb(SHAPE_COL[name]); r = size / 2
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    def path():
        ctx.new_path()
        if name == "circle": ctx.arc(0, 0, r, 0, 2 * PI)
        elif name == "square": ctx.rectangle(-r * .86, -r * .86, r * 1.72, r * 1.72)
        elif name == "rectangle": ctx.rectangle(-r, -r * .6, r * 2, r * 1.2)
        elif name == "oval": ellipse(ctx, 0, 0, r, r * .66)
        elif name == "triangle": ctx.move_to(0, -r); ctx.line_to(r * .98, r * .78); ctx.line_to(-r * .98, r * .78); ctx.close_path()
        elif name == "diamond": ctx.move_to(0, -r); ctx.line_to(r * .8, 0); ctx.line_to(0, r); ctx.line_to(-r * .8, 0); ctx.close_path()
        elif name in ("hexagon", "pentagon"):
            n = 6 if name == "hexagon" else 5
            for i in range(n):
                a = -PI / 2 + i * 2 * PI / n; (ctx.move_to if i == 0 else ctx.line_to)(r * math.cos(a), r * math.sin(a))
            ctx.close_path()
        elif name == "star":
            for i in range(10):
                rr = r if i % 2 == 0 else r * .46; a = -PI / 2 + i * PI / 5
                (ctx.move_to if i == 0 else ctx.line_to)(rr * math.cos(a), rr * math.sin(a))
            ctx.close_path()
        elif name == "heart":
            for k in range(0, 61):
                t = k / 60 * 2 * PI
                px, py = r * .062 * 16 * math.sin(t) ** 3, -r * .062 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) + r * .05
                (ctx.move_to if k == 0 else ctx.line_to)(px, py)
            ctx.close_path()
        elif name == "crescent":
            ctx.arc(0, 0, r, 0.6, 2 * PI - .6); ctx.arc_negative(r * .35, 0, r * .82, 2 * PI - .9, .9); ctx.close_path()
    path(); ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(26); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    g = cairo.RadialGradient(-r * .3, -r * .35, r * .1, 0, 0, r * 1.3); g.add_color_stop_rgb(0, *shade(c, .4)); g.add_color_stop_rgb(1, *shade(c, -.15))
    ctx.set_source(g); ctx.fill()
    if name != "crescent":
        for sx in (-1, 1): ellipse(ctx, sx * r * .26, -r * .08, r * .075, r * .1); fill(ctx, rgb("#1F2349"))
        ctx.set_source_rgb(*rgb("#1F2349")); ctx.set_line_width(max(5, r * .05)); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.arc(0, r * .02, r * .24, .25, PI - .25); ctx.stroke()
    ctx.restore()

# ------------------------------------------------------------ yazı
def text_fit(ctx, txt, maxw, size, bold=True):
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    while size > 22:
        ctx.set_font_size(size)
        if ctx.text_extents(txt)[4] <= maxw: break
        size -= 3
    return size

def draw_text(ctx, txt, cx, cy, size, fillc=(.11, .12, .29), stroke=(1, 1, 1), sw=10, maxw=1500):
    size = text_fit(ctx, txt, maxw, size)
    ext = ctx.text_extents(txt); x = cx - ext[4] / 2; y = cy + size * .34
    ctx.save(); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x, y); ctx.text_path(txt)
    ctx.set_source_rgb(*stroke); ctx.set_line_width(sw); ctx.stroke_preserve()
    ctx.set_source_rgb(*fillc); ctx.fill(); ctx.restore()
    return ext[4]

def rrect(ctx, x, y, w, h, r):
    ctx.new_path(); ctx.arc(x + w - r, y + r, r, -PI / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI); ctx.arc(x + r, y + r, r, PI, 1.5 * PI); ctx.close_path()

def caption(ctx, tr, en, k, accent):
    """Alt yazı: Türkçe büyük, İngilizce altında. k: 0..1 giriş animasyonu."""
    if not tr: return
    oy = (1 - k) * 260
    ctx.save(); ctx.translate(0, oy)
    ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    s1 = text_fit(ctx, tr, 1560, 104); w1 = ctx.text_extents(tr)[4]
    s2 = text_fit(ctx, en, 1560, 74); w2 = ctx.text_extents(en)[4]
    pw = max(w1, w2) + 120; ph = 222; px = (W - pw) / 2; py = H - ph - 28
    rrect(ctx, px + 4, py + 12, pw, ph, 54); ctx.set_source_rgba(0, 0, 0, .22); ctx.fill()
    rrect(ctx, px, py, pw, ph, 54); ctx.set_source_rgba(1, 1, 1, .94); ctx.fill_preserve()
    ctx.set_source_rgb(*accent); ctx.set_line_width(12); ctx.stroke()
    draw_text(ctx, tr, W / 2, py + 76, s1, stroke=(1, 1, 1), sw=0.1, maxw=1560)
    draw_text(ctx, en, W / 2, py + 166, s2, fillc=shade((.35, .38, .62), -.1), stroke=(1, 1, 1), sw=0.1, maxw=1560)
    ctx.restore()

def sparkle(ctx, x, y, r, a):
    ctx.save(); ctx.translate(x, y); ctx.new_path()
    for i in range(8):
        rr = r if i % 2 == 0 else r * .22; ang = i * PI / 4 - PI / 2
        (ctx.move_to if i == 0 else ctx.line_to)(rr * math.cos(ang), rr * math.sin(ang))
    ctx.close_path(); ctx.set_source_rgba(1, 1, .85, a); ctx.fill(); ctx.restore()

# ------------------------------------------------------------ arka planlar
def vgrad(ctx, stops, y0=0, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for o, c in stops: g.add_color_stop_rgb(o, *rgb(c))
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()

def cloud(ctx, x, y, s, a=.95):
    for dx, dy, r in ((-60, 8, 46), (-18, -16, 58), (34, -4, 52), (78, 12, 40), (0, 22, 56)):
        ellipse(ctx, x + dx * s, y + dy * s, r * s, r * s); ctx.set_source_rgba(1, 1, 1, a); ctx.fill()

def hills(ctx, cols, base, amp, scroll, seed, step=24):
    rnd = random.Random(seed)
    for li, c in enumerate(cols):
        ph = rnd.random() * 6; f1 = .0031 + li * .0007; f2 = .0075; sp = (li + 1) * .35
        y0 = base + li * 70
        ctx.new_path(); ctx.move_to(-10, H + 10)
        for x in range(-10, W + step, step):
            xs = x + scroll * sp * 60
            ctx.line_to(x, y0 - amp * (math.sin(xs * f1 + ph) * .6 + math.sin(xs * f2 + ph * 2) * .25))
        ctx.line_to(W + 10, H + 10); ctx.close_path(); ctx.set_source_rgb(*rgb(c)); ctx.fill()

def flowers(ctx, y0, n, seed, scroll, cols=("#FF6B9D", "#FFD93D", "#FFFFFF", "#B983FF")):
    rnd = random.Random(seed)
    for i in range(n):
        x = (rnd.random() * (W + 200) - 100 + scroll * 38) % (W + 200) - 100; y = y0 + rnd.random() * (H - y0 - 20); s = .7 + (y - y0) / (H - y0)
        c = rgb(rnd.choice(cols)); ctx.set_source_rgb(*rgb("#3E9B4F")); ctx.set_line_width(5 * s); ctx.move_to(x, y); ctx.line_to(x, y + 26 * s); ctx.stroke()
        for k in range(5):
            a = k * 2 * PI / 5; ellipse(ctx, x + 9 * s * math.cos(a), y + 9 * s * math.sin(a), 8 * s, 8 * s); fill(ctx, c)
        ellipse(ctx, x, y, 6 * s, 6 * s); fill(ctx, rgb("#FFC93C"))

def tree(ctx, x, y, s, c1="#4CAF50", c2="#388E3C"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.rectangle(-14, -120, 28, 125); ctx.set_source_rgb(*rgb("#8D5A3B")); ctx.fill()
    for dx, dy, r, c in ((-40, -150, 58, c2), (42, -148, 56, c2), (0, -200, 72, c1), (-8, -150, 62, c1)):
        ellipse(ctx, dx, dy, r, r); fill(ctx, rgb(c))
    ctx.restore()

def sun(ctx, x, y, r, T):
    g = cairo.RadialGradient(x, y, r * .6, x, y, r * 2.6); g.add_color_stop_rgba(0, 1, .95, .6, .55); g.add_color_stop_rgba(1, 1, .95, .6, 0)
    ctx.set_source(g); ctx.arc(x, y, r * 2.6, 0, 2 * PI); ctx.fill()
    ctx.save(); ctx.translate(x, y); ctx.rotate(T * .15); ctx.set_source_rgba(1, .9, .4, .8); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(12): a = i * PI / 6; ctx.move_to(r * 1.25 * math.cos(a), r * 1.25 * math.sin(a)); ctx.line_to(r * 1.55 * math.cos(a), r * 1.55 * math.sin(a))
    ctx.stroke(); ctx.restore()
    ellipse(ctx, x, y, r, r); fill(ctx, rgb("#FFD93D"))

def bg_meadow(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#4FC3F7"), (.6, "#B3E5FC"), (1, "#E1F5FE")]); sun(ctx, 1500, 200, 74, T)
    for i in range(4): cloud(ctx, ((i * 560 + T * 18 * (1 + i * .3)) % (W + 500)) - 250, 140 + i * 70, .9 + i * .2)
    hills(ctx, ["#9CCC65", "#7CB342", "#66BB6A"], 640, 140, sc, seed); flowers(ctx, 800, 26, seed, sc)
    for i in range(3): tree(ctx, 160 + i * 680 + (seed % 5) * 40, 790, .8 + (i % 2) * .2)

def bg_forest(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#A5D6A7"), (.55, "#E6EE9C"), (1, "#F9FBE7")])
    ctx.save(); ctx.set_source_rgba(1, 1, .7, .18)
    for i in range(4):
        x = 300 + i * 450 + 40 * math.sin(T * .5 + i); ctx.move_to(x, 0); ctx.line_to(x + 140, 0); ctx.line_to(x + 40, H); ctx.line_to(x - 220, H); ctx.close_path(); ctx.fill()
    ctx.restore()
    hills(ctx, ["#7CB342", "#558B2F"], 700, 90, sc, seed)
    for i in range(6): tree(ctx, 90 + i * 360 - (sc * 24) % 360, 770, 1.1 + (i % 3) * .2, "#43A047", "#2E7D32")
    flowers(ctx, 830, 16, seed, sc, ("#FF8A65", "#FFFFFF", "#FFD54F"))

def bg_beach(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#29B6F6"), (.5, "#81D4FA"), (.52, "#26C6DA"), (.7, "#4DD0E1"), (.71, "#FFE0B2"), (1, "#FFCC80")]); sun(ctx, 300, 190, 70, T)
    for i in range(3): cloud(ctx, ((i * 700 + T * 22) % (W + 500)) - 250, 130 + i * 60, 1 + i * .15)
    ctx.set_source_rgba(1, 1, 1, .55); ctx.set_line_width(6)
    for r in range(5):
        y = 560 + r * 34; ctx.move_to(0, y)
        for x in range(0, W + 30, 30): ctx.line_to(x, y + 9 * math.sin(x * .02 + T * 1.6 + r))
        ctx.stroke()
    ctx.rectangle(1450, 470, 22, 330); ctx.set_source_rgb(*rgb("#8D5A3B")); ctx.fill()
    for a in (-2.4, -1.9, -1.2, -0.7):
        ctx.save(); ctx.translate(1461, 470); ctx.rotate(a + .05 * math.sin(T)); ellipse(ctx, 90, 0, 110, 24); fill(ctx, rgb("#43A047")); ctx.restore()

def bg_under(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#00ACC1"), (.6, "#26C6DA"), (1, "#80DEEA")])
    ctx.save(); ctx.set_source_rgba(1, 1, 1, .09)
    for i in range(5):
        x = 200 + i * 400 + 50 * math.sin(T * .4 + i); ctx.move_to(x, 0); ctx.line_to(x + 120, 0); ctx.line_to(x - 100, H); ctx.line_to(x - 260, H); ctx.close_path(); ctx.fill()
    ctx.restore()
    rnd = random.Random(seed)
    for i in range(18):
        x = rnd.random() * W + 18 * math.sin(T + i); y = (H - ((T * (40 + 30 * rnd.random()) + rnd.random() * H) % (H + 80)) + 40); r = 8 + rnd.random() * 20
        ctx.new_path(); ctx.arc(x, y, r, 0, 2 * PI); ctx.set_source_rgba(1, 1, 1, .28); ctx.fill_preserve(); ctx.set_source_rgba(1, 1, 1, .6); ctx.set_line_width(3); ctx.stroke()
    ctx.rectangle(0, 790, W, 300); ctx.set_source_rgb(*rgb("#FFE0A3")); ctx.fill()
    for i in range(9):
        x = 100 + i * 230; ctx.set_source_rgb(*rgb("#2E9B5B" if i % 2 else "#43B96B")); ctx.set_line_width(20); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, 800); ctx.curve_to(x + 30 * math.sin(T * 1.3 + i), 700, x - 30 * math.sin(T * 1.3 + i), 620, x + 14 * math.sin(T * 1.3 + i), 560 + (i % 3) * 40); ctx.stroke()
    for i in range(4): ellipse(ctx, 260 + i * 480, 830, 70, 44); fill(ctx, rgb(("#FF7EB6", "#FFB74D", "#BA68C8", "#FF8A65")[i]))

def bg_space(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#1A1446"), (.6, "#3B2A7A"), (1, "#6A3FA0")])
    rnd = random.Random(seed)
    for i in range(70):
        x, y = rnd.random() * W, rnd.random() * 760; a = .55 + .35 * math.sin(T * .9 + i)
        ellipse(ctx, x, y, 2 + rnd.random() * 3, 2 + rnd.random() * 3); fill(ctx, (1, 1, .9), a)
    for (x, y, r, c) in ((1500, 230, 120, "#FF8A65"), (330, 280, 70, "#4DD0E1")):
        g = cairo.RadialGradient(x - r * .3, y - r * .3, r * .1, x, y, r); g.add_color_stop_rgb(0, *shade(rgb(c), .35)); g.add_color_stop_rgb(1, *shade(rgb(c), -.25))
        ctx.set_source(g); ctx.arc(x, y, r, 0, 2 * PI); ctx.fill()
    ctx.save(); ctx.translate(1500, 230); ctx.rotate(-.35); ctx.scale(1, .28); ctx.new_path(); ctx.arc(0, 0, 200, 0, 2 * PI); ctx.restore()
    ctx.set_source_rgba(1, .9, .7, .6); ctx.set_line_width(12); ctx.stroke()
    hills(ctx, ["#9E92C9", "#7E70B0"], 720, 70, sc, seed)

def bg_candy(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#FFB3D9"), (.6, "#FFE0F0"), (1, "#FFF3E0")])
    for i in range(3): cloud(ctx, ((i * 700 + T * 15) % (W + 500)) - 250, 150 + i * 80, 1.1)
    hills(ctx, ["#FFCFE5", "#FF9FCB", "#C79BFF"], 650, 120, sc, seed)
    for i in range(5):
        x = 150 + i * 400; ctx.rectangle(x - 7, 560, 14, 240); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        for k, c in enumerate(("#FF5C8D", "#FFD93D", "#4DD0E1")):
            ctx.new_path(); ctx.arc(x, 540, 78 - k * 22, 0, 2 * PI); ctx.set_source_rgb(*rgb(c)); ctx.fill()
    rnd = random.Random(seed)
    for i in range(40):
        ellipse(ctx, rnd.random() * W, 800 + rnd.random() * 260, 14, 5, rnd.random() * 3); fill(ctx, rgb(rnd.choice(("#FF5C8D", "#FFD93D", "#4DD0E1", "#FFFFFF"))))

def bg_snow(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#90CAF9"), (.7, "#E3F2FD"), (1, "#FFFFFF")]); cloud(ctx, 400 + T * 8, 150, 1.3, .9)
    hills(ctx, ["#FFFFFF", "#E1F0FF", "#CFE6FF"], 640, 110, sc, seed)
    for i in range(5):
        x = 150 + i * 430; y = 780
        for k in range(3):
            ctx.new_path(); ctx.move_to(x, y - 150 - k * 70); ctx.line_to(x + 90 - k * 18, y - k * 70); ctx.line_to(x - 90 + k * 18, y - k * 70); ctx.close_path(); ctx.set_source_rgb(*rgb("#2E7D5B")); ctx.fill()
    rnd = random.Random(seed)
    for i in range(50):
        x = (rnd.random() * W + 30 * math.sin(T + i)) % W; y = (rnd.random() * H + T * (50 + 40 * rnd.random())) % H
        ellipse(ctx, x, y, 5, 5); fill(ctx, (1, 1, 1), .9)

def bg_room(ctx, T, seed, sc):
    pal = [("#FFE0B2", "#FFCC80"), ("#E1BEE7", "#CE93D8"), ("#B3E5FC", "#81D4FA"), ("#C8E6C9", "#A5D6A7")][seed % 4]
    ctx.rectangle(0, 0, W, H); ctx.set_source_rgb(*rgb(pal[0])); ctx.fill()
    for i in range(0, W, 120): ctx.rectangle(i, 0, 60, 760); ctx.set_source_rgba(1, 1, 1, .25); ctx.fill()
    rrect(ctx, 1280, 140, 440, 360, 30); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    rrect(ctx, 1300, 160, 400, 320, 20); g = cairo.LinearGradient(0, 160, 0, 480); g.add_color_stop_rgb(0, *rgb("#4FC3F7")); g.add_color_stop_rgb(1, *rgb("#E1F5FE")); ctx.set_source(g); ctx.fill()
    cloud(ctx, 1380 + 20 * math.sin(T * .3), 270, .8)
    ctx.rectangle(1500, 160, 8, 320); ctx.rectangle(1300, 316, 400, 8); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    ctx.rectangle(0, 760, W, 330); ctx.set_source_rgb(*rgb("#D7A86E")); ctx.fill()
    for i in range(0, W, 240): ctx.rectangle(i, 760, 4, 330); ctx.set_source_rgba(0, 0, 0, .12); ctx.fill()
    ellipse(ctx, 700, 940, 520, 90); fill(ctx, rgb(pal[1]))
    ellipse(ctx, 700, 940, 380, 60); fill(ctx, (1, 1, 1), .35)
    for i, c in enumerate(("#FF5C8D", "#FFD93D", "#4DD0E1")):
        ctx.rectangle(120 + i * 70, 680 - (i % 2) * 20, 64, 64); ctx.set_source_rgb(*rgb(c)); ctx.fill()

def bg_town(ctx, T, seed, sc):
    vgrad(ctx, [(0, "#81D4FA"), (1, "#E1F5FE")]); cloud(ctx, 300 + T * 14, 150, 1.2)
    rnd = random.Random(seed)
    for layer, (base, cols) in enumerate(((620, ("#B0BEC5", "#90A4AE", "#CFD8DC")), (700, ("#FF8A65", "#FFD54F", "#4DB6AC", "#BA68C8", "#64B5F6")))):
        x = -((sc * (22 + layer * 22)) % 360)
        while x < W:
            w = 200 + (rnd.random() * 100 if layer else 80); h = 200 + rnd.random() * (260 - layer * 60)
            ctx.rectangle(x, base - h + 100, w - 14, h + 80); ctx.set_source_rgb(*rgb(cols[int(x // 5) % len(cols)])); ctx.fill()
            for wy in range(int(base - h + 140), int(base + 40), 70):
                for wx in range(int(x + 24), int(x + w - 60), 62): ctx.rectangle(wx, wy, 34, 40); ctx.set_source_rgba(1, 1, 1, .8); ctx.fill()
            x += w
        rnd = random.Random(seed + 1)
    ctx.rectangle(0, 790, W, 300); ctx.set_source_rgb(*rgb("#78909C")); ctx.fill()
    ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(12)
    for i in range(-1, 12): x = i * 200 - (T * 160) % 200; ctx.move_to(x, 940); ctx.line_to(x + 100, 940); ctx.stroke()

def bg_color(ctx, T, seed, sc, hexc="#FF5252"):
    c = rgb(hexc); vgrad(ctx, [(0, "#%02X%02X%02X" % tuple(int(v * 255) for v in shade(c, .35))), (1, hexc)])
    ctx.save(); ctx.translate(960, 540); ctx.rotate(T * .12)
    for i in range(0, 16, 2):
        a0, a1 = i * PI / 8, (i + 1) * PI / 8; ctx.move_to(0, 0); ctx.line_to(1500 * math.cos(a0), 1500 * math.sin(a0)); ctx.line_to(1500 * math.cos(a1), 1500 * math.sin(a1)); ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, .16); ctx.fill(); ctx.restore()
    hills(ctx, [("#%02X%02X%02X" % tuple(int(v * 255) for v in shade(c, -.12)))], 760, 60, sc, seed)

BGS = {"meadow": bg_meadow, "forest": bg_forest, "beach": bg_beach, "under": bg_under, "space": bg_space,
       "candy": bg_candy, "snow": bg_snow, "room": bg_room, "town": bg_town}
# karakterlerin durduğu zemin çizgisi (görsel olarak uyumlu)
def draw_bg(ctx, theme, T, seed, sc, color=None):
    if theme == "color": bg_color(ctx, T, seed, sc, color or "#FF5252")
    else: BGS[theme](ctx, T, seed, sc)
