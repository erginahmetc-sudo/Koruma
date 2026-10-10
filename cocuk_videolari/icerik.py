# -*- coding: utf-8 -*-
"""3 videonun senaryosu. Her video 300 sahne x 2.0 sn = 10:00 dk.
Sahne: dict(tpl, em, tr, en, say_tr, say_en, n, big)."""
import random

TARGET = 300

def S(tpl, em, tr, en, say_tr=None, say_en=None, **k):
    d = dict(tpl=tpl, em=em, tr=tr, en=en, say_tr=say_tr or tr, say_en=say_en or en)
    d.update(k)
    return d

def fill(scenes, pool, outro, seed):
    """Havuzdaki sahneleri sirayla/karistirarak farkli sablonlarla tekrar eder (tekrar = ogrenme)."""
    rnd = random.Random(seed)
    tpls = ["trio", "spin", "single"]
    r = 0
    while len(scenes) < TARGET - len(outro):
        items = pool[:]
        rnd.shuffle(items)
        for it in items:
            if len(scenes) >= TARGET - len(outro):
                break
            c = dict(it)
            if c["tpl"] in ("single", "trio", "spin", "color"):
                c["tpl"] = tpls[r % 3] if c["tpl"] != "color" else ("color" if r % 2 == 0 else "spin")
            scenes.append(c)
        r += 1
    return scenes[:TARGET - len(outro)] + outro

# ---------------------------------------------------------------- VIDEO 1
NUM_TR = "bir iki üç dört beş altı yedi sekiz dokuz on on-bir on-iki on-üç on-dört on-beş on-altı on-yedi on-sekiz on-dokuz yirmi".split()
NUM_EN = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
TENS = [("otuz", "thirty", 30), ("kırk", "forty", 40), ("elli", "fifty", 50), ("altmış", "sixty", 60),
        ("yetmiş", "seventy", 70), ("seksen", "eighty", 80), ("doksan", "ninety", 90), ("yüz", "one hundred", 100)]
ORD = [("birinci", "first", "🥇"), ("ikinci", "second", "🥈"), ("üçüncü", "third", "🥉"), ("dördüncü", "fourth", "4️⃣"),
       ("beşinci", "fifth", "5️⃣"), ("altıncı", "sixth", "6️⃣"), ("yedinci", "seventh", "7️⃣"),
       ("sekizinci", "eighth", "8️⃣"), ("dokuzuncu", "ninth", "9️⃣"), ("onuncu", "tenth", "🔟")]
COLORS = {  # ad: (tr, en, hex, [(emoji, tr, en)])
    "red": ("Kırmızı", "Red", "#E53935", [("🍎", "elma", "apple"), ("🍓", "çilek", "strawberry"), ("🚒", "itfaiye arabası", "fire truck"), ("🌹", "gül", "rose")]),
    "blue": ("Mavi", "Blue", "#1E88E5", [("🐳", "balina", "whale"), ("🫐", "yaban mersini", "blueberry"), ("🌊", "dalga", "wave"), ("🦋", "kelebek", "butterfly")]),
    "yellow": ("Sarı", "Yellow", "#FDD835", [("🍌", "muz", "banana"), ("🌻", "ayçiçeği", "sunflower"), ("⭐", "yıldız", "star"), ("🐥", "civciv", "chick")]),
    "green": ("Yeşil", "Green", "#43A047", [("🐸", "kurbağa", "frog"), ("🌳", "ağaç", "tree"), ("🥒", "salatalık", "cucumber"), ("🐢", "kaplumbağa", "turtle")]),
    "orange": ("Turuncu", "Orange", "#FB8C00", [("🍊", "portakal", "orange"), ("🥕", "havuç", "carrot"), ("🎃", "balkabağı", "pumpkin"), ("🦊", "tilki", "fox")]),
    "purple": ("Mor", "Purple", "#8E24AA", [("🍇", "üzüm", "grapes"), ("🍆", "patlıcan", "eggplant"), ("🔮", "kristal küre", "crystal ball"), ("🟣", "daire", "circle")]),
    "pink": ("Pembe", "Pink", "#EC407A", [("🐷", "domuzcuk", "piggy"), ("🌸", "çiçek", "blossom"), ("🦩", "flamingo", "flamingo"), ("🎀", "kurdele", "ribbon")]),
    "brown": ("Kahverengi", "Brown", "#6D4C41", [("🐻", "ayı", "bear"), ("🥔", "patates", "potato"), ("🌰", "kestane", "chestnut"), ("🍫", "çikolata", "chocolate")]),
    "black": ("Siyah", "Black", "#37474F", [("🎩", "şapka", "hat"), ("🐧", "penguen", "penguin"), ("🕶️", "gözlük", "sunglasses"), ("🐜", "karınca", "ant")]),
    "white": ("Beyaz", "White", "#ECEFF1", [("☁️", "bulut", "cloud"), ("⛄", "kardan adam", "snowman"), ("🥛", "süt", "milk"), ("🐑", "koyun", "sheep")]),
    "gray": ("Gri", "Gray", "#90A4AE", [("🐘", "fil", "elephant"), ("🐭", "fare", "mouse"), ("🪨", "taş", "rock"), ("🕊️", "güvercin", "dove")]),
}
RAINBOW = [("Kırmızı", "Red", "#E53935"), ("Turuncu", "Orange", "#FB8C00"), ("Sarı", "Yellow", "#FDD835"),
           ("Yeşil", "Green", "#43A047"), ("Mavi", "Blue", "#1E88E5"), ("Lacivert", "Indigo", "#3949AB"), ("Mor", "Violet", "#8E24AA")]
