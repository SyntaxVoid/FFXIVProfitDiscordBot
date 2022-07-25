import os.path as op

XIVAPI_URL = "https://www.xivapi.com"
UNIVERSALIS_URL = "https://www.universalis.app/api/v2"

OFFLINE_DATA_PATH = ODP = "OfflineData"
RAW_VENTURE_PATH             = op.join(ODP, "raw_combat_venture.txt")
PROCESSED_VENTURE_PATH       = op.join(ODP, "processed_combat_ventures.txt")
RAW_COLLECTIBLE_PATH         = op.join(ODP, "raw_collectible_names.txt")
PROCESSED_COLLECTIBLE_PATH   = op.join(ODP, "processed_collectible_names.txt")
PROCESSED_RECIPE_PATH        = op.join(ODP, "processed_collectible_recipes.txt")
RAW_CRAFTER_SCRIP_PATH       = op.join(ODP, "raw_crafter_scrip_rewards.txt")
PROCESSED_CRAFTER_SCRIP_PATH = op.join(ODP, "processed_crafter_scrip_rewards.txt")
ITEM_NAMES_AND_IDS           = op.join(ODP, "item_ids_to_names.txt")