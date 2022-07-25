import itertools
import logging
import os
import random

import discord
from dotenv import load_dotenv
from discord.ext import commands

import xiv_web_tools as xivwt
import xiv_tools as xivt

COMMAND_LEVEL = 25
logging.addLevelName(COMMAND_LEVEL, "COMMAND")
assert logging.getLevelName(COMMAND_LEVEL) == "COMMAND"

def COMMAND(self, msg, *args, **kwargs):
  return self._log(25, msg, *args, **kwargs)
logging.Logger.COMMAND = COMMAND
logging.basicConfig(level=25)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix="$")

BLANK = "<:01Transparent:997441264666562572>"
LVL = "<:13Lvl:997448285021286430>"
GIL = "<:16Gil:1000682140767367279>"
def number_to_emote(n):
  d = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", 
       "4": ":four:", "5": ":five:", "6": ":six:", "7": ":seven:", 
       "8": ":eight:", "9": ":nine:", ".": ".", ",": ","}
  return "".join([d[digit] for digit in str(n)])

def job_icon(job_abbr):
  # CRP BSM ARM GSM LTW WVR ALC CUL
  d = {"GLA": "https://xivapi.com/cj/companion/gladiator.png",
       "PLD": "https://xivapi.com/cj/companion/paladin.png",
       "MRD": "https://xivapi.com/cj/companion/marauder.png",
       "WAR": "https://xivapi.com/cj/companion/warrior.png",
       "DRK": "https://xivapi.com/cj/companion/darkknight.png",
       "GNB": "https://xivapi.com/cj/companion/gunbreaker.png",
       "PGL": "https://xivapi.com/cj/companion/pugilist.png",
       "MNK": "https://xivapi.com/cj/companion/monk.png",
       "LNC": "https://xivapi.com/cj/companion/lancer.png",
       "DRG": "https://xivapi.com/cj/companion/dragoon.png",
       "ROG": "https://xivapi.com/cj/companion/rogue.png",
       "NIN": "https://xivapi.com/cj/companion/ninja.png",
       "SAM": "https://xivapi.com/cj/companion/samurai.png",
       "RPR": "https://xivapi.com/cj/companion/reaper.png",
       "CNJ": "https://xivapi.com/cj/companion/conjurer.png",
       "WHM": "https://xivapi.com/cj/companion/whitemage.png",
       "SCH": "https://xivapi.com/cj/companion/scholar.png",
       "AST": "https://xivapi.com/cj/companion/astrologian.png",
       "SGE": "https://xivapi.com/cj/companion/sage.png",
       "ARC": "https://xivapi.com/cj/companion/archer.png",
       "BRD": "https://xivapi.com/cj/companion/bard.png",
       "MCH": "https://xivapi.com/cj/companion/machinist.png",
       "DNC": "https://xivapi.com/cj/companion/dancer.png",
       "THM": "https://xivapi.com/cj/companion/thaumaturge.png",
       "BLM": "https://xivapi.com/cj/companion/blackmage.png",
       "ACN": "https://xivapi.com/cj/companion/arcanist.png",
       "SMN": "https://xivapi.com/cj/companion/summoner.png",
       "RDM": "https://xivapi.com/cj/companion/redmage.png",
       "BLU": "https://xivapi.com/cj/companion/bluemage.png",
       "CRP": "https://xivapi.com/cj/companion/carpenter.png",
       "BSM": "https://xivapi.com/cj/companion/blacksmith.png",
       "ARM": "https://xivapi.com/cj/companion/armorer.png",
       "GSM": "https://xivapi.com/cj/companion/goldsmith.png",
       "LTW": "https://xivapi.com/cj/companion/leatherworker.png",
       "WVR": "https://xivapi.com/cj/companion/weaver.png",
       "ALC": "https://xivapi.com/cj/companion/alchemist.png",
       "CUL": "https://xivapi.com/cj/companion/culinarian.png",
       "MIN": "https://xivapi.com/cj/companion/miner.png",
       "BTN": "https://xivapi.com/cj/companion/botanist.png",
       "FSH": "https://xivapi.com/cj/companion/fisher.png"}
  return d.get(job_abbr.upper(), "https://xivapi.com/cj/companion/none.png")

