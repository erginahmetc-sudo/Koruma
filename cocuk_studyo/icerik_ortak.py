# -*- coding: utf-8 -*-
"""Ortak içerik havuzları (renkler, hayvanlar, taşıtlar, zıtlıklar, şekiller)."""

COLORS = {  # (tr, en, hex, [(emoji, tr, en) x4])
    "red": ("Kırmızı", "Red", "#E53935", [("🍎", "elma", "apple"), ("🍓", "çilek", "strawberry"), ("🚒", "itfaiye arabası", "fire truck"), ("🌹", "gül", "rose")]),
    "orange": ("Turuncu", "Orange", "#FB8C00", [("🍊", "portakal", "orange"), ("🥕", "havuç", "carrot"), ("🎃", "balkabağı", "pumpkin"), ("🦊", "tilki", "fox")]),
    "yellow": ("Sarı", "Yellow", "#FDD835", [("🍌", "muz", "banana"), ("🌻", "ayçiçeği", "sunflower"), ("⭐", "yıldız", "star"), ("🐥", "civciv", "chick")]),
    "green": ("Yeşil", "Green", "#43A047", [("🐸", "kurbağa", "frog"), ("🌳", "ağaç", "tree"), ("🥒", "salatalık", "cucumber"), ("🐢", "kaplumbağa", "turtle")]),
    "blue": ("Mavi", "Blue", "#1E88E5", [("🐳", "balina", "whale"), ("🫐", "yaban mersini", "blueberry"), ("🌊", "dalga", "wave"), ("🦋", "kelebek", "butterfly")]),
    "purple": ("Mor", "Purple", "#8E24AA", [("🍇", "üzüm", "grapes"), ("🍆", "patlıcan", "eggplant"), ("🔮", "kristal küre", "crystal ball"), ("🟣", "daire", "circle")]),
    "pink": ("Pembe", "Pink", "#EC407A", [("🐷", "domuzcuk", "piggy"), ("🌸", "çiçek", "blossom"), ("🦩", "flamingo", "flamingo"), ("🎀", "kurdele", "ribbon")]),
    "brown": ("Kahverengi", "Brown", "#6D4C41", [("🐻", "ayı", "bear"), ("🥔", "patates", "potato"), ("🌰", "kestane", "chestnut"), ("🍫", "çikolata", "chocolate")]),
    "black": ("Siyah", "Black", "#37474F", [("🎩", "şapka", "hat"), ("🐧", "penguen", "penguin"), ("🕶️", "gözlük", "sunglasses"), ("🐜", "karınca", "ant")]),
    "white": ("Beyaz", "White", "#90A4AE", [("☁️", "bulut", "cloud"), ("⛄", "kardan adam", "snowman"), ("🥛", "süt", "milk"), ("🐑", "koyun", "sheep")]),
    "gray": ("Gri", "Gray", "#78909C", [("🐘", "fil", "elephant"), ("🐭", "fare", "mouse"), ("🪨", "taş", "rock"), ("🕊️", "güvercin", "dove")]),
}
MIX = [(("🔴", "Kırmızı", "Red"), ("🟡", "Sarı", "Yellow"), ("🟠", "Turuncu", "Orange")),
       (("🔵", "Mavi", "Blue"), ("🟡", "Sarı", "Yellow"), ("🟢", "Yeşil", "Green")),
       (("🔴", "Kırmızı", "Red"), ("🔵", "Mavi", "Blue"), ("🟣", "Mor", "Purple"))]

FARM = [("🐄", "İnek", "Cow", "Möö!", "Moo!", "meadow"), ("🐖", "Domuz", "Pig", "Hrr hrr!", "Oink oink!", "meadow"), ("🐑", "Koyun", "Sheep", "Mee!", "Baa!", "meadow"),
        ("🦆", "Ördek", "Duck", "Vak vak!", "Quack quack!", "meadow"), ("🐴", "At", "Horse", "İhaha!", "Neigh!", "meadow"), ("🐕", "Köpek", "Dog", "Hav hav!", "Woof woof!", "meadow"),
        ("🐈", "Kedi", "Cat", "Miyav!", "Meow!", "room"), ("🐔", "Tavuk", "Hen", "Gıt gıt!", "Cluck cluck!", "meadow"), ("🐓", "Horoz", "Rooster", "Ürü üüü!", "Cock-a-doodle-doo!", "meadow"),
        ("🐐", "Keçi", "Goat", "Meee!", "Maa!", "meadow"), ("🦃", "Hindi", "Turkey", "Glu glu!", "Gobble!", "forest"), ("🐇", "Tavşan", "Rabbit", "Zıp zıp!", "Hop hop!", "forest")]
WILD = [("🦁", "Aslan", "Lion", "Grrr!", "Roar!", "forest"), ("🐘", "Fil", "Elephant", "Tuuut!", "Toot toot!", "forest"), ("🐒", "Maymun", "Monkey", "İi i i!", "Ooh ooh!", "forest"),
        ("🐯", "Kaplan", "Tiger", "Grrr!", "Rawr!", "forest"), ("🐺", "Kurt", "Wolf", "Uuuu!", "Awooo!", "snow"), ("🦉", "Baykuş", "Owl", "Hu hu!", "Hoot hoot!", "space"),
        ("🐸", "Kurbağa", "Frog", "Vrak vrak!", "Ribbit!", "forest"), ("🐝", "Arı", "Bee", "Vızzz!", "Buzz!", "meadow"), ("🦒", "Zürafa", "Giraffe", "Boyum uzun!", "I am tall!", "forest"),
        ("🦓", "Zebra", "Zebra", "Çizgili!", "Striped!", "meadow"), ("🐻", "Ayı", "Bear", "Uykum var!", "I am sleepy!", "snow"), ("🦘", "Kanguru", "Kangaroo", "Zıp zıp!", "Boing boing!", "meadow")]
