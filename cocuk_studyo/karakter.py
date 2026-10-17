# -*- coding: utf-8 -*-
"""Özgün karakterler: 'Pofi ve Dostları' (Baloncuk Vadisi). Tamamı cairo ile vektör çizilir.
Hiçbir mevcut çizgi film karakterine/markasına dayanmaz."""
import math
import cairocffi as cairo

PI = math.pi

def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def shade(c, f):
    """f>0 beyaza, f<0 siyaha doğru karıştır."""
    t = (1, 1, 1) if f > 0 else (0, 0, 0); f = abs(f)
    return tuple(c[i] + (t[i] - c[i]) * f for i in range(3))
def clip(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clip(x); return x * x * (3 - 2 * x)
def back(x):
    x = clip(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

CHARS = {
    "pofi": dict(name="Pofi", c="#2EC4B6", belly="#C6F7F1", ears="sprout", acc=None, voice=("f3", 84, 150)),
    "mimi": dict(name="Mimi", c="#FF7EB6", belly="#FFE3EF", ears="long", acc="bow", voice=("f5", 92, 152)),
    "dodo": dict(name="Dodo", c="#FFC931", belly="#FFF1BA", ears="tuft", acc="beak", voice=("f2", 98, 158)),
    "zuzu": dict(name="Zuzu", c="#9B6BFF", belly="#E6DAFF", ears="antenna", acc="glasses", voice=("f4", 88, 150)),
    "bobo": dict(name="Bobo", c="#FF8A3D", belly="#FFE2C6", ears="round", acc="scarf", voice=("f1", 66, 148)),
    "luna": dict(name="Luna", c="#5B7CFF", belly="#D6DEFF", ears="cat", acc="star", voice=("f3", 74, 146)),
}

BW, BH = 300.0, 280.0   # gövde ölçüsü (s=1)

def squircle(ctx, w, h, kt=0.60, kb=0.70):
    a, b = w / 2, h / 2
    ctx.new_path(); ctx.move_to(0, -b)
    ctx.curve_to(a * kt, -b, a, -b * kt, a, 0)
    ctx.curve_to(a, b * kb, a * kb, b, 0, b)
    ctx.curve_to(-a * kb, b, -a, b * kb, -a, 0)
    ctx.curve_to(-a, -b * kt, -a * kt, -b, 0, -b)
    ctx.close_path()

def ellipse(ctx, x, y, rx, ry, rot=0.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(rx, ry)
    ctx.new_path(); ctx.arc(0, 0, 1, 0, 2 * PI); ctx.restore()

def fill(ctx, col, a=1.0): ctx.set_source_rgba(col[0], col[1], col[2], a); ctx.fill()

def draw_ears(ctx, ch, col, T):
    k = ch["ears"]; dark = shade(col, -0.18); pink = (1, .62, .72)
    top = -BH / 2 - 30 - 8
    wob = math.sin(T * 3.1)
    if k == "round":
        for sx in (-1, 1):
            ellipse(ctx, sx * 105, top + 36, 56, 56); fill(ctx, col)
            ellipse(ctx, sx * 105, top + 38, 32, 32); fill(ctx, pink, .9)
    elif k == "long":
        for sx in (-1, 1):
            ellipse(ctx, sx * 70, top - 100 + 10 * wob * sx * .5, 44, 150, sx * (0.16 + .05 * wob)); fill(ctx, col)
            ellipse(ctx, sx * 70, top - 96 + 10 * wob * sx * .5, 23, 118, sx * (0.16 + .05 * wob)); fill(ctx, pink, .85)
    elif k == "sprout":
        ctx.set_line_width(12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgb(*rgb("#3E9B4F"))
        ctx.move_to(0, top + 30); ctx.curve_to(4 * wob, top - 20, -6 * wob, top - 40, 0, top - 62); ctx.stroke()
        for sx in (-1, 1):
            ctx.save(); ctx.translate(0, top - 62); ctx.rotate(sx * (0.9 + .1 * wob)); ellipse(ctx, sx * 38, 0, 46, 22); fill(ctx, rgb("#5ED36B")); ctx.restore()
    elif k == "antenna":
        for sx in (-1, 1):
            ctx.set_line_width(9); ctx.set_source_rgb(*dark); ctx.move_to(sx * 55, top + 24)
            ex, ey = sx * (105 + 8 * wob), top - 78
            ctx.curve_to(sx * 70, top - 30, sx * 90, top - 50, ex, ey); ctx.stroke()
            g = cairo.RadialGradient(ex, ey, 2, ex, ey, 30); g.add_color_stop_rgba(0, 1, 1, .8, 1); g.add_color_stop_rgba(.5, 1, .86, .3, 1); g.add_color_stop_rgba(1, 1, .7, .2, .0)
            ctx.set_source(g); ctx.arc(ex, ey, 30, 0, 2 * PI); ctx.fill()
            ellipse(ctx, ex, ey, 15, 15); fill(ctx, rgb("#FFE066"))
    elif k == "tuft":
        for i, (dx, ang, ln) in enumerate(((-26, -.4, 70), (0, 0, 88), (26, .4, 70))):
            ctx.save(); ctx.translate(dx, top + 28); ctx.rotate(ang + .06 * wob); ellipse(ctx, 0, -ln / 2, 17, ln / 2); fill(ctx, shade(col, -.06) if i % 2 else col); ctx.restore()
    elif k == "cat":
        for sx in (-1, 1):
            ctx.new_path(); ctx.move_to(sx * 40, top + 36); ctx.curve_to(sx * 70, top - 20, sx * 110, top - 60, sx * 128, top - 52)
            ctx.curve_to(sx * 150, top - 30, sx * 140, top + 40, sx * 120, top + 66); ctx.close_path(); fill(ctx, col)
            ctx.new_path(); ctx.move_to(sx * 66, top + 34); ctx.curve_to(sx * 88, top - 6, sx * 108, top - 30, sx * 120, top - 28)
            ctx.curve_to(sx * 128, top - 6, sx * 124, top + 30, sx * 112, top + 50); ctx.close_path(); fill(ctx, pink, .8)

def draw_cape(ctx, col, T):
    c = shade(col, -.35); w = 8 * math.sin(T * 4)
    ctx.new_path(); ctx.move_to(-130, -BH / 2 - 50); ctx.curve_to(-190 - w, -40, -170, 30, -150 + w, 36)
    ctx.line_to(150 - w, 36); ctx.curve_to(170, 30, 190 + w, -40, 130, -BH / 2 - 50); ctx.close_path(); fill(ctx, c)

def draw_char(ctx, key, x, y, s=1.0, T=0.0, pose="idle", mouth=0.0, flip=False, bpm=120, mood="happy", seed=0, look=0.0):
    """(x,y) = ayak tabanı merkezi. pose: idle|talk|dance|cheer|wave|jump."""
    ch = CHARS[key]; col = rgb(ch["c"]); belly = rgb(ch["belly"]); dark = shade(col, -.30)
    ph = T * bpm / 60.0
    amp = {"idle": .10, "talk": .14, "dance": 1.0, "cheer": .9, "wave": .18, "jump": 1.0}.get(pose, .1)
    b = abs(math.sin(PI * ph)) if pose in ("dance", "cheer", "jump") else .5 + .5 * math.sin(2 * PI * ph * .5 + seed)
    lift = b * 44 * amp * (1.6 if pose == "jump" else 1.0)
    land = (1 - b) ** 5 if pose in ("dance", "cheer", "jump") else 0.0
    sy = 1 + 0.07 * b * amp - 0.10 * land; sx = 1 - 0.04 * b * amp + 0.08 * land
    tilt = (0.07 * math.sin(PI * ph + seed) if pose in ("dance", "cheer") else 0.02 * math.sin(T * 2 + seed)) * (1 if not flip else -1)
    ctx.save(); ctx.translate(x, y - lift * s); ctx.scale(s * (-1 if flip else 1), s)
    # gölge
    ctx.save(); ctx.translate(0, lift); ellipse(ctx, 0, 0, 150 - lift * .6, 24 - lift * .12); fill(ctx, (0, 0, 0), .20); ctx.restore()
    ctx.rotate(tilt); ctx.scale(sx, sy)
    bc = -BH / 2 - 30          # gövde merkezi y
    if ch["acc"] == "star": draw_cape(ctx, col, T)
    # kulaklar/anten
    draw_ears(ctx, ch, col, T)
    # ayaklar
    for sgn in (-1, 1):
        ellipse(ctx, sgn * 84, -18, 52, 30); fill(ctx, dark)
    # kollar (gövdenin arkası)
    side_ang = {"idle": 34, "talk": 30, "dance": 120, "cheer": 150, "wave": 34, "jump": 140}.get(pose, 34)
    for sgn in (-1, 1):
        ang = side_ang + (10 * math.sin(PI * ph * 2 + sgn) if pose in ("dance", "cheer", "jump") else 3 * math.sin(T * 2 + sgn))
        if pose == "wave" and sgn == 1: ang = 150 + 24 * math.sin(T * 9)
        sh = (sgn * BW * .46, bc + 24); L = 112
        a = math.radians(ang); hx, hy = sh[0] + sgn * L * math.sin(a), sh[1] + L * math.cos(a)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(46); ctx.set_source_rgb(*dark); ctx.move_to(*sh); ctx.line_to(hx, hy); ctx.stroke()
        ctx.set_line_width(38); ctx.set_source_rgb(*col); ctx.move_to(*sh); ctx.line_to(hx, hy); ctx.stroke()
        ellipse(ctx, hx, hy, 27, 27); fill(ctx, shade(col, .12))
    # gövde
    ctx.save(); ctx.translate(0, bc); squircle(ctx, BW, BH)
    g = cairo.RadialGradient(-70, -90, 20, -20, -20, 230)
    g.add_color_stop_rgb(0, *shade(col, .38)); g.add_color_stop_rgb(.45, *col); g.add_color_stop_rgb(1, *shade(col, -.22))
    ctx.set_source(g); ctx.fill_preserve(); ctx.set_line_width(6); ctx.set_source_rgba(*shade(col, -.38), .85); ctx.stroke()
    # karın
    ellipse(ctx, 0, 78, 108, 78); fill(ctx, belly, .92)
    # parlama
    ellipse(ctx, -78, -102, 34, 18, -.5); fill(ctx, (1, 1, 1), .38)
    ctx.restore()
    # eşarp (gövde üstü)
    if ch["acc"] == "scarf":
        ctx.set_line_width(40); ctx.set_source_rgb(*rgb("#E94B5A")); ctx.move_to(-118, bc + 34); ctx.curve_to(-60, bc + 82, 60, bc + 82, 118, bc + 34); ctx.stroke()
        ellipse(ctx, 70, bc + 104, 22, 46, .2); fill(ctx, rgb("#E94B5A")); ellipse(ctx, 70, bc + 110, 14, 30, .2); fill(ctx, rgb("#FFD2D6"), .7)
    # yüz
    fy = bc - 22
    bl = 1.0
    cyc = (T + seed * 1.37) % 3.4
    if cyc < .14: bl = 1 - math.sin(cyc / .14 * PI) * .92
    eye_scale = {"wow": 1.15, "cheer": 1.0, "sleepy": .45, "happy": 1.0}.get(mood, 1.0)
    for sgn in (-1, 1):
        ex = sgn * 66
        ellipse(ctx, ex, fy, 38, 46 * bl * eye_scale); fill(ctx, (1, 1, 1))
        px, py = ex + look * 8, fy + (3 if mood != "wow" else 0)
        ellipse(ctx, px, py, 23, 31 * bl * eye_scale); fill(ctx, rgb("#1F2349"))
        if bl > .5:
            ellipse(ctx, px - 8, py - 11, 8, 9); fill(ctx, (1, 1, 1)); ellipse(ctx, px + 8, py + 9, 4, 4.5); fill(ctx, (1, 1, 1), .85)
        # kaş
        ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgba(*shade(col, -.5), .9)
        lift_b = {"wow": -20, "cheer": -8, "sad": 6}.get(mood, 0)
        tl = (sgn * -12) if mood == "sad" else 0
        ctx.move_to(ex - 26, fy - 66 + lift_b + sgn * 3 - tl); ctx.curve_to(ex - 8, fy - 78 + lift_b, ex + 10, fy - 78 + lift_b, ex + 26, fy - 66 + lift_b - sgn * 3 + tl); ctx.stroke()
        # yanak
        ellipse(ctx, sgn * 112, fy + 56, 24, 15); fill(ctx, (1, .42, .52), .5)
    # ağız / gaga
    my = fy + 58
    if ch["acc"] == "beak":
        ctx.new_path(); ctx.move_to(-30, my - 40); ctx.curve_to(-20, my - 62, 20, my - 62, 30, my - 40); ctx.curve_to(18, my - 22, -18, my - 22, -30, my - 40); fill(ctx, rgb("#FF8A1F"))
    op = max(mouth, {"wow": .75, "cheer": .6}.get(mood, 0.0))
    if op < .08 and mood == "sad":
        ctx.set_line_width(8); ctx.set_source_rgb(*rgb("#7A2B3A")); ctx.move_to(-30, my + 10); ctx.curve_to(-16, my - 14, 16, my - 14, 30, my + 10); ctx.stroke()
    elif op < .08:
        ctx.set_line_width(8); ctx.set_source_rgb(*rgb("#7A2B3A")); ctx.move_to(-34, my - 6); ctx.curve_to(-18, my + 22, 18, my + 22, 34, my - 6); ctx.stroke()
    else:
        ctx.new_path(); ctx.move_to(-38, my - 8); ctx.curve_to(-30, my + 12 + op * 54, 30, my + 12 + op * 54, 38, my - 8); ctx.curve_to(18, my - 14, -18, my - 14, -38, my - 8); ctx.close_path()
        ctx.set_source_rgb(*rgb("#6B1D33")); ctx.fill_preserve(); ctx.set_source_rgb(*rgb("#7A2B3A")); ctx.set_line_width(5); ctx.stroke()
        ellipse(ctx, 0, my + 6 + op * 38, 22, 8 + op * 9); fill(ctx, (1, .5, .6))
    # aksesuarlar
    if ch["acc"] == "bow":
        for sgn in (-1, 1):
            ctx.save(); ctx.translate(92, bc - 150); ctx.rotate(sgn * .5 + .2); ellipse(ctx, sgn * 34, 0, 36, 24); fill(ctx, rgb("#FF4F9A")); ctx.restore()
        ellipse(ctx, 92, bc - 150, 14, 14); fill(ctx, rgb("#FF94C2"))
    if ch["acc"] == "glasses":
        ctx.set_source_rgb(*rgb("#2B2F6B")); ctx.set_line_width(8)
        for sgn in (-1, 1): ctx.new_path(); ctx.arc(sgn * 66, fy, 50, 0, 2 * PI); ctx.stroke()
        ctx.move_to(-16, fy); ctx.line_to(16, fy); ctx.stroke()
    if ch["acc"] == "star":
        ctx.new_path()
        for i in range(10):
            r = 24 if i % 2 == 0 else 10; a = -PI / 2 + i * PI / 5
            (ctx.move_to if i == 0 else ctx.line_to)(r * math.cos(a), bc - 112 + r * math.sin(a))
        ctx.close_path(); fill(ctx, rgb("#FFE066"))
    ctx.restore()
