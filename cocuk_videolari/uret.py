# -*- coding: utf-8 -*-
"""Kullanim: python3 uret.py <1|2|3> [--test N]
Sahne basina 2.0 sn, 300 sahne = 10:00. Ses: espeak-ng (TR+EN), muzik: sentezlenmis."""
import os, sys, math, random, subprocess, json, wave, io, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cairosvg
from icerik import VIDEOS

W, H, FPS, SC = 1280, 720, 20, 2.0
NF = int(FPS * SC)
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(HERE, "node_modules/@twemoji/svg")
OUT = os.path.join(HERE, "cikti")
CACHE = os.path.join(HERE, ".cache")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
NAVY = (27, 31, 75)
PAL = [("#FF6B6B", "#FFD93D"), ("#4D96FF", "#6BCB77"), ("#B983FF", "#FF86C8"), ("#00C2A8", "#FFE066"),
       ("#FF9F45", "#FF6B9D"), ("#5AC8FA", "#A78BFA"), ("#7ED957", "#38B6FF"), ("#FF5E8A", "#FFC145")]

def hx(c):
    c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def clip(x, a=0.0, b=1.0): return max(a, min(b, x))
def back(x):
    x = clip(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

_fonts = {}
def font(sz):
    if sz not in _fonts: _fonts[sz] = ImageFont.truetype(FONT, sz)
    return _fonts[sz]

# ------------------------------------------------------------ gorseller
def sticker(im):
    """Beyaz 'cikartma' kenari ekle."""
    pad = 24
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    big.paste(im, (pad, pad))
    a = big.split()[3].filter(ImageFilter.MaxFilter(21))
    white = Image.new("RGBA", big.size, (255, 255, 255, 255)); white.putalpha(a)
    white.alpha_composite(big)
    return white.resize((512, 512), Image.LANCZOS)

_emo = {}
def emoji_img(ch):
    if ch in _emo: return _emo[ch]
    base = "-".join(f"{ord(c):x}" for c in ch)
    for name in (base, "-".join(f"{ord(c):x}" for c in ch if c != "️")):
        p = os.path.join(SVG, name + ".svg")
        if os.path.exists(p): break
    else:
        raise FileNotFoundError("emoji yok: %r (%s)" % (ch, base))
    png = cairosvg.svg2png(url=p, output_width=420, output_height=420)
    _emo[ch] = sticker(Image.open(io.BytesIO(png)).convert("RGBA"))
    return _emo[ch]

SHAPE_COL = ["#FF5252", "#2979FF", "#FFC400", "#00C853", "#AA00FF", "#FF6D00", "#00B8D4", "#F50057"]
def shape_img(key, i=0):
    name = key.split(":")[1]; c = hx(SHAPE_COL[sum(map(ord, name)) % len(SHAPE_COL)]) + (255,)
    Sz = 1024; im = Image.new("RGBA", (Sz, Sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im); m = Sz // 2
    def reg(n, R, rot=-90):
        return [(m + R * math.cos(math.radians(rot + k * 360 / n)), m + 20 + R * math.sin(math.radians(rot + k * 360 / n))) for k in range(n)]
    if name == "circle": d.ellipse((90, 90, 934, 934), fill=c)
    elif name == "square": d.rectangle((140, 140, 884, 884), fill=c)
    elif name == "triangle": d.polygon([(m, 110), (930, 860), (94, 860)], fill=c)
    elif name == "rectangle": d.rectangle((50, 250, 974, 774), fill=c)
    elif name == "star":
        pts = []
        for k in range(10):
            R = 470 if k % 2 == 0 else 200
            a = math.radians(-90 + k * 36); pts.append((m + R * math.cos(a), m + 30 + R * math.sin(a)))
        d.polygon(pts, fill=c)
    elif name == "heart":
        pts = []
        for k in range(200):
            t = k / 200 * 2 * math.pi
            pts.append((m + 27 * 16 * math.sin(t) ** 3, 470 - 27 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))))
        d.polygon(pts, fill=c)
    elif name == "diamond": d.polygon([(m, 70), (950, m), (m, 954), (74, m)], fill=c)
    elif name == "oval": d.ellipse((40, 230, 984, 794), fill=c)
    elif name == "hexagon": d.polygon(reg(6, 450, 0), fill=c)
    elif name == "pentagon": d.polygon(reg(5, 470), fill=c)
    elif name == "crescent":
        d.ellipse((120, 90, 900, 870), fill=c); d.ellipse((330, 40, 1010, 800), fill=(0, 0, 0, 0))
    if name not in ("crescent",):  # sevimli yuz
        d.ellipse((m - 150, m - 60, m - 90, m + 20), fill=(30, 30, 60, 255)); d.ellipse((m + 90, m - 60, m + 150, m + 20), fill=(30, 30, 60, 255))
        d.arc((m - 100, m - 10, m + 100, m + 140), 20, 160, fill=(30, 30, 60, 255), width=22)
    return sticker(im.resize((420, 420), Image.LANCZOS))