def slot_emote(slot):
  # d = {"MainHand": ":crossed_swords:", "OffHand": ":shield:",
  #      "Head": ":billed_cap:", "Body": ":running_shirt_with_sash:",
  #      "Gloves": ":open_hands:", "Legs": ":jeans:", "Feet": ":boot:",
  #      "Ears": ":ear_with_hearing_aid:", "Neck": ":prayer_beads:",
  #      "Wrists": ":prayer_beads:", "Ring": ":ring:"}
  d = {"MainHand": "<:02Sword:997445338602418176>", 
       "OffHand": ":shield:",
       "Head": "<:03Helmet:997445339634225174>", 
       "Body": "<:04Armor:997445340619878440>",
       "Gloves": "<:05Gloves:997445341571993731>", 
       "Legs": "<:06Pants:997445342440206387>",
       "Feet": "<:07Shoes:997445343543296020>",
       "Ears": "<:08Earrings:997445344650604594>", 
       "Neck": "<:09Necklace:997445345871138897>",
       "Wrists": "<:10Bracelet:997445346781319178>", 
       "Ring": ":ring:"}
  
  return d.get(slot, ":question:")

@bot.event
async def on_ready():
  logging.log(COMMAND_LEVEL, " >>> READY <<< ")
  return

@bot.event
async def on_command(ctx):
  logging.log(COMMAND_LEVEL, f"{ctx.author} used ${ctx.command} {' '.join(ctx.args[1:])} in {'DM' if not ctx.guild else ctx.guild.name}")
  return

@bot.event
async def on_command_error(ctx, err):
  logging.error(f"{ctx.author} used {ctx.command} and got the error: {str(err)}")
  if isinstance(err, commands.CommandNotFound):
    await ctx.reply(":warning: **Invalid command. Try using** `$help` **to see a list of available commands.**")
  elif isinstance(err, commands.MissingRequiredArgument):
    await ctx.reply(f":warning: **Please pass in all arguments.** {str(err)}")
  elif isinstance(err, commands.MissingPermissions):
    await ctx.reply(":warning: **You do not have the requirements or permissions for this command.**")
  else:
    await ctx.reply(f":warning: Oopsy Woopsy :( Unhandled Error:\n{str(err)}")
  return

async def check_server(ctx, server_region_dc, mode):
  acceptable_names = []
  acceptable_categories = []
  if mode & 0b001: # Can be a  'server' (not region or dc)
    acceptable_categories.append("Server")
    acceptable_names += xivt.dict_slicer(xivwt.worlds(), ["name"])[0]
  if mode & 0b010: # Can be a 'dc' (not server or region)
    acceptable_categories.append("DC")
    acceptable_names += xivt.dict_slicer(xivwt.dcs(), ["name"])[0]
  if mode & 0b100: # Can be a 'region' (not server or dc)
    acceptable_categories.append("Region")
    acceptable_names += xivt.dict_slicer(xivwt.regions(), ["name"])[0]
  return server_region_dc.lower() in [s.lower() for s in acceptable_names]

def embed_skeleton(ctx, title, description, thumbnail):
  embed = discord.Embed(title=title,
                        description=description,
                        color=discord.Color.random(),
                        timestamp=ctx.message.created_at)
  embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
  embed.set_thumbnail(url=thumbnail)
  return embed

@bot.command(help="Finds the most profitable combat ventures in a world.", brief="Usage: $ventures World")
async def ventures(ctx, server):
  if not await check_server(ctx, server, mode=0b001):
    return await ctx.reply(f":warning: Supplied world must be a valid world name and not a DC or region. Got: {server}")
  embed = embed_skeleton(ctx=ctx,
                         title="Best Combat Ventures",
                         description=f"Finding best combat ventures in {server}...",
                         thumbnail="https://xivapi.com/img-misc/payment_currency_coin.png")
  msg = await ctx.reply(embed=embed)
  best_ventures_table, _ = xivwt.best_combat_ventures(server, n_results=10, v_cutoff=40, verbose=False)
  embed.description = ""
  for ix, (name, lvl, gph, velocity) in enumerate(best_ventures_table, start=1):
    embed.add_field(name=f"{ix:2d}. {name} ({LVL} {lvl})", value=f"{BLANK}➥Gil/Hour: {gph:,}\n{BLANK}{BLANK}➥Sales/Day: {velocity:,}", inline=False)
  return await msg.edit(embed=embed, content=f"Best combat ventures in {server}:")

