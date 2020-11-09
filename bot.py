import os
from discord.ext import commands
import mysql.connector
from dotenv import load_dotenv

async def getPrefijo(bot, message):
    prefijo = "$"
    try:
        cursor = cnx.cursor()
        datos = (message.guild.id, )
        cursor.execute("SELECT prefijo FROM guilds WHERE discord_id = %s", datos)
        prefijo = cursor.fetchone() or "$"
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

@bot.command(name = "react", help = "Reacciona al ultimo mensaje con palabras en emoji")
async def emojiReact(ctx, *, message: str):
    canal = ctx.channel
    mensajes = await canal.history(limit = 2).flatten()
    veces = {a: 0 for a in inventario.keys()}
    ultimo = mensajes[1]
    texto = message.replace(" ", "").upper()
    await ctx.message.delete()
    reacciones = []
    alcanzan = True
    try:
        for c in texto:
            if veces[c] >= len(inventario[c]):
                alcanzan = False
                break
            reacciones.append(inventario[c][veces[c]])
            veces[c] += 1
        if not alcanzan:
            m = await canal.send("No hay suficientes emojis para escribir eso!")
            await m.delete(delay = 5)
        else:
            for c in reacciones:
                await ultimo.add_reaction(c)
    except Exception as e:
        m = await canal.send("Ocurrio un error")
        print(e)

@bot.command(name = "prefix", help = "Cambia el prefijo del bot, si no se pasa nada vuelve a $")
async def changePrefix(ctx, *, prefix = "$"):
    result = await setPrefijo(ctx.guild.id, prefix)
    if result:
        m = await ctx.send(f"Se cambio el prefijo a {prefix}")
        await m.delete(delay = 5)
    else:
        m = await ctx.send(f"No se pudo cambiar el prefijo :(")
        await m.delete(delay = 5)

bot.run(DISCORD_TOKEN)