COUNT_SETS = ["⭐", "🍎", "🐥", "🎈", "🚗", "🍓", "🐟", "🦋", "🍪", "🌸"]

def video1():
    sc = [S("title", ["🌈", "🔢", "🎨"], "Renkler ve Sayılar", "Colors and Numbers", "Renkler ve Sayılar", "Colors and Numbers"),
          S("trio", ["🎉", "🎈", "🎉"], "Hadi başlayalım!", "Let's go!"),
          S("count", "⭐", "Bir", "One", n=1)]
    # 1-20 sayma (3 tur, her tur baska nesne)
    for rnd, em in enumerate(["⭐", "🍎", "🐥"]):
        for i in range(20):
            if rnd == 0 and i == 0:
                continue
            sc.append(S("count", em, NUM_TR[i].replace("-", " ").capitalize(), NUM_EN[i].capitalize(), n=i + 1))
        if rnd == 0:  # onlar basamagi
            for tr, en, v in TENS:
                sc.append(S("bignum", ["🎉"], tr.capitalize(), en.capitalize(), big=str(v)))
            for i, (tr, en, e) in enumerate(ORD):
                sc.append(S("bignum", [e], tr.capitalize(), en.capitalize(), big=str(i + 1) + "."))
            # geri sayim
            for i in range(10, 0, -1):
                sc.append(S("countdown", "🚀", NUM_TR[i - 1].replace("-", " ").capitalize(), NUM_EN[i - 1].capitalize(), big=str(i)))
            sc.append(S("countdown", "🚀", "Fırla!", "Blast off!", big="🚀"))
    # renkler
    cpool = []
    for key, (ctr, cen, hx, objs) in COLORS.items():
        for e, otr, oen in objs:
            cpool.append(S("color", e, f"{ctr} {otr}", f"{cen} {oen}", bg=hx))
    sc += cpool
    for tr, en, hx in RAINBOW:
        sc.append(S("color", "🌈", tr, en, bg=hx))
    pool = cpool + [S("count", COUNT_SETS[i % 10], NUM_TR[i].replace("-", " ").capitalize(), NUM_EN[i].capitalize(), n=i + 1) for i in range(10)]
    outro = [S("trio", ["👋", "😊", "👋"], "Hoşça kal!", "Bye bye!"), S("trio", ["🎉", "🌈", "🎉"], "Tekrar görüşürüz!", "See you soon!"),
             S("trio", ["❤️", "👋", "❤️"], "Çok sevdik!", "Love you!")]
    return dict(id=1, slug="renkler-ve-sayilar", scenes=fill(sc, pool, outro, 1),
                title_tr="Renkler ve Sayılar 🌈 1'den 20'ye Say, Renkleri Öğren | Türkçe-İngilizce Çocuk Videosu",
                title_en="Colors and Numbers 🌈 Count 1 to 20 & Learn Colors | Turkish-English Kids Video",
                tags="renkler,sayılar,çocuk,eğitici,türkçe,ingilizce,colors,numbers,counting,kids,learn english,toddler")