@bot.command(help="Finds the most profitable collectible to craft in a "\
                + "world, DC, or region given a currency. Currency can be "\
                  "either 'White' or 'Purple' (scrips).",
             brief="Usage: $collectibles Currency Server")
async def collectibles(ctx, currency, server):
  if currency.lower() == "white":
    thumbnail = "https://ffxiv.gamerescape.com/w/images/1/19/White_Crafters%27_Scrip_Icon.png"
    cur = "White Crafters' Scrips"
  elif currency.lower() == "purple":
    thumbnail = "https://ffxiv.gamerescape.com/w/images/e/ee/Purple_Crafters%27_Scrip_Icon.png"
    cur = "Purple Crafters' Scrips"
  else:
    return await ctx.reply(f":warning: 'Currency' must be either 'White' or 'Purple'. Got: {currency}")
  if not await check_server(ctx, server, mode=0b111):
    return await ctx.reply(f":warning: Supplied server must be a valid world, DC, or region name. Got: {server}")
  embed = embed_skeleton(ctx=ctx,
                         title="Best Crafting Collectibles",
                         description=f"Finding best collectibles to craft in {server}...",
                         thumbnail=thumbnail)
  msg = await ctx.reply(embed=embed)
  best_collectible_table, _ = xivwt.best_collectible_to_craft(cur, server, n_results=10, verbose=False)
  embed.description = ""
  for ix, (name, lvl, reward, g2c, gpc) in enumerate(best_collectible_table, start=1):
    recipe = xivwt.get_item_recipe_from_local(name)[0]
    crafter = recipe["crafting_class"]
    recipe_lines = f"\n> **__Recipe__** (Cost: {g2c:,} -- Gil/Scrip: {gpc:,})\n>   " + "\n>   ".join([f"{number_to_emote(q)} x {i}" for q,i in zip(recipe["amounts"], recipe["ingredient_names"])])
    embed.add_field(name=f"{ix:2d}. {name} ({crafter} Lvl {lvl})", value=recipe_lines, inline=False)
  return await msg.edit(embed=embed, content=f"Best collectibles to craft in {server}")

async def _gearset_display(ctx, collection, embed):
  embed.description = ""
  total_cost = 0
  for slot, name, price, best_world in collection:
    if not name:
      continue
    if "Ornate" not in slot:
      total_cost += price
    embed.add_field(name=f"{slot_emote(slot)} {name} ({slot})", value=f"{BLANK}{BLANK}➥Price: {price:,} ({best_world})", inline=False)
  cost_str = f"{total_cost:,}"
  embed.title += f"\nTotal Cost: {number_to_emote(cost_str)} {GIL}"
  return embed

@bot.command(help="Finds the cheapest world to buy a gearset in a world, "\
                + "DC, or region given a maximum item level and abbreviated "\
                + "job name (like SMN). Ex: $gearset SMN 580 Primal",
             brief="Usage: $gearset JobAbbr ilvl Server")
async def gearset(ctx, job, ilvl, server):
  if len(job) != 3:
    return await ctx.reply(f":warning: Supplied job must be a job's abbreviation (like SMN). Got: {job}")
  if not ilvl.isdigit():
    return await ctx.reply(f":warning: Supplied ilvl must be a positive integer. Got: {ilvl}")
  if not await check_server(ctx, server, mode=0b111):
    return await ctx.reply(f":warning: Supplied server must be a valid world, DC, or region name. Got: {server}")
  embed = embed_skeleton(ctx=ctx,
                         title=f"{job} Gear (ilvl <= {ilvl})",
                         description=f"Finding cheapest item prices in {server}...",
                         thumbnail=job_icon(job))
  msg = await ctx.reply(embed=embed)
  best_gearset, _ = xivwt.best_server_gearset_items(ilvl, job, server, verbose=False)
  embed = await _gearset_display(ctx, best_gearset, embed)
  return await msg.edit(embed=embed, content="Cheapest item prices")

@bot.command(help="Finds the best scrip rewards on a server for a given scrip"\
                  "color. Ex: $scrips White Excalibur",
             brief="Usage: $scrips Currency World")
