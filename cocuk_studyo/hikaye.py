# -*- coding: utf-8 -*-
"""Özgün senaryolar: 'Pofi ve Dostları' (Baloncuk Vadisi). Üç video, her biri >= 15 dakika.
Hiçbir mevcut video/şarkı/karakter kopyalanmaz; yalnızca tür düzeyindeki ilkeler (kısa, tekrarlı, renkli, öğretici) kullanılır.
Her çekim en fazla 2 sn; sözler kısa tutulur (önce Türkçe sonra İngilizce)."""
import random

MIN_SEC = 905.0
PASTEL = [(.40, .78, .95), (.98, .62, .75), (.60, .85, .55), (1.0, .78, .35), (.72, .62, .98), (.45, .85, .80), (1.0, .60, .45)]
CAMS = [(1.0, 1.10, 0, 0), (1.12, 1.0, 0, 0), (1.05, 1.05, -70, 70), (1.05, 1.05, 70, -70), (1.0, 1.14, 0, 0), (1.08, 1.0, 40, -40)]
ALL = ["pofi", "mimi", "dodo", "zuzu", "bobo", "luna"]
NUM_TR = "bir iki üç dört beş altı yedi sekiz dokuz on on-bir on-iki on-üç on-dört on-beş on-altı on-yedi on-sekiz on-dokuz yirmi".replace("-", " ").split(" ")
NUM_TR = ["bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz", "on", "on bir", "on iki", "on üç", "on dört", "on beş", "on altı", "on yedi", "on sekiz", "on dokuz", "yirmi"]
NUM_EN = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
cap = lambda s: s[:1].upper() + s[1:] if not s.startswith("i") else "İ" + s[1:]
def tcap(s): return ("İ" + s[1:]) if s[:1] == "i" else s[:1].upper() + s[1:]

GO = [("Hadi gidelim!", "Let's go!"), ("Yola çıkalım!", "Off we go!"), ("Koşalım!", "Let's run!"), ("Haydi dostlar!", "Come on, friends!"), ("İleri!", "Forward!"), ("Beni takip edin!", "Follow me!")]
WOW = [("Vay canına!", "Wow!"), ("Harika!", "Great!"), ("Çok güzel!", "So pretty!"), ("Yaşasın!", "Hooray!"), ("Süper!", "Super!"), ("Bravo!", "Well done!")]

