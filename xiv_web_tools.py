from functools import lru_cache, partial
import json
from multiprocessing.pool import ThreadPool
import os
import requests
import time

from dotenv import load_dotenv
import termtables as tt


from global_paths import *
from Dataclasses import Recipe, CraftingClass, Item
import xiv_tools as xivt

load_dotenv()
xivapi_key = os.getenv("xivapi_key")
TAX_RATE = 0.03


def xivapi_endpoint_url(endpoint, **kwargs):
  url = f"{XIVAPI_URL}{endpoint}?private_key={xivapi_key}"
  for k, v in kwargs.items():
    url += f"&{k}={v}"
  return url

def xivapi_search_url(name, indexes="item", columns=None):
  name = name.strip().replace(" ", "%20")
  col_str = f"&columns={','.join(columns)}" if columns else ""
  url = f"{XIVAPI_URL}/search?string={name}" +\
                           f"&indexes={indexes}" + \
                           f"{col_str}" +\
                           f"&private_key={xivapi_key}"
  return url

def universalis_current_data_url(server, item_ids, **kwargs):
  if isinstance(item_ids, str):
    item_ids = [item_ids]
  url = f"{UNIVERSALIS_URL}/{server}/{','.join(item_ids)}?"
  for k, v in kwargs.items():
    url += f"{k}={v}&"
  return url

def universalis_history_url(server, item_ids, **kwargs):
  if isinstance(item_ids, str):
    item_ids = [item_ids]
  url = f"{UNIVERSALIS_URL}/history/{server}/{','.join(item_ids)}?"
  for k, v in kwargs.items():
    url += f"{k}={v}&"
  return url

@lru_cache
def worlds():
  url = f"{UNIVERSALIS_URL}/worlds"
  data = data_from_url(url)
  if data:
    return data
  raise ValueError(f"Invalid response from {url}")

@lru_cache
def dcs():
  url = f"{UNIVERSALIS_URL}/data-centers"
  data = data_from_url(url)
  if data:
    return data
  raise ValueError(f"Invalid response from {url}")

@lru_cache
def regions():
  regions = [{"name": "North-America", "dcs": ["Aether", "Crystal", "Primal"]},
              {"name": "Europe", "dcs": ["Chaos", "Light"]},
              {"name": "Japan", "dcs": ["Elemental", "Gaia", "Mana"]},
              {"name": "Oceania", "dcs": ["Materia"]}]
  return regions

def get_scope(server):
  for world in worlds():
    if world["name"].lower() == server.lower():
      return "server"
  for dc in dcs():
    if dc["name"].lower() == server.lower():
      return "dc"
  for region in regions():
    if region["name"].lower() == server.lower():
      return "region"
  raise ValueError(f"{server} was not found in any database")

@lru_cache
def item_info_from_name(name):
  url = xivapi_search_url(name)
  data = data_from_url(url)
  if data:
    for result in data["Results"]:
      if result["Name"].lower() == name.lower():
        return Item(result)
    else:
      raise ValueError(f"'{name}' wasn't found in response for url: {url}")
  raise ValueError(f"Invalid response from url: {url}")

@lru_cache
def item_info_from_id(item_id):
  item_id = str(item_id).strip()
  url = xivapi_endpoint_url(f"/item/{item_id}", columns="Name")
  data = data_from_url(url)
  return item_info_from_name(data["Name"])

def text_from_url(url):
  response = requests.get(url)
  if response.status_code == 200:
    return response.text
  return ""

def data_from_text(text):
  return json.loads(text)

def data_from_url(url):
  text = text_from_url(url)
  if text:
    return data_from_text(text)
  return {}
  