# ---------------------------------------------------------------- VIDEO 2
ANIMALS = [  # (emoji, tr, en, ses_tr, ses_en)
    ("🐄", "İnek", "Cow", "Möö!", "Moo!"), ("🐖", "Domuz", "Pig", "Hrr hrr!", "Oink oink!"), ("🐑", "Koyun", "Sheep", "Mee!", "Baa!"),
    ("🐐", "Keçi", "Goat", "Meee!", "Maa!"), ("🐓", "Horoz", "Rooster", "Ürü üüü!", "Cock-a-doodle-doo!"), ("🐔", "Tavuk", "Hen", "Gıt gıt!", "Cluck cluck!"),
    ("🦆", "Ördek", "Duck", "Vak vak!", "Quack quack!"), ("🐴", "At", "Horse", "İhaha!", "Neigh!"), ("🐕", "Köpek", "Dog", "Hav hav!", "Woof woof!"),
    ("🐈", "Kedi", "Cat", "Miyav!", "Meow!"), ("🐇", "Tavşan", "Rabbit", None, None), ("🦃", "Hindi", "Turkey", "Glu glu!", "Gobble!"),
    ("🦁", "Aslan", "Lion", "Grrr!", "Roar!"), ("🐯", "Kaplan", "Tiger", "Grrr!", "Rawr!"), ("🐘", "Fil", "Elephant", "Tuuut!", "Toot toot!"),
    ("🦒", "Zürafa", "Giraffe", None, None), ("🦓", "Zebra", "Zebra", None, None), ("🐒", "Maymun", "Monkey", "İi i i!", "Ooh ooh!"),
    ("🦍", "Goril", "Gorilla", None, None), ("🐻", "Ayı", "Bear", None, None), ("🐼", "Panda", "Panda", None, None),
    ("🦘", "Kanguru", "Kangaroo", None, None), ("🐨", "Koala", "Koala", None, None), ("🦏", "Gergedan", "Rhino", None, None),
    ("🦛", "Su aygırı", "Hippo", None, None), ("🐊", "Timsah", "Crocodile", None, None), ("🐺", "Kurt", "Wolf", "Uuuu!", "Awooo!"),
    ("🦊", "Tilki", "Fox", None, None), ("🦌", "Geyik", "Deer", None, None), ("🐿️", "Sincap", "Squirrel", None, None),
    ("🦔", "Kirpi", "Hedgehog", None, None), ("🐪", "Deve", "Camel", None, None),
    ("🐟", "Balık", "Fish", None, None), ("🐠", "Tropik balık", "Tropical fish", None, None), ("🐬", "Yunus", "Dolphin", "Ciii ciii!", "Click click!"),
    ("🐳", "Balina", "Whale", None, None), ("🦈", "Köpek balığı", "Shark", None, None), ("🐙", "Ahtapot", "Octopus", None, None),
    ("🦀", "Yengeç", "Crab", None, None), ("🐢", "Kaplumbağa", "Turtle", None, None), ("🦞", "Istakoz", "Lobster", None, None),
    ("🐡", "Balon balığı", "Pufferfish", None, None), ("🦑", "Mürekkep balığı", "Squid", None, None), ("🐧", "Penguen", "Penguin", None, None),
    ("🦭", "Fok", "Seal", None, None), ("🐚", "Deniz kabuğu", "Seashell", None, None),
    ("🐦", "Kuş", "Bird", "Cik cik!", "Tweet tweet!"), ("🦉", "Baykuş", "Owl", "Hu hu!", "Hoot hoot!"), ("🦜", "Papağan", "Parrot", "Merhaba!", "Hello!"),
    ("🦢", "Kuğu", "Swan", None, None), ("🦅", "Kartal", "Eagle", None, None), ("🐝", "Arı", "Bee", "Vızzz!", "Buzz!"),
    ("🐞", "Uğur böceği", "Ladybug", None, None), ("🦋", "Kelebek", "Butterfly", None, None), ("🐛", "Tırtıl", "Caterpillar", None, None),
    ("🐌", "Salyangoz", "Snail", None, None), ("🐜", "Karınca", "Ant", None, None), ("🦗", "Cırcır böceği", "Cricket", "Cır cır!", "Chirp chirp!"),
    ("🐸", "Kurbağa", "Frog", "Vrak vrak!", "Ribbit!"), ("🦆", "Ördek yavrusu", "Duckling", None, None),
]