class Maker:
    def __init__(s, seed, bpm, themes):
        s.r = random.Random(seed); s.bpm = bpm; s.themes = themes; s.ti = 0; s.shots = []; s.seed = seed * 1000; s.learned = []; s.marks = []

    def theme(s, bg=None):
        if bg: return bg
        s.ti += 1; return s.themes[s.ti % len(s.themes)]

    def layout(s, n):
        return {1: [640], 2: [520, 1400], 3: [380, 960, 1540]}.get(n) or [300 + i * (1320 / (n - 1)) for i in range(n)]

    def add(s, tr=None, en=None, chars=(), speaker=None, props=None, dur=2.0, bg=None, mood="happy", pose=None, sfx=None, say=True,
            say_tr=None, say_en=None, xs=None, color=None, big=None, count=None, count_e=None, cam=None, cs=None):
        assert dur <= 2.0
        chars = list(chars); n = len(chars); xs = xs or s.layout(max(n, 1)); sc = cs or (1.12 if n <= 3 else .86)
        cl = []
        for i, c in enumerate(chars):
            cl.append(dict(id=c, x=xs[i], flip=(xs[i] > 960 and n > 1), pose=pose or ("dance" if mood == "cheer" else "idle"), mood=mood, s=sc, seed=i + 1))
        ps = []
        for i, p in enumerate(props or []):
            if isinstance(p, dict): ps.append(dict(p)); continue
            e, anim = p[0], p[1] if len(p) > 1 else "pop"
            k = len(props)
            x = (1300 if n <= 1 else 960) if k == 1 else (780 + i * 360 if n <= 1 else 560 + i * 800 if k == 2 else 400 + i * 560)
            y = 380 if n <= 1 else 300
            d = dict(x=x, y=y, size=410 if n <= 1 and k == 1 else 340 if k == 1 else 260, anim=anim, ph=i * .4, delay=.12 + .08 * i)
            if e.startswith("shape:"): d["shape"] = e[6:]
            else: d["e"] = e
            ps.append(d)
        if speaker is None and say and tr and n: speaker = chars[0]
        S = dict(dur=dur, bg=s.theme(bg), seed=s.seed, color=color, accent=PASTEL[s.seed % len(PASTEL)], bpm=s.bpm, speaker=speaker if say else None,
                 chars=cl, props=ps, tr=tr, en=en, cam=cam or CAMS[s.r.randrange(len(CAMS))], sfx=sfx, big=big, count=count, count_e=count_e,
                 say_tr=(say_tr or tr) if (say and tr) else None, say_en=(say_en or en) if (say and tr) else None)
        s.seed += 1; s.shots.append(S); return S

    def title(s, tr, en, cast, bg="meadow"):
        s.marks.append((len(s.shots), tr, en))
        s.add(tr, en, cast, speaker=cast[0], mood="cheer", pose="dance", bg=bg, props=[("🎉", "float")], sfx="tada",
              say_tr=tr, say_en=en)

    def dance(s, cast, tr, en, bg=None, dur=2.0):
        return s.add(tr, en, cast, speaker=cast[0], mood="cheer", pose="dance", bg=bg, props=[("🎵", "float"), ("🎶", "float")] if len(cast) < 4 else [("🎵", "float")])

    def count(s, n, e, tr, en, who, bg=None):
        return s.add(tr, en, [who], bg=bg, mood="cheer", pose="cheer", xs=[330], big=str(n), count=n, count_e=e, sfx="ding", speaker=who)

    def bignum(s, txt, tr, en, e, who, bg=None, dur=1.6):
        return s.add(tr, en, [who], bg=bg, mood="cheer", pose="cheer", xs=[400], big=txt, props=[dict(e=e, x=1280, y=380, size=380, anim="bounce", delay=.1)], dur=dur, speaker=who)

    def react(s, cast, sfx=None, e="🎉", dur=1.2):
        return s.add(None, None, cast, mood="cheer", pose="cheer", props=[(e, "float")], dur=dur, sfx=sfx, say=False)

    def review(s, who_pool):
        items = s.learned[:]; s.r.shuffle(items)
        s.add("Tekrar zamanı!", "Review time!", who_pool[:3], mood="cheer", pose="dance", props=[("🔁", "spin")], bg="candy")
        t = sum(x["dur"] for x in s.shots); i = 0
        while t < MIN_SEC - 14 and items:
            it = items[i % len(items)]; i += 1
            who = s.r.choice(who_pool); o = s.r.choice([w for w in who_pool if w != who])
            sh = s.add(it["tr"], it["en"], [who, o], speaker=who, props=[it["prop"]], mood="wow", dur=1.6, bg=it.get("bg"), color=it.get("color"))
            t += 1.6
            if i % len(items) == 0: s.r.shuffle(items)

    def learn(s, prop, tr, en, bg=None, color=None):
        s.learned.append(dict(prop=prop, tr=tr, en=en, bg=bg, color=color))

# ---------------------------------------------------------------- bölümler
def intro(m, cast, tr, en):
    m.marks.append((len(m.shots), "Giriş", "Intro"))
    m.add("Pofi ve Dostları", "Pofi and Friends", ALL, speaker="pofi", mood="cheer", pose="dance", bg="meadow", props=[("🌈", "float")], sfx="tada", cam=(1.0, 1.06, 0, 0))
    m.add("Merhaba dostlar!", "Hello, friends!", ["pofi", "mimi"], speaker="pofi", pose="wave", bg="meadow")
    m.add("Ben Pofi!", "I am Pofi!", ["pofi"], mood="wow", bg="meadow", props=[("🫧", "float")])
    m.add("Bugün neler var?", "What's today?", ["mimi", "dodo"], speaker="mimi", bg="candy")
    m.add(tr, en, cast, speaker=cast[0], mood="cheer", pose="dance", bg="meadow", props=[("🎉", "float")])