async def scrips(ctx, currency, server):
  if currency.lower() == "white":
    thumbnail = "https://ffxiv.gamerescape.com/w/images/1/19/White_Crafters%27_Scrip_Icon.png"
    cur = "White Crafters' Scrip"
    emoji = "<:14WhiteScrip:997658533254406215>"
  elif currency.lower() == "purple":
    thumbnail = "https://ffxiv.gamerescape.com/w/images/e/ee/Purple_Crafters%27_Scrip_Icon.png"
    cur = "Purple Crafters' Scrip"
    emoji = "<:15PurpleScrip:997658534844039178>"
  else:
    return await ctx.reply(f":warning: 'Currency' must be either 'White' or 'Purple'. Got: {currency}")
  if not await check_server(ctx, server, mode=0b001):
    return await ctx.reply(f":warning: Supplied world must be a valid world and not a DC or region. Got: {server}")
  embed = embed_skeleton(ctx=ctx,
                         title=f"Best {cur} Rewards in {server}",
                         description=f"Finding best scrip rewards in {server}...",
                         thumbnail=thumbnail)
  msg = await ctx.reply(embed=embed)
  best_rewards, _ = xivwt.best_scrip_reward(server, cur, n_results=10, verbose=False)
  
  for ix, (name, cost, price, gpc, velocity) in enumerate(best_rewards, start=1):
    embed.add_field(name=f"{ix}. {name} ({cost} {emoji})", value=f"{BLANK}➥Price: {round(price):,} (Gil/Scrip: {gpc:,})\n{BLANK}{BLANK}➥Saless/Day: {velocity:,}", inline=False)
  embed.description=""
  await msg.edit(embed=embed)
  return

@bot.command(help="Finds the best items to buy on other servers and resell on"\
                  " the given home world for a profit. Ex: $resell Excalibur "\
                  "Primal equips",
             brief="Usage: $resell World Server Mode (Mode is 'equips' or 'materia')")
async def resell(ctx, home, dc_or_region, mode, n_results="all"):
  mode = mode.strip().lower()
  if mode.lower() == "equips":
    func = xivwt._bri_ilvl
    emoji = "<:02Sword:997445338602418176>"
  elif mode.lower() == "materia":
    func = xivwt._bri_materia
    emoji = "<:17MateriaX:1000685607305093151>"
  else:
    return await ctx.reply(f":warning: Supplied mode must be either 'equips' or 'materia'. Got {mode}")
  if not await check_server(ctx, home, 0b001):
    return await ctx.reply(f":warning: Supplied home world must be a valid world and not a DC or region. Got: {home}")
  if not await check_server(ctx, dc_or_region, 0b111):
    return await ctx.reply(f":warning: Supplied server must be a valid world, DC, or region name. Got: {dc_or_region}")
  
  embed = embed_skeleton(ctx=ctx,
                         title=f"Best {emoji} {mode} {emoji} to buy from {dc_or_region} and sell on {home}",
                         description=f"Finding best resellable {emoji} {mode} {emoji} from {dc_or_region}...",
                         thumbnail="https://ffxiv.gamerescape.com/w/images/2/22/Gil_Icon.png")
  msg = await ctx.reply(embed=embed)
  collection, _ = func(home, dc_or_region, n_results=10, verbose=False)
  for ix, (name, home_price, foreign_price, diff, best_server) in enumerate(collection, start=1):
    embed.add_field(name=f"{ix}. {name} (Profit: {diff:,} {GIL})", value=f"{BLANK}➥Buy from {best_server} for: {foreign_price:,}\n{BLANK}➥Sell for: {home_price:,}", inline=False)
  embed.description = ""
  await msg.edit(embed=embed)
  return

