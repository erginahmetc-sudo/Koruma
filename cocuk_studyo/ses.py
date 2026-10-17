# -*- coding: utf-8 -*-
"""Ses: karakter sesleri (espeak-ng, TR+EN), dudak senkronu zarfı, sentezlenmiş müzik ve efektler."""
import os, io, wave, hashlib, math, random, subprocess
import numpy as np
from karakter import CHARS

SR = 44100
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
os.makedirs(CACHE, exist_ok=True)
VOICE_START = 0.18

def _espeak(text, lang, var, pitch, speed):
    v = ("tr" if lang == "tr" else "en-us") + "+" + var
    raw = subprocess.run(["espeak-ng", "-v", v, "-s", str(int(speed)), "-p", str(pitch), "-a", "175", "--stdout", text], capture_output=True, check=True).stdout
    w = wave.open(io.BytesIO(raw)); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    sr = w.getframerate()
    return np.interp(np.arange(0, len(a) * SR / sr) * sr / SR, np.arange(len(a)), a).astype(np.float32)

def _trim(a):
    i = np.where(np.abs(a) > 0.012)[0]
    return a[i[0]:i[-1] + 1] if len(i) else a

def voice_for(S):
    """Çekim için TR+EN seslendirmesi (dizi) – süreye sığacak şekilde hızlandırılır."""
    if not S.get("say_tr"): return None
    cid = S.get("speaker") or "pofi"; var, pitch, speed = CHARS[cid]["voice"]
    maxlen = S["dur"] - VOICE_START - 0.08
    key = hashlib.md5(f"{cid}|{S['say_tr']}|{S['say_en']}|{maxlen:.2f}".encode()).hexdigest()
    p = os.path.join(CACHE, key + ".npy")
    if os.path.exists(p): return np.load(p)
    sp = speed
    for _ in range(5):
        a = _trim(_espeak(S["say_tr"], "tr", var, pitch, sp)); b = _trim(_espeak(S["say_en"], "en", var, pitch, sp))
        v = np.concatenate([a, np.zeros(int(.10 * SR), np.float32), b])
        if len(v) / SR <= maxlen or sp >= 260: break
        sp = min(260, sp * len(v) / SR / (maxlen - .03))
    v = v[: int(maxlen * SR)].copy(); n = int(.03 * SR); v[-n:] *= np.linspace(1, 0, n)
    v = v / max(1e-6, np.abs(v).max()) * .85
    np.save(p, v); return v

def mouth_env(v, dur):
    """Dudak açıklığı: 30 fps, 0..1."""
    nf = int(round(dur * FPS)); env = np.zeros(nf, np.float32)
    if v is None: return env
    hop = SR // FPS
    for f in range(nf):
        a = int((f / FPS - VOICE_START) * SR)
        if a < 0 or a >= len(v): continue
        seg = v[a:a + hop]; env[f] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    if env.max() > 0: env = np.clip(env / (np.percentile(env[env > 0], 90) * 1.1), 0, 1)
    k = np.array([.25, .5, .25]); return np.convolve(env, k, mode="same")

# ------------------------------------------------------------ enstrüman
NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)
def _tone(f, dur, kind, vol):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == "pluck": w = np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t) + .12 * np.sin(6 * np.pi * f * t); env = np.minimum(1, t / .004) * np.exp(-t * 7)
    elif kind == "bell": w = np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 5); env = np.minimum(1, t / .003) * np.exp(-t * 3.2)
    elif kind == "bass": w = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t)); env = np.minimum(1, t / .01) * np.exp(-t * 3.5)
    else: w = np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t); env = np.minimum(1, t / .05) * np.minimum(1, (dur - t) / .08)  # pad
    return (w * env * vol).astype(np.float32)

def _add(buf, x, t0):
    i = int(t0 * SR)
    if i < 0 or i >= len(buf): return
    e = min(len(buf), i + len(x)); buf[i:e] += x[:e - i]

PROGS = [[(0, 4, 7), (7, 11, 14), (9, 12, 16), (5, 9, 12)], [(0, 4, 7), (5, 9, 12), (7, 11, 14), (0, 4, 7)], [(9, 12, 16), (5, 9, 12), (0, 4, 7), (7, 11, 14)]]
MOTIFS = [[0, 2, 4, 2, 7, 4, 2, 0], [4, 4, 2, 0, 2, 4, 7, 4], [7, 4, 2, 4, 0, 2, 4, 2], [0, 4, 7, 12, 7, 4, 2, 4]]
PENT = [0, 2, 4, 7, 9, 12, 14, 16]