def get_item_recipe_from_web(name):
  url = xivapi_search_url(name, indexes="Recipe")  
  data = data_from_url(url)
  if not data:
    raise ValueError(f"Invalid or no data returned from URL: {url}")
  results = data["Results"]
  recipe_columns =   [f"AmountIngredient{n}" for n in range(10)] \
                   + [f"ItemIngredient{n}TargetID" for n in range(10)] \
                   + ["AmountResult", "ClassJob.NameEnglish", 
                      "ClassJob.Abbreviation", "ClassJob.ID", "ClassJob.Icon",
                      "RecipeLevelTable.ClassJobLevel"]
  for result in results:
    if result["Name"].lower() == name.lower():
      recipe_url = xivapi_endpoint_url(result["Url"], columns=",".join(recipe_columns))
      recipe_data = data_from_url(recipe_url)
      break
  else: 
    raise ValueError(f"No recipe found for {name}")
  ingredient_amounts = [recipe_data[f"AmountIngredient{n}"] for n in range(10)]
  output_amount = recipe_data["AmountResult"]
  crafting_class = CraftingClass(recipe_data["ClassJob"]["NameEnglish"],
                                 recipe_data["ClassJob"]["Abbreviation"],
                                 recipe_data["ClassJob"]["ID"],
                                 recipe_data["ClassJob"]["Icon"])
  level = recipe_data["RecipeLevelTable"]["ClassJobLevel"]
  names = []
  amts  = []
  for i in range(len(ingredient_amounts)):
    item_id = recipe_data[f"ItemIngredient{i}TargetID"]
    if item_id == 0:
      continue
    item = item_info_from_id(item_id)
    names.append(item.name)
    amts.append(ingredient_amounts[i])
  return Recipe(name, level, crafting_class, names, amts)

def average_price(name_or_names, server, hq="null", listings=10):
  names = [name_or_names] if isinstance(name_or_names, str) else name_or_names
  item_ids = [xivt.item_id_from_name(name) for name in names]
  names = xivt.split_every(names, 99) # Universalis caps at 100 results
  item_ids = xivt.split_every(item_ids, 99)
  urls = []
  for item_id_subset in item_ids:
    urls.append(universalis_current_data_url(server, item_id_subset, listings=listings, hq=hq, entriesWithin=0))
  output = [[], []] # list of prices, list of cheapest server names
  for url, item_id_subset in zip(urls, item_ids):
    data = data_from_url(url)
    if not data:
      raise ValueError(f"Invalid response from url: {url}")
    single_item = (len(item_id_subset) == 1)
    for item_id in item_id_subset:
      if item_id == "44":
        output[0].append(0)
        output[1].append("")
        continue
      listings = data["listings"] if single_item else data["items"][item_id]["listings"]
      if not listings:
        output[0].append(0)
        output[1].append("")
        continue
      gil_list = []
      quantity_list = []
      for listing in listings:
        quantity_list.append(listing["quantity"])
        gil_list.append(listing["pricePerUnit"])
      good_ixs = xivt.filter_outliers(gil_list, f=1.2, filter_below=False)
      gil, quantity = 0, 0
      for ix in good_ixs:
        quantity += quantity_list[ix]
        gil      += quantity_list[ix]*gil_list[ix]
      cheapest_server = listings[0].get("worldName", server)
      output[0].append(round(gil/quantity))
      output[1].append(cheapest_server)
  return output

def lowest_price(name_or_names, server, hq="null"):
  return average_price(name_or_names, server, hq, listings=1)

def velocity(name_or_names, server):
  names = [name_or_names] if isinstance(name_or_names, str) else name_or_names
  item_ids = [xivt.item_id_from_name(name) for name in names]
  item_ids = xivt.split_every(item_ids, 99) # Universalis restricted to 100
  velocities = []
  for item_id_subset in item_ids:
    url = universalis_history_url(server, item_id_subset)
    data = data_from_url(url)
    if not data:
      raise ValueError(f"Invalid response from url: {url}")
    single_item = (len(item_id_subset) == 1)
    for item_id in item_id_subset:
      item_data = data if single_item else data["items"][item_id]
      velocities.append(round(float(item_data["regularSaleVelocity"])))
  return velocities

__COLLECTIBLE_RECIPE_DATA = {}
def get_item_recipe_from_local(name_or_names):
  names = [name_or_names] if isinstance(name_or_names, str) else name_or_names
  global __COLLECTIBLE_RECIPE_DATA
  if not __COLLECTIBLE_RECIPE_DATA:
    __COLLECTIBLE_RECIPE_DATA = xivt.load_json_from_local(PROCESSED_RECIPE_PATH)
  output = []
  for name in names:
    for recipe in __COLLECTIBLE_RECIPE_DATA:
      if recipe["name"].lower() == name.lower():
        output.append(recipe)
        break
    else:
      raise ValueError(f"Did not find a recipe for {name}")
  return output