def outro(m, cast):
    m.marks.append((len(m.shots), "Güle güle", "Bye bye"))
    m.add("Hepsini öğrendik!", "We learned it all!", ALL, speaker="pofi", mood="cheer", pose="dance", bg="meadow", props=[("🎉", "float")], sfx="tada")
    m.add("Çok eğlendik!", "That was fun!", cast[:3], speaker=cast[0], mood="cheer", bg="candy")
    m.add("Seni seviyoruz!", "We love you!", ["pofi", "mimi", "bobo"], speaker="mimi", props=[("❤️", "bounce")], bg="meadow")
    m.add("Tekrar görüşürüz!", "See you soon!", ALL, speaker="pofi", pose="wave", bg="meadow")
    m.add("Güle güle!", "Bye bye!", ALL, speaker="luna", pose="wave", bg="meadow", props=[("👋", "wiggle")])

def ep_count(m, c):
    cast = c["cast"]; e = c["e"]
    m.title(c["tr"], c["en"], cast, bg=c["themes"][0])
    for spk, tr, en in c["intro"]:
        o = [x for x in cast if x != spk][0]; m.add(tr, en, [spk, o], speaker=spk, bg=c["themes"][0], mood="wow" if "!" in tr else "happy")
    m.dance(cast, *c["go"], bg=c["themes"][0])
    for n in range(1, 11):
        who = m.r.choice(cast); o = m.r.choice([x for x in cast if x != who]); tr, en = m.r.choice(GO)
        bg = c["themes"][n % len(c["themes"])]
        m.add(tr, en, [who, o], speaker=who, bg=bg, pose="dance")
        m.add(f"Bak, {c['tr1']}!", f"Look, {c['en1']}!", [who], bg=bg, props=[(e, "bounce")], mood="wow", sfx="boing")
        ntr, nen = NUM_TR[n - 1], NUM_EN[n - 1]
        m.count(n, e, tcap(f"{ntr} {c['trn']}"), f"{tcap(nen)} {c['enp'] if n > 1 else c['en_s']}", who, bg=bg)
        m.react([who, o], sfx="tada" if n % 5 == 0 else None, e=m.r.choice(["🎉", "✨", "🎈"]))
        m.learn((e, "bounce"), tcap(f"{ntr} {c['trn']}"), f"{tcap(nen)} {c['enp'] if n > 1 else c['en_s']}", bg=bg)
    m.add("Şimdi geri sayım!", "Now, a countdown!", [cast[0], cast[1]], speaker=cast[0], bg="space", mood="wow", props=[("🚀", "bounce")])
    for i in range(10, 0, -1):
        m.bignum(str(i), tcap(NUM_TR[i - 1]), tcap(NUM_EN[i - 1]), "🚀", cast[i % len(cast)], bg="space")
    m.bignum("🚀", "Fırla!", "Blast off!", "🚀", cast[0], bg="space", dur=2.0).update(sfx="tada")
    for n in range(11, 21):
        m.count(n, c["e2"], tcap(NUM_TR[n - 1]), tcap(NUM_EN[n - 1]), cast[n % len(cast)], bg=c["themes"][n % len(c["themes"])])
    for tr, en in c["song"] * 2:
        m.dance(cast, tr, en, bg=c["themes"][1])
    for spk, tr, en in c["end"]:
        o = [x for x in cast if x != spk][0]; m.add(tr, en, [spk, o], speaker=spk, bg=c["themes"][0], mood="cheer", props=[("🎉", "float")])