def music(total, episodes):
    """episodes: [(start_s, dur_s, bpm, key, prog, seed)]"""
    out = np.zeros(int(total * SR) + SR, np.float32)
    kick = (np.sin(2 * np.pi * np.cumsum(np.linspace(140, 48, int(.16 * SR))) / SR) * np.linspace(1, 0, int(.16 * SR))).astype(np.float32)
    rs = np.random.RandomState(1); noise = rs.randn(int(.08 * SR)).astype(np.float32)
    hat = noise[:int(.03 * SR)] * np.linspace(1, 0, int(.03 * SR)); snare = noise * np.linspace(1, 0, len(noise)) ** 2
    for (t0, dur, bpm, key, pi, seed) in episodes:
        rnd = random.Random(seed); beat = 60.0 / bpm; bar = beat * 4; prog = PROGS[pi % 3]; root = 48 + key
        for b in range(int(dur / bar) + 1):
            tb = t0 + b * bar; ch = prog[b % 4]; mot = MOTIFS[(b // 2 + seed) % 4]
            _add(out, _tone(NOTE(root + 12 + ch[0]), bar, "pad", .035), tb); _add(out, _tone(NOTE(root + 12 + ch[1]), bar, "pad", .03), tb); _add(out, _tone(NOTE(root + 12 + ch[2]), bar, "pad", .03), tb)
            for k in range(8):
                deg = ch[mot[k] % 3] + (12 if k % 4 == 3 else 0) if (b % 2 == 0 or k % 2 == 0) else mot[k]
                if rnd.random() < .18: deg = rnd.choice(PENT)
                _add(out, _tone(NOTE(root + 12 + deg), beat * .5, "pluck", .10), tb + k * beat * .5)
            for k, off in ((0, 0), (2, 0), (3, .5)):
                _add(out, _tone(NOTE(root - 12 + ch[0]), beat * .9, "bass", .17), tb + k * beat + off * beat)
            for k in range(4):
                _add(out, kick * (.15 if k % 2 == 0 else .06), tb + k * beat)
                _add(out, hat * .035, tb + k * beat + beat / 2)
                if k % 2 == 1: _add(out, snare * .03, tb + k * beat)
    return out

def sfx(kind, n=1):
    if kind == "tada":
        o = np.zeros(int(1.0 * SR), np.float32)
        for i, m in enumerate((72, 76, 79, 84)): _add(o, _tone(NOTE(m), .5, "bell", .22), i * .09)
        return o
    if kind == "ding":
        return _tone(NOTE(72 + PENT[min(n, 7)]), .45, "bell", .25)
    if kind == "boing":
        t = np.arange(int(.35 * SR)) / SR; f = 300 + 250 * np.sin(2 * np.pi * 5 * t) * np.exp(-t * 6)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * .25).astype(np.float32)
    if kind == "swoosh":
        t = np.arange(int(.22 * SR)) / SR; nz = np.random.RandomState(3).randn(len(t)); env = np.sin(np.pi * t / .22) ** 2
        y = np.cumsum(nz) * .0; k = np.ones(40) / 40; return (np.convolve(nz, k, mode="same") * env * .05).astype(np.float32)
    if kind == "pop":
        t = np.arange(int(.1 * SR)) / SR; return (np.sin(2 * np.pi * np.cumsum(np.linspace(500, 1400, len(t))) / SR) * np.exp(-t * 28) * .16).astype(np.float32)
    return np.zeros(10, np.float32)

def build_audio(shots, episodes):
    total = sum(s["dur"] for s in shots); n = int(total * SR) + SR
    voc = np.zeros(n, np.float32); fx = np.zeros(n, np.float32); duck = np.ones(n, np.float32)
    t = 0.0
    for S in shots:
        _add(fx, sfx("swoosh"), t + .0); _add(fx, sfx("pop"), t + .12)
        v = S.get("_voice")
        if v is not None:
            a = int((t + VOICE_START) * SR); voc[a:a + len(v)] += v; duck[a:a + len(v)] = .45
        k = S.get("sfx")
        if k == "ding" and S.get("count"):
            for i in range(S["count"]): _add(fx, sfx("ding", i), t + .25 + i * min(.12, 1.0 / S["count"]))
        elif k: _add(fx, sfx(k), t + .1)
        t += S["dur"]
    w = int(.05 * SR); duck = np.convolve(duck, np.ones(w) / w, mode="same")
    mus = music(total, episodes)[:n]
    mix = mus * duck * .9 + voc * .95 + fx
    mix = mix / max(1e-6, np.abs(mix).max()) * .9
    return (mix * 32767).astype(np.int16)

def write_wav(path, pcm):
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