def video2():
    sc = [S("title", ["🐯", "🐘", "🦁"], "Hayvanlar ve Sesleri", "Animals and Sounds"),
          S("trio", ["🐶", "🐱", "🐭"], "Hadi hayvanları tanıyalım!", "Meet the animals!")]
    names = [S("single", a[0], a[1], a[2]) for a in ANIMALS]
    snds = [S("sound", a[0], a[3], a[4]) for a in ANIMALS if a[3]]
    sc += names[:12] + snds[:6] + names[12:31] + snds[6:14] + names[31:46] + snds[14:] + names[46:]
    pool = names + snds
    outro = [S("trio", ["👋", "🐾", "👋"], "Hoşça kal!", "Bye bye!"), S("trio", ["🐶", "🐱", "🐰"], "Hayvanları çok sevdik!", "We love animals!"),
             S("trio", ["🎉", "🌈", "🎉"], "Tekrar görüşürüz!", "See you soon!")]
    return dict(id=2, slug="hayvanlar-ve-sesleri", scenes=fill(sc, pool, outro, 2),
                title_tr="Hayvanlar ve Sesleri 🐯 Hayvan Seslerini Öğren | Türkçe-İngilizce Çocuk Videosu",
                title_en="Animals and Their Sounds 🐯 Learn Animal Names & Sounds | Turkish-English Kids Video",
                tags="hayvanlar,hayvan sesleri,çocuk,eğitici,türkçe,ingilizce,animals,animal sounds,kids,toddler,learn english")

# ---------------------------------------------------------------- VIDEO 3
SHAPES = [("circle", "Daire", "Circle"), ("square", "Kare", "Square"), ("triangle", "Üçgen", "Triangle"),
          ("rectangle", "Dikdörtgen", "Rectangle"), ("star", "Yıldız", "Star"), ("heart", "Kalp", "Heart"),
          ("diamond", "Baklava dilimi", "Diamond"), ("oval", "Oval", "Oval"), ("hexagon", "Altıgen", "Hexagon"),
          ("pentagon", "Beşgen", "Pentagon"), ("crescent", "Hilal", "Crescent")]