def price_to_craft_collectible(name_or_names, server, listings=10):
  global __COLLECTIBLE_RECIPE_DATA
  if not __COLLECTIBLE_RECIPE_DATA:
    __COLLECTIBLE_RECIPE_DATA = xivt.load_json_from_local(PROCESSED_RECIPE_PATH)
  names = [name_or_names] if isinstance(name_or_names, str) else name_or_names
  recipes = []
  for name in names: # O(n*m)... :(
    for recipe in __COLLECTIBLE_RECIPE_DATA:
      if recipe["name"].lower() == name.lower():
        recipes.append(recipe)
        break
    else:
      raise ValueError(f"Did not find a recipe for {name}")
  ingredient_set = set()
  for recipe in recipes:
    ingredient_set.update(recipe["ingredient_names"])
  ingredient_names = list(ingredient_set)
  ingredient_prices, _ = average_price(ingredient_names, server, listings=listings)
  price_lookup = {n: p for n, p in zip(ingredient_names, ingredient_prices)}
  recipe_costs = []
  for recipe in recipes:
    cost = 0
    for name, quantity in zip(recipe["ingredient_names"], recipe["amounts"]):
      cost += price_lookup[name]*quantity
    recipe_costs.append(cost)
  return recipe_costs

__PROCESSED_COLLECTIBLE_NAMES = {}
def best_collectible_to_craft(currency, server, n_results="all", verbose=True):
  global __PROCESSED_COLLECTIBLE_NAMES
  if not __PROCESSED_COLLECTIBLE_NAMES:
    __PROCESSED_COLLECTIBLE_NAMES = xivt.load_json_from_local(PROCESSED_COLLECTIBLE_PATH)
  batch_start = time.time()
  tiers = [t for t in __PROCESSED_COLLECTIBLE_NAMES if t["currency"].lower() == currency.lower()]
  # turn into lists of names, jobs, levels, costs, gpc
  names = []
  levels = []
  rewards = []
  for tier in tiers:
    tier_size = len(tier["items"])
    names += tier["items"]
    levels += [tier["level"]]*tier_size
    rewards += [tier["reward"]]*tier_size
  num_items = len(names)
  gil_to_craft = price_to_craft_collectible(names, server)
  gpc = [round(g/r) for g, r in zip(gil_to_craft, rewards)]
  collection = [list(_) for _ in zip(names, levels, rewards, gil_to_craft, gpc)]
  collection.sort(key = lambda x: x[-1])
  if isinstance(n_results, int):
    collection = collection[:n_results]
  dt = time.time()-batch_start
  currency_abr = ".".join([s for s in currency if s.isupper()])+"."
  headers = [f"Server: {server}", "Lvl", f"{currency_abr}", "Gil/Ea", f"Gil/{currency_abr}"]
  times = ["", "", "", f"Time: {dt:.2f}s", f"s/item: {dt/num_items:.2f}"]
  table = xivt.format_column(collection, [3, 4], ["{:,}", "{:,}"]) + [times]
  table_str = tt.to_string(table, header=headers, style=tt.styles.rounded_double, alignment="llrrr")
  if verbose:
    print(table_str)
  return collection, table_str

__COMBAT_VENTURE_DATA = {}
def best_combat_ventures(server, n_results="all", v_cutoff=25, verbose=True):
  global __COMBAT_VENTURE_DATA
  if not __COMBAT_VENTURE_DATA:
    __COMBAT_VENTURE_DATA = xivt.load_json_from_local(PROCESSED_VENTURE_PATH)
  batch_start = time.time()
  names, durations, amounts, levels \
    = xivt.dict_slicer(__COMBAT_VENTURE_DATA, ["name", "duration", "amount", "level"])
  num_items = len(names)
  velocities = velocity(names, server)
  good_ixs   = [ix for ix in range(num_items) if velocities[ix] >= v_cutoff]
  names      = xivt.multi_index_slice(names, good_ixs)
  durations  = xivt.multi_index_slice(durations, good_ixs)
  amounts    = xivt.multi_index_slice(amounts, good_ixs)
  levels     = xivt.multi_index_slice(levels, good_ixs)
  velocities = xivt.multi_index_slice(velocities, good_ixs)
  prices, _  = lowest_price(names, server, hq=0)
  prices = [p*(1-TAX_RATE) for p in prices] 
  gph = [round(60*p*int(a)/int(d)) for p, a, d in zip(prices, amounts, durations)]
  collection = [list(_) for _ in zip(names, levels, gph, velocities)]
  collection.sort(key=lambda x: -x[2])
  if isinstance(n_results, int):
    collection = collection[:n_results]
  dt = time.time()-batch_start
  headers = [f"Server: {server}", "Lvl", "~Gil/Hr (Inc. Tax)", "~Sales/Day"]
  times = ["", "", f"Time: {dt:.2f}s", f"s/item: {dt/num_items:.2f}"]
  table = xivt.format_column(collection, [2, 3], ["{:,}", "{:,}"]) + [times]
  table_str = tt.to_string(table, header=headers, style=tt.styles.rounded_double, alignment="lrrr")
  if verbose:
    print(table_str)
  return collection, table_str

