import asyncio
import random
import sqlite3
import time
import os
from threading import Thread

import discord
from discord.ext import commands

# ============================================================
# RENDER PORT HATASINI ÇÖZEN MİNİ WEB SUNUCUSU
# ============================================================
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "OwO Bot aktif ve çalışıyor!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
# ============================================================

# ============================================================
# AYARLAR
# ============================================================
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1505077083003555972  # BURAYA KENDİ DISCORD ID'Nİ YAZ
PREFIXES = ["s!", "S!", "owo ", "Owo ", "OWO ", "o "]
PARA_EMOJI = "🪙"  # kendi emojin: "<:para:123456789012345678>"

# --- Özel emojiler (animasyonlular <a:...> ile başlar) ---
SLOT_DONME = "<a:SlotsRolling:1568658456766849056>"   # slot dönerken
KALP = "<:kalp:1568659160344563712>"
PATLICAN = "<:patlcan:1568659129419964536>"
CHERRY = "<:cherry:1568659177679626360>"

COIN_DONME = "<a:dnencoin:1568659254276001904>"       # para havadayken
SURATLI = "<:suratl:1568659272907358308>"             # suratlı taraf = Tura
SURATSIZ = "<:suratsz:1568659291228078111>"           # suratsız taraf = Yazı

# Slot: 3 aynı sembol gelirse bahsin kaç katını kazanırsın
SLOT_KAT = {KALP: 12, PATLICAN: 6, CHERRY: 4}

# ============================================================
# HAYVANLAR - emojileri buradan değiştir
# Özel emoji formatı: "<:isim:ID>"  (Discord'da \:emoji: yazarak ID'yi bulursun)
# ============================================================
HAYVANLAR = {
    "yaygin": {
        "ad": "Yaygın", "sans": 60, "fiyat": 10, "guc": 1,
        "liste": {"🐀": "Fare", "🐔": "Tavuk", "🐸": "Kurbağa", "🐛": "Tırtıl", "🐟": "Balık"},
    },
    "seyrek": {
        "ad": "Seyrek", "sans": 25, "fiyat": 30, "guc": 3,
        "liste": {"🐇": "Tavşan", "🦊": "Tilki", "🐺": "Kurt", "🦆": "Ördek"},
    },
    "nadir": {
        "ad": "Nadir", "sans": 10, "fiyat": 100, "guc": 8,
        "liste": {"🐻": "Ayı", "🦅": "Kartal", "🐊": "Timsah"},
    },
    "destansi": {
        "ad": "Destansı", "sans": 4, "fiyat": 400, "guc": 20,
        "liste": {"🦁": "Aslan", "🐯": "Kaplan", "🦈": "Köpekbalığı"},
    },
    "efsanevi": {
        "ad": "Efsanevi", "sans": 1, "fiyat": 2000, "guc": 60,
        "liste": {"🐉": "Ejderha", "🦄": "Tek Boynuzlu At", "🔥": "Anka Kuşu"},
    },
}
SIRA = ["yaygin", "seyrek", "nadir", "destansi", "efsanevi"]

# "Destansı", "efsanevi", "ı/İ" gibi yazımları aynı hale getirir
TR_TABLO = str.maketrans("ıİşŞçÇğĞöÖüÜ", "iissccggoouu")


def sade(metin):
    return metin.translate(TR_TABLO).lower()


# ============================================================
# VERİTABANI
# ============================================================
db = sqlite3.connect("owo_tr.db")
db.execute("CREATE TABLE IF NOT EXISTS kullanici (id INTEGER PRIMARY KEY, para INTEGER DEFAULT 100, son_gunluk REAL DEFAULT 0, seri INTEGER DEFAULT 0)")
db.execute("CREATE TABLE IF NOT EXISTS hayvanat (kullanici_id INTEGER, emoji TEXT, adet INTEGER, PRIMARY KEY (kullanici_id, emoji))")
db.commit()


def kullanici_al(uid):
    db.execute("INSERT OR IGNORE INTO kullanici (id) VALUES (?)", (uid,))
    db.commit()
    return db.execute("SELECT para, son_gunluk, seri FROM kullanici WHERE id=?", (uid,)).fetchone()


def para_ekle(uid, miktar):
    kullanici_al(uid)
    db.execute("UPDATE kullanici SET para = para + ? WHERE id=?", (miktar, uid))
    db.commit()


def hayvan_ekle(uid, emoji, n=1):
    db.execute(
        "INSERT INTO hayvanat (kullanici_id, emoji, adet) VALUES (?,?,?) "
        "ON CONFLICT(kullanici_id, emoji) DO UPDATE SET adet = adet + ?",
        (uid, emoji, n, n),
    )
    db.commit()


