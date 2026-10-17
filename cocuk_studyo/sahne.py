# -*- coding: utf-8 -*-
"""Tek bir çekimin (shot) belirli bir andaki karesini çizer."""
import math, random
import cairocffi as cairo
from karakter import draw_char, rgb, shade, clip, ease, back, ellipse, fill, PI
from dunya import (W, H, GROUND, draw_bg, draw_prop, draw_shape, caption, draw_text, sparkle, rrect)

def lerp(a, b, t): return a + (b - a) * t

def prop_anim(p, t, T):
    """Dönüş: (x, y, size, rot, alpha)"""
    x, y, s = p["x"], p["y"], p["size"]; d = t - p.get("delay", 0.0)
    if d < 0: return None
    k = back(d / .30); a = p.get("anim", "pop"); rot = 0.0
    if a == "bounce": y -= 36 * abs(math.sin(PI * (T * 2.0 + p.get("ph", 0))))
    elif a == "float": y += 14 * math.sin(T * 3 + p.get("ph", 0)); rot = .08 * math.sin(T * 2 + p.get("ph", 0))
    elif a == "spin": rot = d * 3.0
    elif a == "wiggle": rot = .18 * math.sin(T * 14)
    elif a == "rise": y -= 180 * ease(d / 1.6)
    elif a == "fall": y = lerp(y - 520, y, ease(d / .45)); k = 1
    elif a == "slide": x = lerp(x - 900, x, ease(d / .5)); k = 1
    return x, y, s * k, rot, 1.0

def render_shot(ctx, S, t, T, mouth=0.0):
    dur = S["dur"]; u = clip(t / dur)
    # ---- dünya (kamera uygulanır)
    ctx.save()
    z0, z1, px0, px1 = S.get("cam", (1.0, 1.06, 0, 0))
    z = lerp(z0, z1, ease(u)); px = lerp(px0, px1, ease(u))
    ctx.translate(W / 2 + px, H / 2 + 20); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2 - 20)
    draw_bg(ctx, S["bg"], T, S["seed"], T * S.get("scroll", 1.0) + S["seed"] * 3, S.get("color"))
    # parıltılar
    rnd = random.Random(S["seed"] * 13 + 5)
    for i in range(7):
        x = rnd.random() * W; y = 120 + rnd.random() * 520; sparkle(ctx, x + 14 * math.sin(T + i), y, 16 + rnd.random() * 18, .35 + .35 * (.5 + .5 * math.sin(T * 1.4 + i * 2)))
    # şekil/emoji (karakterlerin arkasında kalanlar)
    for p in S.get("props_back", []):
        r = prop_anim(p, t, T)
        if r: _prop(ctx, p, *r, T)
    for c in S.get("chars", []):
        spk = (c["id"] == S.get("speaker"))
        draw_char(ctx, c["id"], c["x"], GROUND + c.get("dy", 0), c.get("s", 1.12), T, c.get("pose", "talk" if spk else "idle"),
                  mouth if spk else 0.0, c.get("flip", False), S.get("bpm", 120), c.get("mood", "happy"), seed=c.get("seed", hash(c["id"]) % 7), look=c.get("look", 0.0))
    for p in S.get("props", []):
        r = prop_anim(p, t, T)
        if r: _prop(ctx, p, *r, T)
    # sayma ızgarası
    if S.get("count"): _count(ctx, S, t, T)
    ctx.restore()
    # ---- ekran katmanı
    if S.get("big"): _big(ctx, S, t)
    caption(ctx, S.get("tr"), S.get("en"), back((t - .05) / .32), S.get("accent", (.3, .6, .9)))
    if t < .22:  # iris açılışı (yumuşak, parlama yok)
        r = 260 + (t / .22) ** 1.5 * 1200
        ctx.save(); ctx.rectangle(0, 0, W, H); ctx.arc(W / 2, H / 2, max(r, .1), 0, 2 * PI); ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgb(*S.get("accent", (.3, .6, .9))); ctx.fill(); ctx.restore()

def _prop(ctx, p, x, y, s, rot, a, T):
    if p.get("shape"): draw_shape(ctx, p["shape"], x, y, s, rot, T)
    else: draw_prop(ctx, p["e"], x, y, s, rot, a)

def _count(ctx, S, t, T):
    n = S["count"]; e = S["count_e"]
    x0, x1, y0, y1 = 760, 1820, 200, 700
    best = (0, 1, 1)
    for rows in range(1, 6):
        cols = math.ceil(n / rows); cell = min((x1 - x0) / cols, (y1 - y0) / rows)
        if cell > best[0]: best = (cell, rows, cols)
    cell, rows, cols = best; size = min(cell * .92, 270)
    gx = (x0 + x1) / 2 - cols * cell / 2 + cell / 2; gy = (y0 + y1) / 2 - rows * cell / 2 + cell / 2
    for k in range(n):
        r_, c_ = divmod(k, cols); d = t - .25 - k * min(.12, 1.0 / n)
        if d < 0: continue
        sc = back(d / .28)
        draw_prop(ctx, e, gx + c_ * cell, gy + r_ * cell - 22 * abs(math.sin(PI * (T * 2 + k * .13))) * .8, size * sc, .1 * math.sin(T * 5 + k))

def _big(ctx, S, t):
    txt = S["big"]; k = back((t - .04) / .3)
    cx, cy, r = 250, 250, 150 * k
    if r < 5: return
    ctx.save(); ctx.new_path(); ctx.arc(cx + 5, cy + 12, r, 0, 2 * PI); ctx.set_source_rgba(0, 0, 0, .22); ctx.fill()
    ctx.new_path(); ctx.arc(cx, cy, r, 0, 2 * PI); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve(); ctx.set_source_rgb(*S.get("accent", (.3, .6, .9))); ctx.set_line_width(16); ctx.stroke()
    draw_text(ctx, txt, cx, cy - 6, int(230 * k) if len(txt) < 3 else int(160 * k), stroke=(1, 1, 1), sw=.1, maxw=250)
    ctx.restore()
