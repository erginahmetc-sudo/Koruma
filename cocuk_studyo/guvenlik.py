# -*- coding: utf-8 -*-
"""YouTube Kids / küçük çocuk uyum denetleyicisi.
1) Senaryo denetimi: yasaklı sözcük, bağlantı/@, çekim süresi, toplam süre, ses sığması.
2) Medya denetimi: çözünürlük/fps/süre, parlama (flash) analizi, ses seviyesi (LUFS / tepe)."""
import re, json, subprocess, sys
import numpy as np

BAN_TR = ["öldür", "kan ", "silah", "vur", "savaş", "korku", "canavar", "hayalet", "cadı", "ölüm", "ölü", "kavga", "dövüş", "kötü", "nefret", "aptal", "salak",
          "sigara", "alkol", "içki", "bomba", "kaza", "yara", "abone ol", "beğen", "satın al", "indirim", "reklam", "tıkla", "bağlantı", "bahis"]
BAN_EN = ["kill", "blood", "gun", "shoot", "war", "scary", "monster", "ghost", "witch", "death", "dead", "fight", "hate", "stupid", "idiot", "cigarette", "alcohol",
          "beer", "wine", "bomb", "crash", "wound", "subscribe", "like and", "buy now", "discount", "click here", "click on", "link in", "sponsor", "bet"]
BRANDS = ["youtube", "instagram", "tiktok", "facebook", "disney", "cocomelon", "pinkfong", "baby shark", "blippi", "masha", "marvel", "pokemon", "lego", "coca", "mcdonald"]

def lint(B, voice_ok=None):
    issues = []; shots = B["shots"]; total = 0.0
    for i, S in enumerate(shots):
        total += S["dur"]
        if S["dur"] > 2.0 + 1e-6: issues.append(f"çekim {i}: süre {S['dur']} > 2.0 sn")
        if S["dur"] < 0.9: issues.append(f"çekim {i}: çok kısa ({S['dur']})")
        for key in ("tr", "en", "say_tr", "say_en"):
            tx = (S.get(key) or "").lower()
            if not tx: continue
            if re.search(r"https?:|www\.|@|\.com|#", tx): issues.append(f"çekim {i}: bağlantı/etiket '{tx}'")
            hit = set()
            for w in (BAN_TR if key.endswith("tr") else BAN_EN):
                w2 = w.strip(); pat = r"(?<![\wçğıöşü])" + re.escape(w2) + (r"(?![\wçğıöşü])" if len(w2) <= 4 else "")
                if re.search(pat, tx) and w2 not in hit:
                    hit.add(w.strip()); issues.append(f"çekim {i}: yasaklı sözcük '{w.strip()}' → '{tx}'")
            for b in BRANDS:
                if b in tx: issues.append(f"çekim {i}: marka adı '{b}'")
        if S.get("say_tr") and len(S["say_tr"]) + len(S["say_en"]) > 60: issues.append(f"çekim {i}: söz çok uzun, hızlandırılır: '{S['say_tr']}'")
    if total < 900: issues.append(f"toplam süre {total:.1f} sn < 900 sn (15 dk)")
    return issues, total

def _decode_gray(path, w=32, h=18, fps=30):
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    buf = p.stdout.read(); p.wait()
    return np.frombuffer(buf, np.uint8).reshape(-1, h * w).astype(np.float32) / 255.0

def flash_analysis(path, fps=30):
    """WCAG/Harding 'general flash' yaklaşımı: bir saniye içinde >=%10'luk parlaklık değişimi çiftlerinin sayısı (<=3 olmalı)."""
    L = _decode_gray(path, fps=fps).mean(axis=1)
    d = np.diff(L); big = np.where(np.abs(d) >= 0.10)[0]
    worst = 0
    for i in big:
        win = [j for j in big if i <= j < i + fps]
        signs = [np.sign(d[j]) for j in win]
        pairs = sum(1 for a, b in zip(signs, signs[1:]) if a != b)
        worst = max(worst, (pairs + 1) // 2 if pairs else 0)
    # toplam hareket (ani kesme sıklığı)
    return dict(frames=len(L), big_transitions=int(len(big)), worst_flashes_per_sec=int(worst), max_step=float(np.abs(d).max()) if len(d) else 0.0, ok=worst <= 3)

def loudness(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    return dict(lufs=float(I[-1]) if I else None, true_peak=float(P[-1]) if P else None)

def probe(path):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,duration", "-show_entries", "format=duration,size", "-of", "json", path], capture_output=True, text=True).stdout)
    return j

def media_report(path):
    pr = probe(path); fl = flash_analysis(path); ld = loudness(path)
    v = [s for s in pr["streams"] if s.get("width")][0]
    dur = float(pr["format"]["duration"])
    rep = dict(width=v["width"], height=v["height"], fps=v["r_frame_rate"], duration_s=round(dur, 2), size_mb=round(int(pr["format"]["size"]) / 1e6, 1), flash=fl, loudness=ld)
    rep["ok"] = dict(res=v["height"] >= 1080, length=dur >= 900, flash=fl["ok"], lufs=(ld["lufs"] is not None and -23 <= ld["lufs"] <= -12), peak=(ld["true_peak"] is not None and ld["true_peak"] <= -1.0))
    return rep

if __name__ == "__main__":
    print(json.dumps(media_report(sys.argv[1]), indent=1))
