# -*- coding: utf-8 -*-
"""Üç videonun kurgusu. Her video: giriş + bölümler + tekrar kuşağı + kapanış, >= 15 dk."""
import icerik_ortak as O
from hikaye import (Maker, intro, outro, ep_count, ep_colors, ep_animals, ep_vehicles, ep_opposites, ep_shapes, ep_routine, ep_share,
                    ep_feelings, MIN_SEC, ALL)

COUNTS = {
    "stars": dict(cast=["luna", "pofi", "zuzu"], e="⭐", e2="🌟", tr="Kayıp Yıldızlar", en="The Lost Stars", themes=["space", "meadow", "forest", "beach", "candy", "snow"],
                  intro=[("luna", "Yıldızlarım düştü!", "My stars fell!"), ("pofi", "Biz bulalım!", "We will find them!"), ("zuzu", "Birlikte sayalım!", "Let's count together!")],
                  go=("Yıldız avına!", "Star hunt!"), tr1="yıldız", en1="a star", trn="yıldız", enp="stars", en_s="star",
                  song=[("Işıl ışıl yıldızlar!", "Sparkly, sparkly stars!"), ("Gökyüzüne dönün!", "Back to the sky!"), ("Bir iki üç, say!", "One, two, three, count!"), ("Yıldızlar yerinde!", "Stars in place!")],
                  end=[("luna", "Teşekkürler dostlar!", "Thank you, friends!"), ("pofi", "Hepsi yerinde!", "All in place!"), ("zuzu", "İyi geceler!", "Good night!")]),
    "apples": dict(cast=["bobo", "mimi", "dodo"], e="🍎", e2="🍏", tr="Elma Toplama Günü", en="Apple Picking Day", themes=["meadow", "forest", "candy", "beach"],
                   intro=[("bobo", "Elmalı pasta yapacağım!", "I will bake an apple pie!"), ("mimi", "Ben yardım ederim!", "I will help!"), ("dodo", "Sayarak toplayalım!", "Let's count as we pick!")],
                   go=("Elma toplamaya!", "Let's pick apples!"), tr1="elma", en1="an apple", trn="elma", enp="apples", en_s="apple",
                   song=[("Elma elma toplayalım!", "Pick, pick the apples!"), ("Sepet doldu doldu!", "The basket is full!"), ("Say say say say!", "Count, count, count!"), ("Pasta zamanı!", "Pie time!")],
                   end=[("bobo", "Teşekkürler dostlar!", "Thank you, friends!"), ("mimi", "Ne güzel pasta!", "What a lovely pie!"), ("dodo", "Hep birlikte yiyelim!", "Let's eat together!")]),
    "balloons": dict(cast=["dodo", "pofi", "mimi"], e="🎈", e2="🎁", tr="Uçan Balonlar", en="Flying Balloons", themes=["town", "candy", "meadow", "beach"],
                     intro=[("dodo", "Balonlarım uçtu!", "My balloons flew away!"), ("pofi", "Yakalayalım!", "Let's catch them!"), ("mimi", "Sayarak bulalım!", "Let's find them by counting!")],
                     go=("Balon avına!", "Balloon hunt!"), tr1="balon", en1="a balloon", trn="balon", enp="balloons", en_s="balloon",
                     song=[("Balon balon uç uç!", "Balloons, balloons, fly!"), ("Rengârenk balonlar!", "Colorful balloons!"), ("Bir iki üç, say!", "One, two, three, count!"), ("Hepsini bulduk!", "We found them all!")],
                     end=[("dodo", "Teşekkürler dostlar!", "Thank you, friends!"), ("pofi", "Ne güzel balonlar!", "What lovely balloons!"), ("mimi", "Hep birlikte uçuralım!", "Let's fly them together!")]),
}
SHARES = {
    "cookies": dict(e="🍪", tr="Paylaşmak Güzel", en="Sharing Is Fun", trn="kurabiye", enp="cookies", l1_tr="Kurabiye pişirdim!", l1_en="I baked cookies!"),
    "apples": dict(e="🍎", tr="Elmaları Paylaşalım", en="Let's Share the Apples", trn="elma", enp="apples", l1_tr="Elma topladım!", l1_en="I picked apples!"),
    "berries": dict(e="🍓", tr="Çilekleri Paylaşalım", en="Let's Share the Berries", trn="çilek", enp="strawberries", l1_tr="Çilek topladım!", l1_en="I picked strawberries!"),
}