def ep_colors(m, cast, objs_idx, rev=False):
    from icerik_ortak import COLORS, MIX
    m.title("Sihirli Fırça", "The Magic Brush", cast[:3], bg="candy")
    m.add("Bir fırça buldum!", "I found a brush!", [cast[0], cast[1]], speaker=cast[0], props=[("🖌️", "wiggle")], mood="wow", bg="candy")
    m.add("Sihirli fırça!", "A magic brush!", [cast[1], cast[2]], speaker=cast[1], props=[("✨", "float")], mood="wow", bg="candy")
    keys = list(COLORS.keys()); keys = keys[::-1] if rev else keys
    for k, key in enumerate(keys):
        ctr, cen, hx, objs = COLORS[key]; who = cast[k % len(cast)]; o = cast[(k + 1) % len(cast)]
        m.add(f"{ctr} fırça!", f"{cen} brush!", [who], speaker=who, props=[("🖌️", "wiggle")], bg="color", color=hx, mood="cheer", pose="dance")
        for oi in objs_idx:
            e, otr, oen = objs[oi]
            m.add(f"{ctr} {otr}", f"{cen} {oen}", [who if oi == objs_idx[0] else o], props=[(e, "bounce")], bg="color", color=hx, mood="wow", sfx="boing")
            m.learn((e, "bounce"), f"{ctr} {otr}", f"{cen} {oen}", bg="color", color=hx)
        m.react([who, o], e="🎨")
    m.add("Renkleri karıştıralım!", "Let's mix colors!", [cast[0], cast[2]], speaker=cast[0], props=[("🎨", "wiggle")], mood="wow", bg="candy")
    for (a, atr, aen), (b, btr, ben), (c_, ctr, cen) in MIX:
        m.add(f"{atr} artı {btr}", f"{aen} plus {ben}", [cast[0], cast[1]], props=[(a, "pop"), (b, "pop")], bg="candy")
        m.add(f"{ctr}!", f"{cen}!", [cast[2]], props=[(c_, "bounce")], mood="cheer", sfx="tada", bg="candy")
    m.add("Gökkuşağı zamanı!", "Rainbow time!", cast[:3], speaker=cast[0], mood="cheer", pose="dance", props=[("🌈", "float")], bg="candy")
    for tr, en, hx in [("Kırmızı", "Red", "#E53935"), ("Turuncu", "Orange", "#FB8C00"), ("Sarı", "Yellow", "#FDD835"), ("Yeşil", "Green", "#43A047"),
                       ("Mavi", "Blue", "#1E88E5"), ("Lacivert", "Indigo", "#3949AB"), ("Mor", "Violet", "#8E24AA")]:
        m.add(tr, en, cast[:3], speaker=cast[m.r.randrange(3)], mood="cheer", pose="dance", bg="color", color=hx, dur=1.6)
    for tr, en in [("Renkli dünya!", "Colorful world!"), ("Hepimiz renkliyiz!", "We are all colorful!"), ("Boyayalım, boyayalım!", "Let's paint, let's paint!"), ("Tralala renkler!", "Tra-la-la colors!")] * 2:
        m.dance(cast[:3], tr, en, bg="candy")

