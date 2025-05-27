import os
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GPU_CHANNEL_ID = int(os.getenv("GPU_CHANNEL_ID"))

# Mots-clés pour filtrer les GPU pertinents
GPU_TAGS = ["RTX", "GTX", "Radeon", "RX", "NVIDIA", "AMD"]

# Initialisation du bot Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction de scraping de GPU sur Cdiscount
def scrape_cdiscount_gpus():
    url = "https://www.cdiscount.com/informatique/cartes-graphiques/l-1076702.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    for item in soup.select(".prdtBloc"):
        title = item.select_one(".prdtBTit")
        price = item.select_one(".price")
        link = item.select_one("a")
        image = item.select_one("img")

        if not title or not price or not link:
            continue

        title_text = title.get_text(strip=True)
        if not any(tag.lower() in title_text.lower() for tag in GPU_TAGS):
            continue

        price_text = price.get_text(strip=True).replace("\u20ac", "").replace(" ", "").replace(",", ".")
        try:
            price_value = float(price_text)
        except ValueError:
            continue

        product_url = "https://www.cdiscount.com" + link["href"]
        image_url = image["src"] if image else ""

        results.append({
            "title": title_text,
            "price": price_value,
            "link": product_url,
            "image": image_url
        })

    results.sort(key=lambda x: x["price"])
    return results[:10]  # Top 10 GPU

# Fonction d'envoi des deals dans un embed
async def send_gpu_deals():
    channel = bot.get_channel(GPU_CHANNEL_ID)
    gpus = scrape_cdiscount_gpus()

    for gpu in gpus:
        embed = discord.Embed(title=gpu["title"], url=gpu["link"], description=f"**Prix :** {gpu['price']} €", color=0x00ff00)
        if gpu["image"]:
            embed.set_thumbnail(url=gpu["image"])
        embed.set_footer(text="Source : Cdiscount")
        await channel.send(embed=embed)

# Lancement automatique après le ready
@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user.name}")
    await send_gpu_deals()
    await bot.close()  # Ferme le bot une fois l'envoi fait (idéal pour Railway)

# Lancement du bot
if __name__ == "__main__":
    asyncio.run(bot.start(DISCORD_TOKEN))
