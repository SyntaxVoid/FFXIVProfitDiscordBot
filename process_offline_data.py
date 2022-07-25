import json
import re
import os.path as op
from multiprocessing.pool import ThreadPool

from global_paths import *
import xiv_tools as xivt
import xiv_web_tools as xivwt


def get_list_of_match_groups(re_str, data_str, group_indices):
  matches = re.finditer(re_str, data_str, re.MULTILINE)
  if isinstance(group_indices, int):
    group_indices = [group_indices]
  output = [[] for _ in group_indices]
  for match_num, match in enumerate(matches):
    for grp_ix, grp in enumerate(group_indices):
      output[grp_ix].append(match.group(grp))
  if len(group_indices) == 1:
    return output[0]
  return output

def lists_to_dicts(lists, key_names):
  list_size = len(lists[0])
  if not all([len(a) == list_size for a in lists]):
    raise ValueError("Lists are not the same size")
  output = []
  for ix in range(list_size):
    temp = {}
    for key_ix, key in enumerate(key_names):
      temp[key] = lists[key_ix][ix]
    output.append(temp)
  return output

def process_venture_html(input_file_name, output_file_name=""):
  print(f"Processing venture table from {input_file_name}...")
  r1 = r"title=\"([^.><]*)\">(\1)<\/a><\/td>\n<td>(\d+)"
  r2 = r"<td>(\d+)<\/td>\n<td align=\"left\">"
  r3 = r"<td>(\d+[mh])<\/td>"
  data = xivt.read_all(input_file_name)
  name_list, amount_list = get_list_of_match_groups(r1, data, [1, 3])
  level_list = get_list_of_match_groups(r2, data, [1])
  duration_list = get_list_of_match_groups(r3, data, [1])
  if (len(name_list) != len(amount_list) != len(level_list) != len(duration_list)):
    raise ValueError("Bad input - Lists have un-equal lengths")
  for i in range(len(duration_list)):
    if duration_list[i][-1] == "h":
      duration_list[i] = str(int(duration_list[i][:-1])*60)
    elif duration_list[i][-1] == "m":
      duration_list[i] = duration_list[i][:-1]
  output = lists_to_dicts([name_list, amount_list, level_list, duration_list],
                          ["name"   , "amount"   , "level"   , "duration"])
  print("  Done!")
  if output_file_name:
    xivt.write_json_to_file(output, output_file_name)
    print(f"  Written to {output_file_name}")
  return output

def process_collectible_html(input_file_name, output_file_name=""):
  print(f"Processing collectible table from {input_file_name}...")
  data = xivt.read_all(input_file_name)
  r1 = r"\"(Rarefied [^.><]*)\""
  items = get_list_of_match_groups(r1, data, [1])
  levels = [90, 89, 87, 85, 83, 81, 80, 78, 76, 74, 72, 
            70, 68, 66, 64, 62, 60, 58, 56, 54, 52, 50]
  rewards = [144, 198, 171, 157, 142, 128, 114, 99, 85, 82, 
             68, 54, 54, 54, 54, 54, 54, 54, 54, 54, 54, 54]
  num_tiers = len(levels)
  tier_size = 8
  tiered_items = xivt.split_every(items, tier_size)
  currency = ["Purple Crafters' Scrips"] + ["White Crafters' Scrips"]*(num_tiers-1)
  output = lists_to_dicts([levels, rewards, currency, tiered_items],
                          ["level", "reward", "currency", "items"])
  print("  Done!")
  if output_file_name:
    xivt.write_json_to_file(output, output_file_name)
    print(f"  Written to {output_file_name}")
  return output

def process_collectible_recipes(input_file_name, output_file_name=""):
  print(f"Processing collectible recipe table from {input_file_name}...")
  data = xivt.read_all(input_file_name)
  data_dict = json.loads(data)
  output = []
  num_tiers = len(data_dict)
  for ix, tier in enumerate(data_dict, start=1):
    print(f"  Processing recipes for tier {ix}/{num_tiers}...")
    temp = []
    num_items = len(tier["items"])
    p = ThreadPool(8)
    output += p.map(xivwt.get_item_recipe_from_web, tier["items"])
    p.close()
    p.join()
  for ix in range(len(output)):
    output[ix] = output[ix]._as_dict()
  print("  Done!")
  if output_file_name:
    xivt.write_json_to_file(output, output_file_name)
    print(f"  Written to {output_file_name}")
  return output

def full_process_collectible_recipes(raw_collectible_html, output_collectible_file, output_recipe_file):
  process_collectible_html(raw_collectible_html, output_collectible_file)
  return process_collectible_recipes(output_collectible_file, output_recipe_file)

def process_crafter_scrip_rewards(input_file_name, output_file_name=""):
  print(f"Processing crafter scrip reward table from {input_file_name}...")
  r1 = r"item=(\d+) (.+)\|cost=(\d+) (.+)}}"
  data = xivt.read_all(input_file_name)
  matches = get_list_of_match_groups(r1, data, [2, 1, 3, 4])
  output = lists_to_dicts(matches, ["name", "quantity", "cost", "currency"])
  print("  Done!")
  if output_file_name:
    xivt.write_json_to_file(output, output_file_name)
    print(f"  Written to {output_file_name}")
  return output

if __name__ == "__main__":
  process_venture_html(RAW_VENTURE_PATH, PROCESSED_VENTURE_PATH)
  full_process_collectible_recipes(RAW_COLLECTIBLE_PATH, PROCESSED_COLLECTIBLE_PATH, PROCESSED_RECIPE_PATH)
  process_crafter_scrip_rewards(RAW_CRAFTER_SCRIP_PATH, PROCESSED_CRAFTER_SCRIP_PATH)


