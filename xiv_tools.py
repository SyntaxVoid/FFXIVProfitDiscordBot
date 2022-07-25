from copy import deepcopy
from functools import lru_cache
from itertools import chain
import json
import statistics

from global_paths import *

def read_all(file_name):
  with open(file_name, "r", encoding="utf-8") as f:
    return f.read()

def write_json_to_file(obj, file_name):
  with open(file_name, "w", encoding="utf-8") as f:
    f.write(json.dumps(obj, indent=2))
  return

def load_json_from_local(file_name):
  with open(file_name, "r", encoding="utf-8") as f:
    return json.loads(f.read())

def split_every(arr, n):
  return [arr[i:i+n] for i in range(0, len(arr), n)]

def dict_slicer(d, keys):
  return [[v[key] for v in d] for key in keys]

def multi_index_slice(arr, ixs):
  return [arr[ix] for ix in ixs]

def format_column(table, cols, fstrs):
  _table = deepcopy(table)
  for row in range(len(table)):
    for col, fstr in zip(cols, fstrs):
      _table[row][col] = fstr.format(_table[row][col]) if _table[row][col] != "" else ""
  return _table

def filter_outliers(arr, f=1.5, filter_above=True, filter_below=True):
  if len(arr) == 1:
    return [0]
  q25, q50, q75 = statistics.quantiles(arr)
  q0, q100 = min(arr), max(arr)
  qir = q75-q25
  good_ixs = []
  high_cutoff = q75+(f*qir) if filter_above else q100
  low_cutoff  = q25-(f*qir) if filter_below else q0
  for ix, element in enumerate(arr):
    if low_cutoff <= element <= high_cutoff:
      good_ixs.append(ix)
  return good_ixs
  

__ITEM_ID_DATA = {}
@lru_cache
def name_from_item_id(item_id):
  global __ITEM_ID_DATA
  if not __ITEM_ID_DATA:
    __ITEM_ID_DATA = load_json_from_local(ITEM_NAMES_AND_IDS)
  return __ITEM_ID_DATA[str(item_id)]["en"]

@lru_cache
def item_id_from_name(name):
  global __ITEM_ID_DATA
  if not __ITEM_ID_DATA:
    __ITEM_ID_DATA = load_json_from_local(ITEM_NAMES_AND_IDS)
  name = name.strip().lower()
  for item_id, item_names in __ITEM_ID_DATA.items():
    if item_names["en"].lower() == name:
      return item_id
  return 0

def weave_lists(*args):
  return list(chain.from_iterable(zip(*args)))