__SCRIP_REWARDS = {}
def best_scrip_reward(server, currency, n_results="all", v_cutoff=10, verbose=True):
  global __SCRIP_REWARDS
  if not __SCRIP_REWARDS:
    __SCRIP_REWARDS = xivt.load_json_from_local(PROCESSED_CRAFTER_SCRIP_PATH)
  batch_start = time.time()
  rewards = [r for r in __SCRIP_REWARDS if r["currency"].lower() == currency.lower()]
  names, quantities, costs, currencies = \
    xivt.dict_slicer(rewards, ["name", "quantity", "cost", "currency"])
  num_items = len(names)
  velocities = velocity(names, server)
  good_ixs = [ix for ix in range(num_items) if velocities[ix] >= v_cutoff]
  names = xivt.multi_index_slice(names, good_ixs)
  quantities = xivt.multi_index_slice(quantities, good_ixs)
  costs = xivt.multi_index_slice(costs, good_ixs)
  currencies = xivt.multi_index_slice(currencies, good_ixs)
  velocities = xivt.multi_index_slice(velocities, good_ixs)
  prices, _ = lowest_price(names, server)
  prices = [p*(1-TAX_RATE) for p in prices]
  gpc = [round(p*int(q)/float(c)) for q, c, p in zip(quantities, costs, prices)]
  collection = [list(_) for _ in zip(names, costs, prices, gpc, velocities)]
  collection.sort(key=lambda x: -x[3])
  if isinstance(n_results, int):
    collection = collection[:n_results]
  dt = time.time()-batch_start
  currency_abr = ".".join([s for s in currency if s.isupper()])+"."
  headers=[f"Server: {server}", currency_abr, "Gil/Ea (Inc. Tax)", f"Gil/{currency_abr}", "~Sales/Day"]
  times = ["", "", "", f"Time: {dt:.2f}s", f"s/item: {dt/num_items:.2f}"]
  table = xivt.format_column(collection, [2, 4], ["{:,}", "{:,}"]) + [times]
  table_str = tt.to_string(table, header=headers, style=tt.styles.rounded_double, alignment="llrrr")
  if verbose:
    print(table_str)
  return collection, table_str

def best_equip_for_slot(slot, ilvl, job, ornate=False):
  job = job.upper()
  filters = [f"LevelItem<={ilvl}", f"ClassJobCategory.{job}=1", "IsUntradable=0", f"EquipSlotCategory.{slot}=1"]
  limit = 2 if slot == "Body" else 1
  url = xivapi_endpoint_url("/search", filters=",".join(filters), sort_field="LevelItem", sort_order="desc", limit=limit)
  data = data_from_url(url)
  results = data["Results"]
  if not results:
    return ""
  if slot == "Body":
    for result in results:
      if ornate and "Ornate" in result["Name"]:
        return result["Name"]
      if not ornate and "Ornate" not in result["Name"]:
        return result["Name"]
    return ""
  else:
    return results[0]["Name"]