def ep_animals(m, cast, animals, title):
    m.title(title[0], title[1], cast[:3], bg=animals[0][5])
    m.add("Kapıda biri var!", "Someone is at the door!", [cast[0], cast[1]], speaker=cast[0], mood="wow", bg=animals[0][5], props=[("🚪", "wiggle")])
    for k, (e, tr, en, str_, sen, bg) in enumerate(animals):
        who = cast[k % len(cast)]; o = cast[(k + 1) % len(cast)]
        m.add("Tak tak! Kim o?", "Knock knock! Who is it?", [who], speaker=who, props=[("🚪", "wiggle")], bg=bg, mood="wow")
        m.add(f"{tr}!", f"{en}!", [who, o], speaker=who, props=[(e, "bounce")], bg=bg, mood="wow", sfx="boing")
        m.add(str_, sen, [o], speaker=o, props=[dict(e=e, x=1280, y=380, size=420, anim="wiggle", delay=.1), dict(e="🔊", x=1600, y=250, size=150, anim="float", delay=.3)], bg=bg, mood="cheer")
        m.react([who, o], e="🎶")
        m.learn((e, "wiggle"), f"{tr}: {str_}", f"{en}: {sen}", bg=bg)
    m.add("Hep birlikte dans!", "Dance all together!", cast[:3], speaker=cast[0], mood="cheer", pose="dance", bg=animals[1][5])
    for k in range(len(animals)):
        e, tr, en, str_, sen, bg = animals[k]
        m.add(str_, sen, [cast[k % len(cast)]], speaker=cast[k % len(cast)], props=[(e, "bounce")], bg=bg, mood="cheer", pose="dance", dur=1.6)
    for tr, en in [("Hayvanlar, hayvanlar!", "Animals, animals!"), ("Hep beraber şarkı!", "Sing along together!"), ("Tıpış tıpış gel!", "Come, come, come!"), ("Dans edelim!", "Let's dance!")] * 2:
        m.dance(cast[:3], tr, en, bg=animals[2][5])

def ep_vehicles(m, cast, items):
    m.title("Yardımcı Araçlar", "Helper Vehicles", cast[:3], bg="town")
    m.add("Bugün yardıma çıkıyoruz!", "Today we help out!", [cast[0], cast[1]], speaker=cast[0], mood="wow", bg="town")
    for k, (e, tr, en, str_, sen, bg, ttr, ten) in enumerate(items):
        who = cast[k % len(cast)]; o = cast[(k + 1) % len(cast)]
        m.add(ttr, ten, [who, o], speaker=who, bg=bg)
        m.add(f"{tr} geldi!", f"Here comes the {en.lower()}!", [o], speaker=o, props=[dict(e=e, x=1280, y=420, size=430, anim="slide", delay=.05)], bg=bg, mood="wow")
        m.add(str_, sen, [who], speaker=who, props=[(e, "wiggle")], bg=bg, mood="cheer", sfx="boing")
        m.add("Teşekkürler!", "Thank you!", [who, o], speaker=o, bg=bg, mood="cheer", props=[("❤️", "float")], dur=1.6)
        m.learn((e, "bounce"), f"{tr}: {str_}", f"{en}: {sen}", bg=bg)
    for k, (e, tr, en, str_, sen, bg, *_r) in enumerate(items):
        m.add(tr + "!", en + "!", [cast[k % len(cast)]], props=[dict(e=e, x=1280, y=420, size=420, anim="slide", delay=.05)], bg=bg, mood="cheer", dur=1.6)
    for tr, en in [("Vın vın yola!", "Vroom, vroom, go!"), ("Hep birlikte yardım!", "Helping together!"), ("Bip bip bip!", "Beep, beep, beep!"), ("Hadi hadi hadi!", "Come on, come on!")] * 2:
        m.dance(cast[:3], tr, en, bg="town")

def ep_opposites(m, cast, pairs):
    m.title("Zıt Kelimeler", "Opposites", cast[:3], bg="meadow")
    m.add("Zıtları öğrenelim!", "Let's learn opposites!", [cast[0], cast[1]], speaker=cast[0], mood="wow", bg="meadow")
    for k, ((e1, t1, n1), (e2, t2, n2)) in enumerate(pairs):
        who = cast[k % len(cast)]; o = cast[(k + 1) % len(cast)]
        m.add(f"{t1}!", f"{n1}!", [who], speaker=who, props=[(e1, "bounce")], mood="wow", sfx="boing")
        m.add(f"{t2}!", f"{n2}!", [o], speaker=o, props=[(e2, "bounce")], mood="wow", sfx="boing")
        m.add(f"{t1} ↔ {t2}", f"{n1} ↔ {n2}", [who, o], speaker=who, props=[dict(e=e1, x=720, y=300, size=300, anim="float"), dict(e=e2, x=1200, y=300, size=300, anim="float", ph=1)], mood="cheer", pose="dance")
        m.react([who, o], e="✨")
        m.learn((e1, "bounce"), f"{t1}!", f"{n1}!"); m.learn((e2, "bounce"), f"{t2}!", f"{n2}!")
    for tr, en in [("Zıtlar, zıtlar!", "Opposites, opposites!"), ("Büyük küçük, sıcak soğuk!", "Big small, hot cold!"), ("Hep beraber söyle!", "Say it together!")] * 2:
        m.dance(cast[:3], tr, en, bg="candy")