SEA = [("🐬", "Yunus", "Dolphin", "Ciii ciii!", "Click click!", "under"), ("🐳", "Balina", "Whale", "Fış fış!", "Splash!", "under"), ("🐙", "Ahtapot", "Octopus", "Sekiz kol!", "Eight arms!", "under"),
       ("🦀", "Yengeç", "Crab", "Yan yürür!", "Walks sideways!", "beach"), ("🐢", "Kaplumbağa", "Turtle", "Yavaş yavaş!", "Slowly, slowly!", "beach"), ("🐠", "Balık", "Fish", "Yüzer!", "Swims!", "under"),
       ("🐦", "Kuş", "Bird", "Cik cik!", "Tweet tweet!", "forest"), ("🦜", "Papağan", "Parrot", "Merhaba!", "Hello!", "forest"), ("🦢", "Kuğu", "Swan", "Şık şık!", "So elegant!", "meadow"),
       ("🐧", "Penguen", "Penguin", "Kayar!", "Slides on ice!", "snow"), ("🐞", "Uğur böceği", "Ladybug", "Beni say!", "Count my dots!", "meadow"), ("🦋", "Kelebek", "Butterfly", "Kanat çırpar!", "Flaps wings!", "meadow")]

VEHICLES = [("🚗", "Araba", "Car", "Bip bip!", "Beep beep!", "town", "Markete gidelim!", "Let's go shopping!"), ("🚌", "Otobüs", "Bus", "Vın vın!", "Vroom vroom!", "town", "Okula gidelim!", "Let's go to school!"),
            ("🚂", "Tren", "Train", "Çuf çuf!", "Choo choo!", "meadow", "Anneanneye gidelim!", "Let's visit Grandma!"), ("✈️", "Uçak", "Airplane", "Vıııv!", "Whoosh!", "beach", "Tatile gidelim!", "Let's go on holiday!"),
            ("🚁", "Helikopter", "Helicopter", "Pırrr!", "Whirr!", "meadow", "Yukarıdan bakalım!", "Let's look from above!"), ("🚢", "Gemi", "Ship", "Tuuut!", "Toot toot!", "beach", "Denize açılalım!", "Let's sail the sea!"),
            ("🚀", "Roket", "Rocket", "Fışşş!", "Whoosh!", "space", "Yıldızlara gidelim!", "Let's go to the stars!"), ("🚒", "İtfaiye", "Fire truck", "Viyu viyu!", "Wee-woo!", "town", "Kedi ağaçta kaldı!", "A kitty is stuck in a tree!"),
            ("🚑", "Ambulans", "Ambulance", "Viyu viyu!", "Wee-woo!", "town", "Biri yardım istiyor!", "Someone needs help!"), ("🚜", "Traktör", "Tractor", "Tırrr tırrr!", "Putt putt!", "meadow", "Tarlayı sürelim!", "Let's plow the field!"),
            ("🚲", "Bisiklet", "Bicycle", "Tring tring!", "Ring ring!", "meadow", "Parka gidelim!", "Let's go to the park!"), ("🚚", "Kamyon", "Truck", "Brrm brrm!", "Rumble rumble!", "town", "Paketleri taşıyalım!", "Let's carry the boxes!"),
            ("🛴", "Scooter", "Scooter", "Vızzz!", "Zoom!", "candy", "Yarışalım!", "Let's race!"), ("🚇", "Metro", "Subway", "Şşşş!", "Whoosh!", "town", "Şehri gezelim!", "Let's tour the city!")]

OPPOSITES = [(("🐘", "Büyük", "Big"), ("🐭", "Küçük", "Small")), (("☀️", "Sıcak", "Hot"), ("❄️", "Soğuk", "Cold")), (("⬆️", "Yukarı", "Up"), ("⬇️", "Aşağı", "Down")),
             (("🐇", "Hızlı", "Fast"), ("🐢", "Yavaş", "Slow")), (("🌞", "Gündüz", "Day"), ("🌙", "Gece", "Night")), (("😀", "Mutlu", "Happy"), ("😢", "Üzgün", "Sad")),
             (("🦒", "Uzun", "Tall"), ("🐛", "Kısa", "Short")), (("🥛", "Dolu", "Full"), ("🍽️", "Boş", "Empty")), (("📖", "Açık", "Open"), ("📕", "Kapalı", "Closed")),
             (("🪶", "Hafif", "Light"), ("🪨", "Ağır", "Heavy")), (("☔", "Islak", "Wet"), ("🌵", "Kuru", "Dry")), (("🛁", "Temiz", "Clean"), ("🐷", "Kirli", "Dirty")),
             (("🔊", "Gürültülü", "Loud"), ("🔇", "Sessiz", "Quiet"))]

SHAPES = [("circle", "Daire", "Circle", "⚽", "Top", "Ball"), ("square", "Kare", "Square", "🎁", "Hediye", "Gift"), ("triangle", "Üçgen", "Triangle", "🍕", "Pizza", "Pizza"),
          ("rectangle", "Dikdörtgen", "Rectangle", "🚪", "Kapı", "Door"), ("star", "Yıldız", "Star", "🌟", "Parlak", "Shiny"), ("heart", "Kalp", "Heart", "💌", "Mektup", "Letter"),
          ("diamond", "Baklava dilimi", "Diamond", "🪁", "Uçurtma", "Kite"), ("oval", "Oval", "Oval", "🥚", "Yumurta", "Egg"), ("hexagon", "Altıgen", "Hexagon", "🍯", "Bal", "Honey"),
          ("pentagon", "Beşgen", "Pentagon", "🏠", "Ev", "House"), ("crescent", "Hilal", "Crescent", "🌙", "Ay", "Moon")]