def get_img(ch):
    if ch not in _emo:
        _emo[ch] = shape_img(ch) if ch.startswith("shape:") else emoji_img(ch)
    return _emo[ch]

def fit_font(text, maxw, sz):
    while sz > 24 and font(sz).getlength(text) > maxw: sz -= 4
    return font(sz), sz

def banner(text, fill, border, maxw=1150, sz=104):
    f, sz = fit_font(text, maxw - 90, sz)
    tw = int(f.getlength(text)); w, h = tw + 90, sz + 56
    im = Image.new("RGBA", (w + 14, h + 18), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((7, 14, w + 7, h + 14), 40, fill=(0, 0, 0, 70))
    d.rounded_rectangle((7, 4, w + 7, h + 4), 40, fill=fill, outline=border, width=10)
    d.text((7 + w / 2, 4 + h / 2 + 4), text, font=f, fill=NAVY, anchor="mm")
    return im

# ------------------------------------------------------------ sahne hazirlik
def prepare(S, i):
    p = PAL[(i * 3 + S.get("seed", 0)) % len(PAL)]
    if S.get("bg"):
        c = hx(S["bg"]); c1, c2 = mix(c, (255, 255, 255), 0.18), mix(c, (0, 0, 0), 0.12)
    else:
        c1, c2 = hx(p[0]), hx(p[1])
    g = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(c1)[None, None, :] * (1 - g) + np.array(c2)[None, None, :] * g)
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    S["_bg"] = Image.fromarray(arr, "RGB"); S["_ray"] = mix(c1, (255, 255, 255), 0.22)
    S["_acc"] = mix(c1, c2, 0.5) if not S.get("bg") else hx(S["bg"])
    S["_tr"] = banner(S["tr"], (255, 255, 255, 255), S["_acc"] + (255,))
    S["_en"] = banner(S["en"], (255, 245, 190, 255), mix(S["_acc"], (0, 0, 0), 0.25) + (255,), sz=92)
    S["_ems"] = [S["em"]] if isinstance(S["em"], str) else list(S["em"])
    for e in S["_ems"]: get_img(e)
    rnd = random.Random(i * 7 + 1)
    S["_bub"] = [(rnd.random(), rnd.random(), rnd.uniform(20, 70), rnd.uniform(0.3, 0.9)) for _ in range(12)]
    S["_conf"] = [(rnd.random(), rnd.random(), tuple(rnd.choice([(255, 82, 82), (255, 196, 0), (41, 121, 255), (0, 200, 83), (255, 255, 255)])), rnd.uniform(0.4, 1.0)) for _ in range(22)]

def put(fr, im, cx, cy, size, ang=0.0):
    size = max(8, int(size)); r = im.resize((size, size), Image.BILINEAR)
    if abs(ang) > 0.5: r = r.rotate(ang, resample=Image.BILINEAR, expand=True)
    fr.paste(r, (int(cx - r.width / 2), int(cy - r.height / 2)), r)