SPECS = {
    1: dict(slug="1_say-boya-ogren", title_tr="Pofi ve Dostları: Say, Boya, Öğren!", title_en="Pofi and Friends: Count, Paint, Learn!",
            tag=("Say, boya, öğren!", "Count, paint, learn!"), cast=["pofi", "mimi", "dodo"],
            eps=[(ep_count, ("count", "stars")), (ep_colors, ((["mimi", "pofi", "dodo"], [0, 1]),)), (ep_animals, (["bobo", "mimi", "dodo"], O.FARM, ("Çiftlik Dostları", "Farm Friends"))),
                 (ep_shapes, (["zuzu", "pofi", "luna"], O.SHAPES)), (ep_share, (["bobo", "mimi", "dodo"], "cookies")),
                 (ep_opposites, (["pofi", "mimi", "zuzu"], O.OPPOSITES[0:7])), (ep_routine, (["pofi", "mimi", "dodo"],)), (ep_feelings, (["mimi", "bobo", "luna"],))]),
    2: dict(slug="2_hayvanlar-araclar-duygular", title_tr="Pofi ve Dostları: Hayvanlar, Araçlar ve Duygular", title_en="Pofi and Friends: Animals, Vehicles and Feelings",
            tag=("Hayvanlar ve araçlar!", "Animals and vehicles!"), cast=["pofi", "zuzu", "luna"],
            eps=[(ep_count, ("count", "apples")), (ep_vehicles, (["pofi", "zuzu", "luna"], O.VEHICLES[0:7])), (ep_animals, (["zuzu", "luna", "bobo"], O.WILD, ("Vahşi Doğa Dostları", "Wild Friends"))),
                 (ep_colors, ((["luna", "mimi", "zuzu"], [2, 3]), True)), (ep_feelings, (["pofi", "dodo", "mimi"],)), (ep_share, (["mimi", "pofi", "bobo"], "apples")),
                 (ep_shapes, (["mimi", "dodo", "pofi"], O.SHAPES)), (ep_opposites, (["dodo", "bobo", "luna"], O.OPPOSITES[7:14]))]),
    3: dict(slug="3_guzel-bir-gun", title_tr="Pofi ve Dostları: Güzel Bir Gün", title_en="Pofi and Friends: A Lovely Day",
            tag=("Güzel bir gün!", "A lovely day!"), cast=["pofi", "mimi", "luna"],
            eps=[(ep_count, ("count", "balloons")), (ep_routine, (["pofi", "mimi", "dodo"],)), (ep_animals, (["mimi", "zuzu", "pofi"], O.SEA, ("Deniz ve Gökyüzü Dostları", "Sea and Sky Friends"))),
                 (ep_shapes, (["bobo", "luna", "pofi"], O.SHAPES)), (ep_vehicles, (["dodo", "bobo", "luna"], O.VEHICLES[7:14])),
                 (ep_opposites, (["pofi", "luna", "zuzu"], O.OPPOSITES[3:10])), (ep_share, (["luna", "zuzu", "dodo"], "berries")),
                 (ep_colors, ((["pofi", "bobo", "mimi"], [1, 3]),))]),
}
BPMS = [120, 112, 126, 118, 124, 116, 128, 122]
KEYS = [0, 5, 7, 2, -2, 0, 5, 7]

def build(vid):
    spec = SPECS[vid]
    m = Maker(seed=vid * 7 + 3, bpm=120, themes=["meadow", "forest", "candy", "beach", "town"])
    segs = []
    def seg(i, name, fn, *a):
        s0 = len(m.shots); m.bpm = BPMS[i % 8]; fn(*a); segs.append(dict(idx=s0, bpm=m.bpm, key=KEYS[i % 8], prog=i % 3, seed=vid * 31 + i, name=name))
    seg(0, "Giriş", intro, m, spec["cast"], *spec["tag"])
    for i, (fn, args) in enumerate(spec["eps"], 1):
        if fn is ep_count: a = (m, COUNTS[args[1]])
        elif fn is ep_colors:
            cast_idx = args[0]; a = (m, cast_idx[0], cast_idx[1], *(args[1:]))
        elif fn is ep_share: a = (m, args[0], SHARES[args[1]])
        else: a = (m, *args)
        seg(i, fn.__name__, fn, *a)
    seg(9, "Tekrar", m.review, ALL)
    seg(10, "Kapanış", outro, m, spec["cast"])
    # zamanlar
    t = 0.0
    for S in m.shots: S["_t0"] = t; t += S["dur"]
    total = t
    bounds = [sg["idx"] for sg in segs] + [len(m.shots)]
    eps = []
    for k, sg in enumerate(segs):
        a, b = bounds[k], bounds[k + 1]; t0 = m.shots[a]["_t0"]; dur = sum(S["dur"] for S in m.shots[a:b])
        for S in m.shots[a:b]: S["_ep0"] = t0
        eps.append((t0, dur, sg["bpm"], sg["key"], sg["prog"], sg["seed"]))
    chapters = [(m.shots[idx]["_t0"], tr, en) for idx, tr, en in m.marks]
    chapters += [(m.shots[sg["idx"]]["_t0"], "Tekrar zamanı", "Review time") for sg in segs if sg["name"] == "Tekrar"]
    chapters.sort()
    return dict(id=vid, spec=spec, shots=m.shots, episodes=eps, chapters=chapters, total=total)