def ep_shapes(m, cast, shapes):
    m.title("Şekil Geçit Töreni", "Shape Parade", cast[:3], bg="candy")
    m.add("Şekiller geliyor!", "Shapes are coming!", [cast[0], cast[1]], speaker=cast[0], mood="wow", bg="candy")
    for k, (sh, tr, en, obj, otr, oen) in enumerate(shapes):
        who = cast[k % len(cast)]; o = cast[(k + 1) % len(cast)]
        m.add(f"{tr}!", f"{en}!", [who], speaker=who, props=[("shape:" + sh, "bounce")], mood="wow", sfx="boing", bg="candy")
        m.add(f"{otr}: {tr}", f"{oen}: {en}", [o], speaker=o, props=[(obj, "bounce")], bg="meadow")
        m.add(f"{tr}, {tr.lower()}!" if tr[0] != "İ" else f"{tr}!", f"{en}, {en.lower()}!", [who, o], speaker=who, props=[("shape:" + sh, "spin")], mood="cheer", pose="dance", bg="candy")
        m.react([who, o], e="✨")
        m.learn(("shape:" + sh, "spin"), f"{tr}!", f"{en}!", bg="candy")
    for k, (sh, tr, en, *_r) in enumerate(shapes):
        m.add(f"{tr}!", f"{en}!", [cast[k % len(cast)]], props=[("shape:" + sh, "bounce")], mood="cheer", pose="dance", bg="candy", dur=1.6)
    for tr, en in [("Şekil şekil geç!", "Shapes, shapes, parade!"), ("Yuvarlak, köşeli!", "Round and pointy!"), ("Hep birlikte!", "All together!")] * 2:
        m.dance(cast[:3], tr, en, bg="candy")