def render_frame(S, fi, gi, total):
    t = fi / FPS
    fr = S["_bg"].copy(); d = ImageDraw.Draw(fr)
    rot = t * 25 + gi * 17
    for k in range(0, 16, 2):
        a0, a1 = math.radians(rot + k * 22.5), math.radians(rot + (k + 1) * 22.5)
        d.polygon([(640, 360), (640 + 1400 * math.cos(a0), 360 + 1400 * math.sin(a0)), (640 + 1400 * math.cos(a1), 360 + 1400 * math.sin(a1))], fill=S["_ray"])
    for bx, by, r, sp in S["_bub"]:
        y = H + 80 - ((t * sp * 160 + by * (H + 160)) % (H + 160)); x = bx * W + 25 * math.sin(t * 3 + bx * 9)
        d.ellipse((x - r, y - r, x + r, y + r), fill=S["_ray"])
    tpl = S["tpl"]; beat = abs(math.sin(math.pi * (t % 0.5) / 0.5)); pop = back((t - 0.02) / 0.32)
    ems = S["_ems"]; cx, cy = 640, 365
    bob = -34 * beat
    if tpl in ("single", "sound", "color", "shape", "spin", "countdown", "bignum"):
        e = get_img(ems[0]); size = 400 * pop
        if tpl == "color":
            d.ellipse((cx - 245, cy - 245 + bob * .3, cx + 245, cy + 245 + bob * .3), fill=(255, 255, 255)); size = 330 * pop
        ang = 7 * math.sin(t * 9) if tpl != "spin" else 360 * back(t / 0.9) * 2 % 360 if t < 0.9 else 7 * math.sin(t * 9)
        if tpl == "sound": ang = 14 * math.sin(t * 28); cx2 = 560
        else: cx2 = cx
        if tpl in ("countdown", "bignum"):
            cx2 = 880 if tpl == "countdown" else 900
            f, _ = fit_font(S["big"], 420, 330 if len(S["big"]) < 3 else 250)
            d.ellipse((200, 170, 600, 570), fill=(255, 255, 255), outline=S["_acc"], width=14)
            d.text((400, 372 + bob * .4), S["big"], font=f, fill=NAVY, anchor="mm")
            size = 330 * pop
            if tpl == "countdown": cy2 = cy - 180 * clip(t / 2) * (1 if S["big"] != "🚀" else 2) + 100; bob = 0
            else: cy2 = cy + bob
        else:
            cy2 = cy + bob
        put(fr, e, cx2, cy2, size, ang)
        if tpl == "sound":
            put(fr, get_img("🔊"), 980, 300 + bob, 220 * pop, 0)
            for k in range(3):
                put(fr, get_img("🎵"), 930 + k * 100, 470 - ((t * 140 + k * 50) % 160), 90, 12 * math.sin(t * 6 + k))
    elif tpl in ("trio", "title"):
        if len(ems) == 1: ems = ems * 3
        for k, (ox, sz) in enumerate(((-340, 270), (0, 390), (340, 270))):
            ph = beat if k != 1 else 1 - beat
            put(fr, get_img(ems[k]), cx + ox, cy + 20 - 45 * ph, sz * clip(back((t - 0.05 * k) / 0.32)), 9 * math.sin(t * 8 + k * 2))
    elif tpl == "count":
        n = S["n"]; e = get_img(ems[0])
        best = (0, 1, 1)
        for rows in range(1, 6):
            cols = math.ceil(n / rows); cell = min(740 / cols, 340 / rows)
            if cell > best[0]: best = (cell, rows, cols)
        cell, rows, cols = best
        d.ellipse((60, 190, 400, 530), fill=(255, 255, 255), outline=S["_acc"], width=14)
        f, _ = fit_font(str(n), 260, 250); d.text((230, 365 + bob * .3), str(n), font=f, fill=NAVY, anchor="mm")
        x0 = 430 + (780 - cols * cell) / 2 + cell / 2; y0 = 365 - rows * cell / 2 + cell / 2 + 10
        for k in range(n):
            r_, c_ = divmod(k, cols)
            if r_ == rows - 1 and rows * cols > n: pass
            ap = clip(back((t - 0.12 - k * min(0.07, 1.0 / n)) / 0.28))
            if ap > 0:
                put(fr, e, x0 + c_ * cell, y0 + r_ * cell - (14 * beat if k % 2 else 0), cell * 0.95 * ap, 8 * math.sin(t * 7 + k))
    # konfeti
    for fx, fy, col, sp in S["_conf"]:
        y = (fy * 900 + t * 260 * sp) % 900 - 90; x = fx * W + 30 * math.sin(t * 5 + fy * 20)
        d.rectangle((x, y, x + 14, y + 22), fill=col)
    # bantlar
    k = back((t - 0.06) / 0.35); tr, en = S["_tr"], S["_en"]
    fr.paste(tr, (int(W / 2 - tr.width / 2), int(-tr.height + (tr.height + 22) * k)), tr)
    fr.paste(en, (int(W / 2 - en.width / 2), int(H + 10 - (en.height + 28) * back((t - 0.14) / 0.35))), en)
    d.rectangle((0, H - 8, int(W * (gi + t / SC) / total), H), fill=(255, 255, 255))
    if t < 0.1: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * (1 - t / 0.1))
    return fr