GROUPS = {
    "fruit": [("🍎", "Elma", "Apple"), ("🍌", "Muz", "Banana"), ("🍊", "Portakal", "Orange"), ("🍇", "Üzüm", "Grapes"), ("🍓", "Çilek", "Strawberry"),
              ("🍉", "Karpuz", "Watermelon"), ("🍍", "Ananas", "Pineapple"), ("🥭", "Mango", "Mango"), ("🍑", "Şeftali", "Peach"), ("🍒", "Kiraz", "Cherry"),
              ("🍋", "Limon", "Lemon"), ("🥝", "Kivi", "Kiwi"), ("🍐", "Armut", "Pear"), ("🍈", "Kavun", "Melon"), ("🥥", "Hindistan cevizi", "Coconut"),
              ("🫐", "Yaban mersini", "Blueberry"), ("🍅", "Domates", "Tomato"), ("🥑", "Avokado", "Avocado")],
    "veg": [("🥕", "Havuç", "Carrot"), ("🥔", "Patates", "Potato"), ("🌽", "Mısır", "Corn"), ("🥦", "Brokoli", "Broccoli"), ("🥒", "Salatalık", "Cucumber"),
            ("🧅", "Soğan", "Onion"), ("🧄", "Sarımsak", "Garlic"), ("🍄", "Mantar", "Mushroom"), ("🫑", "Biber", "Pepper"), ("🥬", "Marul", "Lettuce"),
            ("🍠", "Tatlı patates", "Sweet potato"), ("🎃", "Balkabağı", "Pumpkin"), ("🍆", "Patlıcan", "Eggplant")],
    "vehicle": [("🚗", "Araba", "Car"), ("🚕", "Taksi", "Taxi"), ("🚌", "Otobüs", "Bus"), ("🚓", "Polis arabası", "Police car"), ("🚑", "Ambulans", "Ambulance"),
                ("🚒", "İtfaiye", "Fire truck"), ("🚚", "Kamyon", "Truck"), ("🚜", "Traktör", "Tractor"), ("🏎️", "Yarış arabası", "Race car"),
                ("🏍️", "Motosiklet", "Motorcycle"), ("🚲", "Bisiklet", "Bicycle"), ("🛴", "Scooter", "Scooter"), ("🚂", "Tren", "Train"),
                ("🚁", "Helikopter", "Helicopter"), ("✈️", "Uçak", "Airplane"), ("🚀", "Roket", "Rocket"), ("🚢", "Gemi", "Ship"),
                ("⛵", "Yelkenli", "Sailboat"), ("🚤", "Sürat teknesi", "Speedboat"), ("🛶", "Kano", "Canoe"), ("🚇", "Metro", "Subway"), ("🚡", "Teleferik", "Cable car")],
    "body": [("👀", "Gözler", "Eyes"), ("👂", "Kulak", "Ear"), ("👃", "Burun", "Nose"), ("👄", "Ağız", "Mouth"), ("✋", "El", "Hand"),
             ("🦶", "Ayak", "Foot"), ("🦷", "Diş", "Tooth"), ("💪", "Kol", "Arm")],
    "nature": [("☀️", "Güneş", "Sun"), ("🌙", "Ay", "Moon"), ("⭐", "Yıldız", "Star"), ("☁️", "Bulut", "Cloud"), ("🌧️", "Yağmur", "Rain"),
               ("❄️", "Kar", "Snow"), ("🌈", "Gökkuşağı", "Rainbow"), ("⚡", "Şimşek", "Lightning"), ("💨", "Rüzgar", "Wind"),
               ("🌍", "Dünya", "Earth"), ("🪐", "Gezegen", "Planet")],
    "feel": [("😀", "Mutlu", "Happy"), ("😢", "Üzgün", "Sad"), ("😴", "Uykulu", "Sleepy"), ("😮", "Şaşkın", "Surprised"), ("😂", "Gülüyor", "Laughing"),
             ("😍", "Seviyor", "Loving"), ("🥶", "Üşüyor", "Cold"), ("🥱", "Esniyor", "Yawning"), ("😎", "Havalı", "Cool")],
    "food": [("🍞", "Ekmek", "Bread"), ("🥛", "Süt", "Milk"), ("🧀", "Peynir", "Cheese"), ("🥚", "Yumurta", "Egg"), ("🍪", "Kurabiye", "Cookie"),
             ("🍦", "Dondurma", "Ice cream"), ("🍕", "Pizza", "Pizza")],
}

def video3():
    sc = [S("title", ["🔷", "🍎", "🚗"], "Hızlı Öğren: Şekiller, Meyveler, Taşıtlar", "Quick Learn: Shapes, Fruits, Vehicles",
            "Hızlı Öğren", "Quick Learn"),
          S("trio", ["🎉", "🎈", "🎉"], "Hadi başlayalım!", "Let's go!")]
    shapes = [S("shape", "shape:" + k, tr, en) for k, tr, en in SHAPES]
    groups = {g: [S("single", e, tr, en) for e, tr, en in v] for g, v in GROUPS.items()}
    order = ["fruit", "veg", "vehicle", "body", "nature", "feel", "food"]
    sc += shapes
    for g in order:
        sc += groups[g]
    pool = shapes + [x for g in order for x in groups[g]]
    outro = [S("trio", ["👋", "😊", "👋"], "Hoşça kal!", "Bye bye!"), S("trio", ["🎉", "🌈", "🎉"], "Tekrar görüşürüz!", "See you soon!"),
             S("trio", ["❤️", "👋", "❤️"], "Çok sevdik!", "Love you!")]
    return dict(id=3, slug="sekiller-meyveler-tasitlar", scenes=fill(sc, pool, outro, 3),
                title_tr="Hızlı Öğren ⚡ Şekiller, Meyveler, Taşıtlar ve Daha Fazlası | Türkçe-İngilizce Çocuk Videosu",
                title_en="Quick Learn ⚡ Shapes, Fruits, Vehicles & More | Turkish-English Kids Video",
                tags="şekiller,meyveler,taşıtlar,çocuk,eğitici,türkçe,ingilizce,shapes,fruits,vehicles,kids,toddler,learn english")

VIDEOS = {1: video1, 2: video2, 3: video3}
