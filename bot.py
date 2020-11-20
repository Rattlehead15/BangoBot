import os
from discord.ext import commands
import mysql.connector
from dotenv import load_dotenv
import copy
import emoji
import re

inventario = {
    "0": ["0️⃣"],
    "1": ["1️⃣"],
    "2": ["2️⃣"],
    "3": ["3️⃣"],
    "4": ["4️⃣"],
    "5": ["5️⃣"],
    "6": ["6️⃣"],
    "7": ["7️⃣"],
    "8": ["8️⃣"],
    "9": ["9️⃣"],
    "A": ["🅰️", "🇦", "🇱🇨"],
    "B": ["🅱️", "🇧"],
    "C": ["🇨", "©️", "☪️", "↪️", "🌜"],
    "D": ["🇩", "↩️"],
    "E": ["🇪", "📧"],
    "F": ["🇫"],
    "G": ["🇬", "🗜️"],
    "H": ["🇭", "♓", "🏨", "🏩"],
    "I": ["ℹ️", "🇮", "📍", "🥄", "💈", "♟️", "💄", "👃"],
    "J": ["🇯", "⤴️", "☂️"],
    "K": ["🇰"],
    "L": ["🇱", "🕒", "📐"],
    "M": ["Ⓜ️", "🇲", "〽️", "♏", "♍"],
    "N": ["🇳", "♑", "📈"],
    "O": ["⭕", "🅾️", "🇴", "🚫", "🔄", "👌", "🔅", "⚙️", "🔘"],
    "P": ["🅿️", "🇵"],
    "Q": ["🇶", "🔍", "🍭", "🏓", "🎯"],
    "R": ["🇷", "®️"],
    "S": ["💲", "🇸", "💰", "💵", "💸"],
    "T": ["🇹", "✝️", "🪧"],
    "U": ["⛎", "🇺"],
    "V": ["🇻", "♈"],
    "W": ["🇼", "〰️"],
    "X": ["❌", "✖️", "🇽", "❎", "⚔️", "⚒️", "✂️"],
    "Y": ["🇾", "💹", "💴"],
    "Z": ["🇿", "💤"]
}

async def getPrefijo(bot, message):
    prefijo = "b!"
    try:
        cursor = cnx.cursor()
        datos = (message.guild.id, )
        cursor.execute("SELECT prefijo FROM guilds WHERE discord_id = %s", datos)
        prefijo = cursor.fetchone() or "b!"
        cnx.commit()
    except Exception as e:
        print(e)
    finally:
        return prefijo

async def setPrefijo(guildId, prefijo):
    try:
        cursor = cnx.cursor()
        datos = {"guild": guildId, "prefijo": prefijo}
        cursor.execute("""INSERT INTO guilds (discord_id, prefijo) VALUES (%(guild)s, %(prefijo)s)
                            ON DUPLICATE KEY UPDATE prefijo = %(prefijo)s """, datos)
        cnx.commit()
        return True
    except Exception as e:
        print(e)
    return False

def buildMessage(message, inv = copy.deepcopy(inventario), macros = [], customEmojis = []):
    for m in macros:
        message = message.replace("(" + m[0] + ")", m[1])
    customs = re.finditer("<[^>]*>", message)
    ids = []
    if customs:
        for match in customs:
            if i := next((x for x in customEmojis if match.group() == str(x)), None):
                ids.append(i)
        message = re.sub("<[^>]*>", "_", message)
    veces = {a: 0 for a in inv.keys()}
    message = message.replace(" ", "").upper()
    reacciones = []
    alcanzan = True
    for c in message:
        if c in emoji.UNICODE_EMOJI:
            reacciones.append(c)
        elif c in inv.keys():
            if veces[c] >= len(inv[c]):
                alcanzan = False
                break
            reacciones.append(inv[c][veces[c]])
            veces[c] += 1
        elif c == "_":
            reacciones.append(ids.pop(0))
        else:
            alcanzan = False
            break
    
    alcanzan = alcanzan and len(reacciones) == len(frozenset(reacciones))
    return reacciones if alcanzan else []

async def getMacros(guild_id):
    try:
        cursor = cnx.cursor()
        datos = (guild_id,)
        cursor.execute("SELECT keyword, expansion FROM macros WHERE guild_discord_id = %s", datos)
        macros = cursor.fetchall()
        cnx.commit()
        return macros
    except Exception as e:
        print(e)
    return []

async def addMacro(keyword, expansion, guild_id):
    try:
        cursor = cnx.cursor()
        datos = {"keyword": keyword, "expansion": expansion, "guild_discord_id": guild_id}
        cursor.execute("INSERT INTO macros (keyword, expansion, guild_discord_id) VALUES (%(keyword)s, %(expansion)s, %(guild_discord_id)s)", datos)
        cnx.commit()
        return True
    except Exception as e:
        print(e)
    return False

async def deleteMacro(keyword, guild_id):
    try:
        cursor = cnx.cursor()
        datos = {"keyword": keyword, "guild_discord_id": guild_id}
        cursor.execute("DELETE FROM macros WHERE keyword = %(keyword)s AND guild_discord_id = %(guild_discord_id)s", datos)
        cnx.commit()
        return True
    except Exception as e:
        print(e)
    return False

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SQL_USER = os.getenv("SQL_USER")
SQL_PASS = os.getenv("SQL_PASS")
SQL_DATABASE = os.getenv("SQL_DATABASE")
cnx = mysql.connector.connect(
    host = "localhost",
    user = SQL_USER,
    password = SQL_PASS,
    database = SQL_DATABASE,
    port = 3306
)
bot = commands.Bot(command_prefix = getPrefijo)

@bot.command(name = "react", help = "React to a message with emoji words")
async def emojiReact(ctx, *, message: str):
    canal = ctx.channel
    if ctx.message.reference:
        cita = await canal.fetch_message(ctx.message.reference.message_id)
    else:
        cita = (await canal.history(limit = 2).flatten())[1]
    await ctx.message.delete()
    try:
        customEmojis = list(ctx.guild.emojis)
        macros = await getMacros(ctx.guild.id)
        reacciones = buildMessage(message, macros=macros, customEmojis=customEmojis)
        if not reacciones:
            m = await canal.send("There's not enough emoji to write that!")
            await m.delete(delay = 5)
        else:
            for c in reacciones:
                await cita.add_reaction(c)
    except Exception as e:
        m = await canal.send("An error ocurred. Try again maybe?")
        await m.delete(delay = 5)
        print(e)

@bot.command(name = "prefix", help = "Changes bot prefix or reverts back to b! if unspecified")
async def changePrefix(ctx, *, prefix = "b!"):
    result = await setPrefijo(ctx.guild.id, prefix)
    if result:
        m = await ctx.send(f"Prefix changed to {prefix}")
        await m.delete(delay = 5)
    else:
        m = await ctx.send(f"Prefix couldn't be changed :(")
        await m.delete(delay = 5)

@bot.command(name = "macro", help = "Creates and deletes emoji macros for replies")
async def manageMacros(ctx, mode, keyword, expansion = ""):
    if mode == "add":
        result = await addMacro(keyword, expansion, ctx.guild.id)
    elif mode == "delete":
        result = await deleteMacro(keyword, ctx.guild.id)
    if result:
        if mode == "add":
            m = await ctx.send(f"You can now use ({keyword}) in your reacts to react with {expansion}!")
        elif mode == "delete":
            m = await ctx.send(f"Deleted macro ({keyword})")
        await m.delete(delay = 5)
    else:
        m = await ctx.send(f"An error occurred :(")
        await m.delete(delay = 5)

bot.run(DISCORD_TOKEN)