# ------------------------------------------------------------ ses
def espeak(text, lang, speed):
    cmd = ["espeak-ng", "-v", ("tr+f3" if lang == "tr" else "en-us+f3"), "-s", str(int(speed)), "-p", "78", "-a", "170", "--stdout", text]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    w = wave.open(io.BytesIO(raw)); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    sr = w.getframerate()
    return np.interp(np.arange(0, len(a) * SR / sr) * sr / SR, np.arange(len(a)), a).astype(np.float32)

def trim(a):
    idx = np.where(np.abs(a) > 0.01)[0]
    return a[idx[0]:idx[-1] + 1] if len(idx) else a

def voice(S):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5((S["say_tr"] + "|" + S["say_en"]).encode()).hexdigest()
    p = os.path.join(CACHE, key + ".npy")
    if os.path.exists(p): return np.load(p)
    sp = 150
    for _ in range(4):
        a = trim(espeak(S["say_tr"], "tr", sp)); b = trim(espeak(S["say_en"], "en", sp))
        v = np.concatenate([a, np.zeros(int(0.12 * SR), np.float32), b])
        if len(v) / SR <= 1.6 or sp >= 300: break
        sp = min(300, sp * len(v) / SR / 1.55)
    v = v[: int(1.65 * SR)]
    v[-int(.03 * SR):] *= np.linspace(1, 0, int(.03 * SR))
    np.save(p, v); return v

NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
def tone(f, dur, kind="tri", vol=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * t) + (0.35 * np.sin(4 * np.pi * f * t) if kind == "lead" else 0)
    if kind == "tri": w = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))
    env = np.minimum(1, t / 0.008) * np.exp(-t * (6 if kind == "lead" else 3))
    return (w * env * vol).astype(np.float32)