async def _crafter_gatherer_set(ctx, ilvl, server, crafter_or_gatherer):
  if not await check_server(ctx, server, 0b111):
    return await ctx.reply(f":warning: Supplied server must be a valid world, DC, or region name. Got: {server}")
  if crafter_or_gatherer == "all":
    title_substring = "Crafter + Gatherer"
  else:
    title_substring = crafter_or_gatherer.capitalize()
  embed = embed_skeleton(ctx=ctx,
                         title=f"{title_substring} Gear (ilvl <= {ilvl})",
                         description=f"Finding cheapest {title_substring} prices in {server}...",
                         thumbnail="https://ffxiv.consolegameswiki.com/mediawiki/images/2/25/Trained_Finesse.png")
  msg = await ctx.reply(embed=embed)
  best_gearset, _ = xivwt.best_server_full_crafter_gatherer_set(ilvl, server, crafter_or_gatherer, sort_by_server=True, verbose=False)
  x = itertools.groupby(best_gearset, key=lambda x: x[3])
  total_cost = 0
  for best_server, group in x:
    if not best_server:
      continue
    values = []
    field_value = ""
    value_length = 0
    for slot, name, price, _ in group:
      temp = f"{BLANK}➥{name} ({slot.replace('Hand', '')}) - {price:,} {GIL}\n"
      if value_length + len(temp) >= 1000:
        values.append(field_value)
        field_value = ""
        value_length = 0
      value_length += len(temp)
      field_value += temp
      total_cost += (2 if slot == "Ring" else 1)*price
    if field_value:
      values.append(field_value)
    for ix, val in enumerate(values, start=1):
      embed.add_field(name=f"{best_server} ({ix}/{len(values)})", value=val, inline=False)
  cost_str = f"{total_cost:,}"
  embed.title += f"\nTotal Cost: {number_to_emote(cost_str)} {GIL}"
  embed.description = ""
  return await msg.edit(embed=embed, content="Cheapest item prices")

@bot.command(help="Finds the best worlds to buy an entire crafter set and "\
                  "includes primary/secondary tools for all crafter jobs at "\
                  "an item level less than or equal to the supplied ilvl. " \
                  "Example: $crafter_set 600 Primal", 
             brief="Usage: $crafter_set ilvl Server")
async def crafter_set(ctx, ilvl, server):
  return await _crafter_gatherer_set(ctx, ilvl, server, "crafter")

@bot.command(help="Finds the best worlds to buy an entire gatherer set and "\
                  "includes primary/secondary tools for all gatherer jobs at "\
                  "an item level less than or equal to the supplied ilvl. " \
                  "Example: $gatherer_set 600 Primal", 
             brief="Usage: $gatherer_set ilvl Server")
async def gatherer_set(ctx, ilvl, server):
  return await _crafter_gatherer_set(ctx, ilvl, server, "gatherer")

@bot.command(help="Finds the best worlds to buy an entire crafter/gatherer "\
                  "set and includes primary/secondary tools for all "\
                  "jobs at an item level less than or equal to the supplied "\
                  "ilvl. Example: $crafter_gatherer_set 600 Primal", 
             brief="Usage: $crafter_gatherer_set ilvl Server")
async def crafter_gatherer_set(ctx, ilvl, server):
  return await _crafter_gatherer_set(ctx, ilvl, server, "all")


@bot.command(help="NAX")
async def pee(ctx):
  return await ctx.reply("NAX")

@bot.command(help="woo")
async def a(ctx):
  links = ["https://i.imgur.com/EmkUgB6.png", "https://i.imgur.com/bM550fc.png",
           "https://i.imgur.com/OFtgeZE.png", "https://i.imgur.com/XMuIUjd.png",
           "https://i.imgur.com/UpfSKzr.png", "https://i.imgur.com/c018qUf.png",
           "https://i.imgur.com/AewXvI0g.png", "https://i.imgur.com/3jxPr7P.png",
           "https://i.imgur.com/alaMNPW.png", "https://i.imgur.com/p6X6p1N.png",
           "https://i.imgur.com/abtr3Bc.png", "https://i.imgur.com/UY2Jb5w.png",
           "https://i.imgur.com/9z7C7tE.png", "https://i.imgur.com/euDuJKA.png",
           "https://i.imgur.com/Fz6Zq0q.png", "https://i.imgur.com/8ENvaQr.png",
           "https://i.imgur.com/lVVfpfr.png", "https://i.imgur.com/yq2gV8I.png",
           "https://i.imgur.com/BawHPue.png", "https://i.imgur.com/hR1dnF3.png",
           "https://i.imgur.com/D381ZR7.png", "https://i.imgur.com/LIfDOpP.png",
           "https://i.imgur.com/kvfZm6J.png", "https://i.imgur.com/kzwJtf1.png",
           "https://i.imgur.com/8fzSrj4.png", "https://i.imgur.com/JEDz1ep.png",
           ]
  
  return await ctx.reply(f"AWOO\n{random.choice(links)}")



if __name__ == "__main__":  
  bot.run(DISCORD_TOKEN)