def best_server_gearset_items(ilvl, job, server, hq="true", verbose=True):
  batch_start = time.time()
  slot_names = ["MainHand", "OffHand", "Head", "Body", "Gloves", "Legs",
                "Feet", "Ears", "Neck", "Wrists", "FingerR"]
  p = ThreadPool(6)
  worker = partial(best_equip_for_slot, ilvl=ilvl, job=job)
  equip_names = p.map(worker, slot_names)
  p.close()
  p.join()
  slot_names[-1] = "Ring"
  ornate_body = best_equip_for_slot("Body", ilvl, job, ornate=True)
  if ornate_body:
    slot_names.append("OrnateBody")
    equip_names.append(ornate_body)
  best_prices, best_servers = lowest_price(equip_names, server, hq=hq)
  collection = [list(_) for _ in zip(slot_names, equip_names, best_prices, best_servers)]
  num_items = len(equip_names)
  dt = time.time()-batch_start
  
  headers = ["Slot", f"{job} Gear (ilvl<={ilvl})", "Price (HQ)", "Server"]
  price = sum([(2 if c[0]=="Ring" else 1)*c[2] for c in collection if c[0] != "OrnateBody"])
  price_row = ["", "Total Price (Excl. Ornate)", price, ""]
  time_row = ["", "", f"Time: {dt:.2f}s", f"s/item: {0 if not num_items else dt/num_items:.2f}"]
  table = xivt.format_column(collection+[price_row], [2], ["{:,}"]) + [time_row]
  table_str = tt.to_string(table, header=headers, style=tt.styles.rounded_double, alignment="llrl")
  if verbose:
    print(table_str)
  return collection, table_str

def __best_equip_for_slot_helper(job, ilvl, slot): # Re-ordering args for pool
  return best_equip_for_slot(slot, ilvl, job) 

def best_server_full_crafter_gatherer_set(ilvl, server, crafter_or_gatherer, hq="true", sort_by_server=False, verbose=True):
  crafters = ["CRP", "BSM", "ARM", "GSM", "LTW", "WVR", "ALC", "CUL"]
  gatherers = ["MIN", "BTN", "FSH"]
  if crafter_or_gatherer.lower().strip() == "crafter":
    job_list = crafters
    generic_gear, _ = best_server_gearset_items(ilvl, crafters[0], server, hq, verbose=False)
  elif crafter_or_gatherer.lower().strip() == "gatherer":
    job_list = gatherers
    generic_gear, _ = best_server_gearset_items(ilvl, gatherers[0], server, hq, verbose=False)
  elif crafter_or_gatherer.lower().strip() == "all":
    job_list = crafters + gatherers
    c_gear, _ = best_server_gearset_items(ilvl, crafters[0], server, hq, verbose=False)
    g_gear, _ = best_server_gearset_items(ilvl, gatherers[0], server, hq, verbose=False)
    generic_gear = c_gear + g_gear
  else:
    return {}
  batch_start = time.time()
  # generic_gear, _ = best_server_gearset_items(ilvl, job_list[0], server, hq, verbose=False)
  mainhands = [generic_gear.pop(0)[1]]
  offhands =  [generic_gear.pop(0)[1]]
  hand_slotnames = [f"{job_list[0]} MainHand", f"{job_list[0]} OffHand"]
  main_pool = ThreadPool(len(job_list)-1)
  main_worker = partial(__best_equip_for_slot_helper, ilvl=ilvl, slot="MainHand")
  mainhands += main_pool.map(main_worker, job_list[1:])
  main_pool.close()
  main_pool.join()
  off_pool = ThreadPool(len(job_list)-1)
  off_worker = partial(__best_equip_for_slot_helper, ilvl=ilvl, slot="OffHand")
  offhands += off_pool.map(off_worker, job_list[1:])
  off_pool.close()
  off_pool.join()
  for job in job_list[1:]:
    hand_slotnames += [f"{job} MainHand", f"{job} OffHand"]
  allhands_names = xivt.weave_lists(mainhands, offhands)
  allhands_prices, allhands_servers = lowest_price(allhands_names, server, hq)
  hands_collection = [list(_) for _ in zip(hand_slotnames, allhands_names, allhands_prices, allhands_servers)]
  collection = hands_collection + generic_gear
  if sort_by_server:
    collection.sort(key=lambda x: x[3])
  dt = time.time() - batch_start
  num_items = len(collection)
  headers = ["Slot", f"{crafter_or_gatherer.capitalize()} Gear (ilvl<={ilvl})", "Price (HQ)", "Server"]
  price = sum([(2 if c[0]=="Ring" else 1)*c[2] for c in collection if c[0] != "OrnateBody"])
  price_row = ["", "Total Price", price, ""]
  time_row = ["", "", f"Time: {dt:.2f}s", f"s/item: {0 if not num_items else dt/num_items:.2f}"]
  table = xivt.format_column(collection+[price_row], [2], ["{:,}"]) + [time_row]
  table_str = tt.to_string(table, header=headers, style=tt.styles.rounded_double, alignment="llrl")
  if verbose:
    print(table_str)
  return collection, table_str