def ep_routine(m, cast):
    P, M, D = cast[0], cast[1], cast[2]
    m.title("Güzel Bir Gün", "A Lovely Day", cast[:3], bg="room")
    A = m.add
    A("Günaydın!", "Good morning!", [P], props=[("☀️", "float")], bg="room", mood="happy")
    A("Zzz...", "Zzz...", [M], props=[("😴", "float")], mood="sleepy", bg="room", say=False)
    A("Kalk, esne!", "Wake up, stretch!", [P, M], speaker=P, bg="room", pose="wave")
    A("Ellerimizi yıkayalım!", "Let's wash our hands!", [M, D], speaker=M, props=[("🧼", "wiggle")], bg="room")
    m.count(5, "🫧", "Beş köpük", "Five bubbles", M, bg="room")
    A("Tertemiz!", "All clean!", [M, D], speaker=D, mood="cheer", props=[("✨", "float")], bg="room", sfx="tada")
    A("Dişlerimizi fırçalayalım!", "Let's brush our teeth!", [D, P], speaker=D, props=[("🪥", "wiggle")], bg="room")
    m.count(10, "🦷", "On kez fırçala", "Brush ten times", D, bg="room")
    A("Parlak dişler!", "Shiny teeth!", [D, P], speaker=P, mood="cheer", props=[("🦷", "bounce")], bg="room", sfx="tada")
    A("Kahvaltı zamanı!", "Breakfast time!", [P, M, D], speaker=P, bg="room", mood="wow")
    for e, tr, en in [("🍎", "Elma", "Apple"), ("🍌", "Muz", "Banana"), ("🥛", "Süt", "Milk"), ("🍞", "Ekmek", "Bread"), ("🥚", "Yumurta", "Egg"), ("🧀", "Peynir", "Cheese")]:
        A(f"{tr}!", f"{en}!", [cast[m.r.randrange(3)]], props=[(e, "bounce")], bg="room", mood="wow", dur=1.7); m.learn((e, "bounce"), f"{tr}!", f"{en}!", bg="room")
    A("Afiyet olsun!", "Enjoy your meal!", [P, M, D], speaker=M, mood="cheer", pose="dance", bg="room", sfx="tada")
    A("Oyun vakti!", "Playtime!", [P, M], speaker=P, mood="cheer", pose="dance", bg="meadow", props=[("🧸", "bounce")])
    for e, tr, en in [("⚽", "Top", "Ball"), ("🧸", "Ayıcık", "Teddy bear"), ("🧱", "Bloklar", "Blocks"), ("🎨", "Boya", "Paint"), ("🪁", "Uçurtma", "Kite"), ("🚲", "Bisiklet", "Bicycle")]:
        A(f"{tr}!", f"{en}!", [cast[m.r.randrange(3)]], props=[(e, "bounce")], bg="meadow", mood="wow", dur=1.7); m.learn((e, "bounce"), f"{tr}!", f"{en}!", bg="meadow")
    A("Oyuncakları toplayalım!", "Let's tidy up!", [D, P], speaker=D, bg="room", props=[("🧺", "wiggle")])
    m.count(5, "🧸", "Beş oyuncak", "Five toys", D, bg="room")
    A("Her şey yerinde!", "Everything is in place!", [D, P, M], speaker=P, mood="cheer", bg="room", sfx="tada")
    A("Banyo zamanı!", "Bath time!", [M, P], speaker=M, props=[("🛁", "bounce")], bg="room")
    A("Köpük köpük!", "Bubbles, bubbles!", [M, P], speaker=P, props=[("🫧", "float"), ("🫧", "float")], mood="cheer", bg="room")
    A("Uyku zamanı!", "Sleepy time!", [P, M, D], speaker=P, props=[("🌙", "float")], bg="space", mood="sleepy")
    A("İyi geceler!", "Good night!", [P, M, D], speaker=M, props=[("⭐", "float")], bg="space", mood="sleepy")
    for tr, en in [("Güzel bir gün!", "A lovely day!"), ("Yıka, fırçala, oyna!", "Wash, brush, play!"), ("Her gün böyle!", "Every day like this!"), ("Hep birlikte!", "All together!")] * 2:
        m.dance([P, M, D], tr, en, bg="meadow")

DAT = {"pofi": "Pofi'ye", "mimi": "Mimi'ye", "dodo": "Dodo'ya", "zuzu": "Zuzu'ya", "bobo": "Bobo'ya", "luna": "Luna'ya"}