def hayvan_bul(emoji):
    for nadirlik, veri in HAYVANLAR.items():
        if emoji in veri["liste"]:
            return nadirlik, veri["liste"][emoji]
    return None, None


def takim_gucu(uid):
    satirlar = db.execute("SELECT emoji, adet FROM hayvanat WHERE kullanici_id=?", (uid,)).fetchall()
    gucler = []
    for emoji, adet in satirlar:
        nadirlik, _ = hayvan_bul(emoji)
        if nadirlik:
            gucler += [HAYVANLAR[nadirlik]["guc"]] * adet
    gucler.sort(reverse=True)
    return sum(gucler[:3])


# ============================================================
# BOT
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*PREFIXES),
    intents=intents,
    case_insensitive=True,
    help_command=None,
)


@bot.event
async def on_ready():
    print(f"{bot.user} hazır!")


@bot.event
async def on_command_error(ctx, hata):
    if isinstance(hata, commands.CommandOnCooldown):
        await ctx.reply(f"⏳ Biraz yavaş! **{hata.retry_after:.0f} sn** beklemelisin.", mention_author=False)
    elif isinstance(hata, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.reply("❌ Hatalı kullanım. Komutlar için `owo yardim` yaz.", mention_author=False)
    elif isinstance(hata, (commands.CommandNotFound, commands.CheckFailure)):
        pass
    else:
        raise hata


# ---------------- AV ----------------
@bot.command(name="av", aliases=["h", "hunt"])
@commands.cooldown(1, 15, commands.BucketType.user)
async def av(ctx):
    nadirlik = random.choices(SIRA, weights=[HAYVANLAR[r]["sans"] for r in SIRA])[0]
    emoji, ad = random.choice(list(HAYVANLAR[nadirlik]["liste"].items()))
    hayvan_ekle(ctx.author.id, emoji)
    await ctx.reply(
        f"🌱 **{ctx.author.display_name}** ava çıktı ve {emoji} **{ad}** yakaladı! (`{HAYVANLAR[nadirlik]['ad']}`)",
        mention_author=False,
    )


# ---------------- HAYVANAT ----------------
@bot.command(name="hayvanat", aliases=["z", "zoo", "hayvanlar"])
async def hayvanat(ctx):
    satirlar = dict(db.execute("SELECT emoji, adet FROM hayvanat WHERE kullanici_id=?", (ctx.author.id,)).fetchall())
    embed = discord.Embed(title=f"🌿 {ctx.author.display_name} Hayvanat Bahçesi", color=0x4CAF50)
    toplam = 0
    for nadirlik in SIRA:
        satir = ""
        for emoji in HAYVANLAR[nadirlik]["liste"]:
            if satirlar.get(emoji, 0) > 0:
                satir += f"{emoji}x{satirlar[emoji]}  "
                toplam += satirlar[emoji]
        embed.add_field(name=HAYVANLAR[nadirlik]["ad"], value=satir or "—", inline=False)
    embed.set_footer(text=f"Toplam hayvan: {toplam}")
    await ctx.reply(embed=embed, mention_author=False)


# ---------------- SAT ----------------
@bot.command(name="sat", aliases=["s", "sell"])
async def sat(ctx, hedef: str = "hepsi"):
    hedef = sade(hedef)
    if hedef in ("all", "hepsi", "tum", "tumu"):
        hedef = "hepsi"
    elif hedef not in HAYVANLAR:
        return await ctx.reply(
            "❌ Geçersiz tür. Örnek: `owo sat hepsi`, `owo sat yaygin`, `owo sat nadir`",
            mention_author=False,
        )
    satirlar = db.execute("SELECT emoji, adet FROM hayvanat WHERE kullanici_id=? AND adet>0", (ctx.author.id,)).fetchall()
    kazanc, satilan = 0, 0
    for emoji, adet in satirlar:
        nadirlik, _ = hayvan_bul(emoji)
        if not nadirlik or (hedef != "hepsi" and hedef != nadirlik):
            continue
        kazanc += HAYVANLAR[nadirlik]["fiyat"] * adet
        satilan += adet
        db.execute("UPDATE hayvanat SET adet=0 WHERE kullanici_id=? AND emoji=?", (ctx.author.id, emoji))
    db.commit()
    if satilan == 0:
        return await ctx.reply("❌ Satacak hayvanın yok. Önce `owo av` yaz!", mention_author=False)
    para_ekle(ctx.author.id, kazanc)
    await ctx.reply(f"💰 **{satilan}** hayvan satıldı ve **{kazanc}** {PARA_EMOJI} kazandın!", mention_author=False)


# ---------------- PARA ----------------
@bot.command(name="para", aliases=["c", "cash", "bakiye"])
async def para(ctx):
    p, _, _ = kullanici_al(ctx.author.id)
    await ctx.reply(f"{PARA_EMOJI} **{ctx.author.display_name}**, bakiyen: **{p}**", mention_author=False)


# ---------------- GÜNLÜK ----------------
@bot.command(name="gunluk", aliases=["günlük", "d", "daily"])
async def gunluk(ctx):
    _, son, seri = kullanici_al(ctx.author.id)
    simdi = time.time()
    if simdi - son < 86400:
        kalan = int(86400 - (simdi - son))
        return await ctx.reply(
            f"⏳ Günlük ödülün için **{kalan // 3600} sa {kalan % 3600 // 60} dk** beklemelisin.",
            mention_author=False,
        )
    seri = seri + 1 if simdi - son < 172800 else 1
    odul = 250 + min(seri, 30) * 25
    db.execute("UPDATE kullanici SET para=para+?, son_gunluk=?, seri=? WHERE id=?", (odul, simdi, seri, ctx.author.id))
    db.commit()
    await ctx.reply(f"🎁 Günlük ödülün: **{odul}** {PARA_EMOJI}  |  🔥 Seri: **{seri}** gün", mention_author=False)


# ---------------- VER ----------------
@bot.command(name="ver", aliases=["g", "give"])
async def ver(ctx, uye: discord.Member, miktar: int):
    if uye.bot or uye == ctx.author or miktar <= 0:
        return await ctx.reply("❌ Geçersiz işlem.", mention_author=False)
    p, _, _ = kullanici_al(ctx.author.id)
    if miktar > p:
        return await ctx.reply("❌ Yeterli paran yok.", mention_author=False)
    para_ekle(ctx.author.id, -miktar)
    para_ekle(uye.id, miktar)
    await ctx.reply(f"💸 {uye.mention} kullanıcısına **{miktar}** {PARA_EMOJI} gönderdin.", mention_author=False)


# ---------------- PARA YOLLA (SADECE BOT SAHİBİ) ----------------
@bot.command(name="parayolla", aliases=["pv"])
@commands.check(lambda ctx: ctx.author.id == OWNER_ID)
async def parayolla(ctx, kullanici_id: int, miktar: int):
    if miktar <= 0:
        return await ctx.reply("❌ Miktar 0'dan büyük olmalı.", mention_author=False)
    try:
        hedef = await bot.fetch_user(kullanici_id)
    except discord.NotFound:
        return await ctx.reply("❌ Bu ID'ye ait bir kullanıcı bulunamadı.", mention_author=False)
    para_ekle(kullanici_id, miktar)
    yeni, _, _ = kullanici_al(kullanici_id)
    await ctx.reply(
        f"✅ **{hedef}** (`{kullanici_id}`) kullanıcısına **{miktar}** {PARA_EMOJI} gönderildi.\n"
        f"Yeni bakiyesi: **{yeni}** {PARA_EMOJI}",
        mention_author=False,
    )


# ---------------- YAZI TURA ----------------
@bot.command(name="yazitura", aliases=["yt", "cf", "coinflip"])
async def yazitura(ctx, miktar: int = 1, taraf: str = "y"):
    p, _, _ = kullanici_al(ctx.author.id)
    if miktar <= 0 or miktar > p:
        return await ctx.reply("❌ Geçersiz miktar veya yetersiz bakiye.", mention_author=False)
    secim = "y" if sade(taraf) in ("y", "yazi", "h", "heads") else "t"
    sonuc = random.choice(["y", "t"])
    ad = {"y": "Yazı", "t": "Tura"}[sonuc]
    yuz = SURATSIZ if sonuc == "y" else SURATLI  # suratsız = Yazı, suratlı = Tura
    secilen = "Yazı" if secim == "y" else "Tura"

    mesaj = await ctx.reply(
        f"{COIN_DONME} **{ctx.author.display_name}** **{miktar}** {PARA_EMOJI} bahis yaptı ve **{secilen}** seçti...",
        mention_author=False,
    )
    await asyncio.sleep(2)

    if secim == sonuc:
        para_ekle(ctx.author.id, miktar)
        await mesaj.edit(content=f"{yuz} **{ad}** geldi! **{miktar * 2}** {PARA_EMOJI} kazandın!")
    else:
        para_ekle(ctx.author.id, -miktar)
        await mesaj.edit(content=f"{yuz} **{ad}** geldi... **{miktar}** {PARA_EMOJI} kaybettin.")


# ---------------- SLOT ----------------
@bot.command(name="slot", aliases=["slots"])
async def slot(ctx, miktar: int = 1):
    p, _, _ = kullanici_al(ctx.author.id)
    if miktar <= 0 or miktar > p:
        return await ctx.reply("❌ Geçersiz miktar veya yetersiz bakiye.", mention_author=False)
    semboller = list(SLOT_KAT.keys())
    r = [random.choice(semboller) for _ in range(3)]
    kat = SLOT_KAT[r[0]] if r[0] == r[1] == r[2] else 0

    mesaj = await ctx.reply(
        f"**{ctx.author.display_name}** **{miktar}** {PARA_EMOJI} bahis yaptı\n"
        f"🎰 | {SLOT_DONME} {SLOT_DONME} {SLOT_DONME} |",
        mention_author=False,
    )
    await asyncio.sleep(2)

    para_ekle(ctx.author.id, miktar * kat - miktar)
    sonuc = f"🎉 **{miktar * kat}** {PARA_EMOJI} kazandın! (x{kat})" if kat else f"😢 **{miktar}** {PARA_EMOJI} kaybettin."
    await mesaj.edit(
        content=(
            f"**{ctx.author.display_name}** **{miktar}** {PARA_EMOJI} bahis yaptı\n"
            f"🎰 | {' '.join(r)} |\n{sonuc}"
        )
    )


# ---------------- SAVAŞ ----------------
@bot.command(name="savas", aliases=["savaş", "b", "battle"])
@commands.cooldown(1, 20, commands.BucketType.user)
async def savas(ctx, rakip: discord.Member):
    if rakip.bot or rakip == ctx.author:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("❌ Geçersiz rakip.", mention_author=False)
    g1, g2 = takim_gucu(ctx.author.id), takim_gucu(rakip.id)
    if g1 + g2 == 0:
        ctx.command.reset_cooldown(ctx)
        return await ctx.reply("❌ İki tarafın da hayvanı yok. Önce `owo av` yaz!", mention_author=False)
    kazanan = ctx.author if random.random() < g1 / (g1 + g2) else rakip
    odul = random.randint(20, 60)
    para_ekle(kazanan.id, odul)
    await ctx.reply(
        f"⚔️ **{ctx.author.display_name}** (güç {g1}) vs **{rakip.display_name}** (güç {g2})\n"
        f"🏆 Kazanan: {kazanan.mention}  +**{odul}** {PARA_EMOJI}",
        mention_author=False,
    )


# ---------------- YARDIM ----------------
@bot.command(name="yardim", aliases=["yardım", "help"])
async def yardim(ctx):
    embed = discord.Embed(
        title="📖 Yardım Menüsü",
        description="Önek olarak **`s!`** veya **`owo `** kullanabilirsin.\nÖrnek: `s!av` ya da `owo av`",
        color=0x5865F2,
    )
    embed.add_field(
        name="🌿 Hayvan Sistemi",
        value=(
            "`s!av` (h) • Ava çıkıp rastgele hayvan yakalarsın (15 sn bekleme)\n"
            "`s!hayvanat` (z) • Yakaladığın hayvanları gösterir\n"
            "`s!sat hepsi` • Tüm hayvanlarını satar\n"
            "`s!sat <tür>` • Sadece o türü satar\n"
            "Türler: `yaygin`, `seyrek`, `nadir`, `destansi`, `efsanevi`"
        ),
        inline=False,
    )
    embed.add_field(
        name=f"{PARA_EMOJI} Ekonomi",
        value=(
            "`s!para` (c) • Bakiyeni gösterir\n"
            "`s!gunluk` (d) • Günlük ödülünü alırsın, art arda almak bonus verir\n"
            "`s!ver @kişi <miktar>` (g) • Başkasına para gönderir"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎰 Oyunlar",
        value=(
            "`s!yazitura <miktar> <y/t>` (yt) • Yazı tura, kazanırsan 2 katı\n"
            "`s!slot <miktar>` • Slot makinesi, 3 aynı sembol gelirse kazanırsın\n"
            f" {KALP} x12 • {PATLICAN} x6 • {CHERRY} x4\n"
            "`s!savas @kişi` (b) • En güçlü 3 hayvanla savaşırsın (20 sn bekleme)"
        ),
        inline=False,
    )
    embed.add_field(
        name="ℹ️ Diğer",
        value="`s!yardim` • Bu menüyü gösterir",
        inline=False,
    )
    embed.set_footer(text="Parantez içindekiler kısa yoludur. Örnek: s!h = s!av")
    await ctx.reply(embed=embed, mention_author=False)


bot.run(TOKEN)