def music(nbars, key, seed):
    rnd = random.Random(seed); out = np.zeros(int(nbars * SC * SR) + SR, np.float32)
    prog = [(0, 4, 7), (7, 11, 14), (9, 12, 16), (5, 9, 12)]  # C G Am F
    pent = [0, 2, 4, 7, 9, 12, 14, 16]
    kick = np.sin(2 * np.pi * np.cumsum(np.linspace(130, 45, int(.14 * SR))) / SR) * np.linspace(1, 0, int(.14 * SR))
    hat = (np.random.RandomState(seed).randn(int(.04 * SR)) * np.linspace(1, 0, int(.04 * SR))).astype(np.float32)
    for b in range(nbars):
        t0 = b * SC; ch = prog[b % 4]; root = 48 + key
        for k in range(8):  # sekizlik arpej / melodi
            deg = ch[k % 3] + (12 if k % 2 else 0) if rnd.random() < .55 else rnd.choice(pent)
            s = tone(NOTE(root + 12 + deg), .22, "lead", .11); i0 = int((t0 + k * .25) * SR); out[i0:i0 + len(s)] += s
        for k in (0, 2):
            s = tone(NOTE(root - 12 + ch[0]), .45, "tri", .22); i0 = int((t0 + k * .5) * SR); out[i0:i0 + len(s)] += s
        for k in range(4):
            i0 = int((t0 + k * .5) * SR); out[i0:i0 + len(kick)] += kick.astype(np.float32) * .16
            i1 = int((t0 + k * .5 + .25) * SR); out[i1:i1 + len(hat)] += hat * .05
    return out

def build_audio(scenes, key, seed):
    n = len(scenes); total = int(n * SC * SR)
    mus = music(n, key, seed)[:total]; duck = np.ones(total, np.float32); vox = np.zeros(total, np.float32)
    pop = np.sin(2 * np.pi * np.cumsum(np.linspace(500, 1500, int(.12 * SR))) / SR) * np.linspace(1, 0, int(.12 * SR)) * .25
    for i, S in enumerate(scenes):
        v = voice(S); a = int((i * SC + 0.22) * SR); vox[a:a + len(v)] += v
        duck[a:a + len(v)] = 0.5
        s0 = int(i * SC * SR); vox[s0:s0 + len(pop)] += pop.astype(np.float32)
    k = int(.04 * SR); duck = np.convolve(duck, np.ones(k) / k, mode="same")
    mix_ = mus * duck + vox * 0.95
    mix_ = mix_ / max(1e-6, np.abs(mix_).max()) * 0.92
    return (mix_ * 32767).astype(np.int16)

# ------------------------------------------------------------ ana akis
def main():
    vid = int(sys.argv[1]); test = int(sys.argv[sys.argv.index("--test") + 1]) if "--test" in sys.argv else 0
    V = VIDEOS[vid](); scenes = V["scenes"][:test] if test else V["scenes"]
    assert test or len(scenes) == 300, len(scenes)
    os.makedirs(OUT, exist_ok=True)
    for i, S in enumerate(scenes): prepare(S, i)
    print("ses...", flush=True)
    pcm = build_audio(scenes, {1: 0, 2: 7, 3: 5}[vid], vid)
    wav = os.path.join(CACHE, f"video{vid}.wav"); os.makedirs(CACHE, exist_ok=True)
    with wave.open(wav, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    outf = os.path.join(OUT, f"{vid}_{V['slug']}" + (f"_test{test}" if test else "") + ".mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                           "-ac", "2", "-movflags", "+faststart", "-shortest", outf], stdin=subprocess.PIPE)
    total = len(scenes)
    for gi, S in enumerate(scenes):
        for fi in range(NF):
            fr = render_frame(S, fi, gi, total)
            if fi == 14 and gi == 0:
                fr.save(os.path.join(OUT, f"{vid}_kapak.jpg"), quality=90)
            ff.stdin.write(fr.tobytes())
        if gi % 20 == 0: print(f"sahne {gi}/{total}", flush=True)
    ff.stdin.close(); ff.wait()
    json.dump([{k: v for k, v in s.items() if not k.startswith("_")} | {"baslangic_sn": i * SC, "sure_sn": SC} for i, s in enumerate(scenes)],
              open(os.path.join(OUT, f"{vid}_senaryo.json"), "w"), ensure_ascii=False, indent=1)
    print("bitti", outf)

if __name__ == "__main__":
    main()