def ep_share(m, cast, c):
    B, M, Dd = cast[0], cast[1], cast[2]; e = c["e"]; nB, nM, nD = CHAR_TR[B], CHAR_TR[M], CHAR_TR[Dd]
    m.title(c["tr"], c["en"], cast[:3], bg="meadow")
    m.add(c["l1_tr"], c["l1_en"], [B], props=[(e, "bounce")], mood="cheer", bg="meadow")
    m.count(6, e, f"Altı {c['trn']}", f"Six {c['enp']}", B, bg="meadow")
    m.add(f"Merhaba, {nB}!", f"Hello, {nB}!", [B, M], speaker=M, pose="wave", bg="meadow")
    m.add("Çok güzel kokuyor!", "Smells so good!", [B, M], speaker=M, mood="wow", props=[(e, "float")], bg="meadow")
    m.add("Hadi paylaşalım!", "Let's share!", [B, M], speaker=B, mood="cheer", bg="meadow")
    m.add(f"Sen de gel, {nD}!", f"You come too, {nD}!", [B, Dd], speaker=B, bg="meadow", pose="wave")
    m.add("Ben de isterim!", "Me too, please!", [B, Dd], speaker=Dd, mood="wow", bg="meadow")
    for (who, tr, en) in [(M, f"{DAT[M]} iki", f"Two for {nM}"), (Dd, f"{DAT[Dd]} iki", f"Two for {nD}"), (B, "Bana iki", "Two for me")]:
        m.count(2, e, tr, en, B, bg="meadow")
        m.add("Teşekkürler!", "Thank you!", [B, who], speaker=who, mood="cheer", props=[("❤️", "float")], bg="meadow")
    m.add("Hepimizde iki!", "Two each!", [B, M, Dd], speaker=B, mood="cheer", pose="dance", bg="meadow", sfx="tada")
    m.add("Paylaşınca daha güzel!", "Sharing is better!", [B, M, Dd], speaker=M, mood="cheer", pose="dance", bg="candy", props=[("❤️", "bounce")])
    m.add("Ye, ye, ye!", "Yum, yum, yum!", [B, M, Dd], speaker=Dd, mood="cheer", bg="meadow", props=[(e, "bounce")])
    for tr, en in [("Paylaşmak güzel!", "Sharing is nice!"), ("Birlikte yiyelim!", "Let's eat together!"), ("Sen de bana ver!", "Give some to me!"), ("Hep beraber!", "All together!")] * 2:
        m.dance(cast[:3], tr, en, bg="candy")

CHAR_TR = {"pofi": "Pofi", "mimi": "Mimi", "dodo": "Dodo", "zuzu": "Zuzu", "bobo": "Bobo", "luna": "Luna"}

def ep_feelings(m, cast):
    m.title("Duygularımız", "Our Feelings", cast[:3], bg="meadow")
    m.add("Bugün nasılsın?", "How are you today?", [cast[0], cast[1]], speaker=cast[0], mood="wow", bg="meadow")
    F = [("😀", "Mutluyum!", "I am happy!", "happy", None), ("😢", "Üzgünüm.", "I am sad.", "sad", ("Sarılalım!", "Let's hug!")),
         ("😮", "Şaşırdım!", "I am surprised!", "wow", None), ("😴", "Uykum geldi.", "I am sleepy.", "sleepy", ("İyi uykular!", "Sleep well!")),
         ("🥰", "Seviyorum!", "I love you!", "cheer", None), ("😂", "Çok komik!", "So funny!", "cheer", None),
         ("🥶", "Üşüdüm!", "I am cold!", "sad", ("Battaniye getir!", "Bring a blanket!")), ("🤩", "Heyecanlıyım!", "I am excited!", "cheer", None)]
    for k, (e, tr, en, mood, help_) in enumerate(F):
        who = cast[k % len(cast)]; o = cast[(k + 1) % len(cast)]
        m.add(tr, en, [who], speaker=who, props=[(e, "bounce")], mood=mood, bg="meadow" if mood != "sleepy" else "space")
        if help_:
            m.add(help_[0], help_[1], [o, who], speaker=o, mood="happy", bg="meadow", props=[("🤗", "float")])
            m.add("Teşekkürler!", "Thank you!", [who, o], speaker=who, mood="cheer", bg="meadow", props=[("❤️", "float")], sfx="tada")
        else:
            m.add(tr, en, [who, o], speaker=o, mood=mood, pose="dance", bg="candy", props=[(e, "float")], dur=1.8)
            m.react([who, o], e="✨")
        m.learn((e, "bounce"), tr, en, bg="meadow")
    for tr, en in [("Her duygu güzel!", "Every feeling is okay!"), ("Gül, sarıl, paylaş!", "Smile, hug, share!"), ("Hep birlikte!", "All together!")] * 2:
        m.dance(cast[:3], tr, en, bg="candy")