def _bri_ilvl_search(min_ilvl):
  filters = [f"LevelItem>={min_ilvl}", "IsUntradable=0", "EquipSlotCategory!"]
  url = xivapi_endpoint_url("/search", filters=",".join(filters), sort_field="LevelItem", sort_order="desc", limit=500)
  data = data_from_url(url)
  results = data["Results"]
  return xivt.dict_slicer(results, ["Name", "ID"])

def _bri_materia_search():
  tiers_of_interest = ["VII", "VIII", "IX", "X"]
  m = ["Savage Aim Materia {}", "Savage Might Materia {}", 
       "Heavens' Eye Materia {}", "Quickarm Materia {}" ,
       "Quicktongue Materia {}", "Battledance Materia {}",
       "Piety Materia {}", "Craftsman's Command Materia {}", 
       "Craftsman's Cunning Materia {}", "Gatherer's Grasp Materia {}",
       "Craftsman's Competence Materia {}", "Gatherer's Guerdon Materia {}",
       "Gatherer's Guile Materia {}"]
  names = []
  for materia in m:
    for tier in tiers_of_interest:
      names.append(materia.format(tier))
  item_ids = [xivt.item_id_from_name(name) for name in names]
  return [names, item_ids]

def _bri_differences(home, foreign):
  return [round(h*(1-TAX_RATE)-f) for h,f in zip(home, foreign)]

def _bri_helper(names, item_ids, home_world, dc_or_region, n_results="all"):
  home_price, _ = lowest_price(names, home_world)
  foreign_price, best_server = lowest_price(names, dc_or_region)
  delta = _bri_differences(home_price, foreign_price)
  collection = [list(_) for _ in zip(names, home_price, foreign_price, delta, best_server)]
  collection = list(filter(lambda x: x[3]>0, collection))
  collection.sort(key=lambda x: -x[3])
  if isinstance(n_results, int):
    collection = collection[:n_results]
  return collection

def _bri_finisher(collection, dt, home_world, verbose=True):
  num_items = len(collection)
  headers = [f"Home World: {home_world}", "Home Price", "Foreign Price", "Profit (Inc. Tax)", "Lowest Server"]
  time_row = ["", "", "", f"Time: {dt:.2f}s", f"s/item: {0 if not num_items else dt/num_items:.2f}"]
  table = xivt.format_column(collection, [1, 2, 3], ["{:,}", "{:,}", "{:,}"]) + [time_row]
  table_str = tt.to_string(table, header=headers, style=tt.styles.rounded_double, alignment="lrrrl")
  if verbose:
    print(table_str)
  return collection, table_str
  return

def _bri_ilvl(home_world, dc_or_region, min_ilvl=560, n_results="all", verbose=True):
  batch_start = time.time()
  item_names_ilvl, item_ids_ilvl = _bri_ilvl_search(min_ilvl)
  collection_ilvl = _bri_helper(item_names_ilvl, item_ids_ilvl, home_world, dc_or_region, n_results)
  dt = time.time() - batch_start
  return _bri_finisher(collection_ilvl, dt, home_world, verbose)

def _bri_materia(home_world, dc_or_region, n_results="all", verbose=True):
  batch_start = time.time()
  item_names_materia, item_ids_materia = _bri_materia_search()
  collection_materia = _bri_helper(item_names_materia, item_ids_materia, home_world, dc_or_region, n_results)
  dt = time.time() - batch_start
  return _bri_finisher(collection_materia, dt, home_world, verbose)

def best_reselling_items(home_world, dc_or_region, min_ilvl=560, n_results="all", verbose=True):
  _bri_ilvl(home_world, dc_or_region, min_ilvl, n_results, verbose)
  _bri_materia(home_world, dc_or_region, n_results, verbose)
  return

if __name__ == "__main__":
  pass



