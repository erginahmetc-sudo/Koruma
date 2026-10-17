# -*- coding: utf-8 -*-
"""Kullanım:
  python3 studyo.py uret <1|2|3|hepsi> [--test N]   # video üret
  python3 studyo.py kontrol <1|2|3|hepsi>           # uyum raporu
  python3 studyo.py onizleme <1|2|3|hepsi>          # 480p küçük önizleme"""
import os, sys, json, shutil, subprocess, time
from multiprocessing import Pool
import numpy as np
import cairocffi as cairo
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import videolar, ses, guvenlik
from dunya import W, H
from sahne import render_shot

FPS = ses.FPS
OUT = os.path.join(HERE, "cikti")

def render_chunk(job):
    cid, shots, outp = job
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(surf)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", str(FPS * 2), "-bf", "2", outp], stdin=subprocess.PIPE)
    for S in shots:
        nf = int(round(S["dur"] * FPS)); env = S["_env"]
        for fi in range(nf):
            t = fi / FPS; T = S["_t0"] - S["_ep0"] + t
            render_shot(ctx, S, t, T, float(env[min(fi, len(env) - 1)]) if len(env) else 0.0)
            surf.flush(); ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close(); ff.wait(); return cid

def uret(vid, test=0):
    t0 = time.time(); B = videolar.build(vid); shots = B["shots"][:test] if test else B["shots"]
    d = os.path.join(OUT, B["spec"]["slug"] + ("_test" if test else "")); os.makedirs(d, exist_ok=True)
    print(f"[{vid}] {len(shots)} çekim, {B['total'] / 60:.2f} dk — ses hazırlanıyor", flush=True)
    for S in shots:
        S["_voice"] = ses.voice_for(S); S["_env"] = ses.mouth_env(S["_voice"], S["dur"])
    pcm = ses.build_audio(shots, [e for e in B["episodes"] if e[0] < sum(s["dur"] for s in shots)])
    wav = os.path.join(d, "ses.wav"); ses.write_wav(wav, pcm)
    for S in shots: S.pop("_voice", None)
    # dengeli parçalara böl
    nchunk = 12; tot = sum(S["dur"] for S in shots); per = tot / nchunk; chunks = []; cur = []; acc = 0.0
    for S in shots:
        cur.append(S); acc += S["dur"]
        if acc >= per: chunks.append(cur); cur = []; acc = 0.0
    if cur: chunks.append(cur)
    jobs = [(i, c, os.path.join(d, f"parca_{i:02d}.mp4")) for i, c in enumerate(chunks)]
    print(f"[{vid}] render: {len(jobs)} parça, 4 işçi", flush=True)
    with Pool(4) as p:
        for k, cid in enumerate(p.imap_unordered(render_chunk, jobs), 1): print(f"[{vid}] parça {k}/{len(jobs)} bitti ({time.time() - t0:.0f} sn)", flush=True)
    lst = os.path.join(d, "liste.txt"); open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    vid_only = os.path.join(d, "goruntu.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid_only], check=True)
    final = os.path.join(d, B["spec"]["slug"] + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid_only, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-movflags", "+faststart", "-shortest", final], check=True)
    for j in jobs: os.remove(j[2])
    os.remove(vid_only); os.remove(lst)
    json.dump(dict(video=B["spec"]["title_tr"], chapters=[(round(t, 1), a, b) for t, a, b in B["chapters"]],
                   shots=[{k: v for k, v in S.items() if not k.startswith("_") and k not in ("chars", "props", "cam", "accent")} | {"start_s": round(S["_t0"], 2)} for S in shots]),
              open(os.path.join(d, "senaryo.json"), "w"), ensure_ascii=False, indent=1)
    print(f"[{vid}] TAMAM → {final}  ({time.time() - t0:.0f} sn)", flush=True)

def kontrol(vid):
    B = videolar.build(vid)
    for S in B["shots"]: S["_voice"] = ses.voice_for(S)
    issues, total = guvenlik.lint(B)
    for i, S in enumerate(B["shots"]):
        v = S.get("_voice")
        if v is not None and len(v) / ses.SR > S["dur"] - ses.VOICE_START: issues.append(f"çekim {i}: ses sığmıyor")
    d = os.path.join(OUT, B["spec"]["slug"]); final = os.path.join(d, B["spec"]["slug"] + ".mp4")
    rep = dict(senaryo_sorunlari=issues, toplam_sn=round(total, 1), cekim_sayisi=len(B["shots"]))
    if os.path.exists(final): rep["medya"] = guvenlik.media_report(final)
    md = [f"# Uyum raporu — {B['spec']['title_tr']}", "", f"- Çekim sayısı: **{rep['cekim_sayisi']}**, süre: **{total / 60:.2f} dk**, en uzun çekim: **{max(S['dur'] for S in B['shots'])} sn**",
          f"- Senaryo sorunları: **{len(issues)}**"] + [f"  - {x}" for x in issues[:40]]
    if "medya" in rep:
        m = rep["medya"]
        md += ["", "## Medya", f"- Çözünürlük: {m['width']}x{m['height']} @ {m['fps']}, süre {m['duration_s']} sn, boyut {m['size_mb']} MB",
               f"- Parlama analizi: en kötü saniyede {m['flash']['worst_flashes_per_sec']} parlama (sınır 3), büyük geçiş sayısı {m['flash']['big_transitions']} → {'GEÇTİ' if m['flash']['ok'] else 'KALDI'}",
               f"- Ses: {m['loudness']['lufs']} LUFS, tepe {m['loudness']['true_peak']} dBFS", f"- Kontroller: {m['ok']}"]
    open(os.path.join(d if os.path.isdir(d) else OUT, "uyum_raporu.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md)); return rep

def onizleme(vid):
    B = videolar.build(vid); d = os.path.join(OUT, B["spec"]["slug"]); src = os.path.join(d, B["spec"]["slug"] + ".mp4")
    dst = os.path.join(d, B["spec"]["slug"] + "_480p.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", "scale=854:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-c:a", "aac", "-b:a", "64k", "-ac", "1", dst], check=True)
    print(dst, os.path.getsize(dst) // 1e6, "MB")

if __name__ == "__main__":
    cmd = sys.argv[1]; which = sys.argv[2] if len(sys.argv) > 2 else "hepsi"; ids = [1, 2, 3] if which == "hepsi" else [int(which)]
    test = int(sys.argv[sys.argv.index("--test") + 1]) if "--test" in sys.argv else 0
    for v in ids:
        {"uret": lambda: uret(v, test), "kontrol": lambda: kontrol(v), "onizleme": lambda: onizleme(v)}[cmd]()
