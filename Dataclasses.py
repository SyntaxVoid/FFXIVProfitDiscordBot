class CraftingClass(object):
  def __init__(self, name, abr, class_id, icon):
    self.name = name
    self.abr = abr
    self.class_id = class_id
    self.icon_url = f"https://www.xivapi.com{icon}"
    return

  def __repr__(self):
    return f"<CraftingClass({self.name})>"

class Item(object):
  def __init__(self, d):
    root_url = "https://xivapi.com"
    self.item_id = d["ID"]
    self.icon_url = f"{root_url}{d['Icon']}"
    self.name = d["Name"]
    self.item_url = f"{root_url}{d['Url']}"
    self.url_type = d["UrlType"]
    return
  
  def __repr__(self):
    return f"<Item({self.name})>"

class Recipe(object):
  def __init__(self, name, level, craftingclass, ingredient_names, amounts):
    self.name = name
    self.level = level
    self.craftingclass = craftingclass # a CraftingClass object
    self.ingredient_names = ingredient_names
    self.amounts = amounts
    return
  
  def __repr__(self):
    return f"<Recipe({self.name})>"
  
  def _as_dict(self): # Don't use this pls
    return {            "name": self.name,
                       "level": self.level, 
              "crafting_class": self.craftingclass.name,
            "ingredient_names": self.ingredient_names, 
                     "amounts": self.amounts}

class SaleStats(object):
  def __init__(self, name, item_id, server, n_days):
    self.name = name
    self.item_id = item_id
    self.server = server
    self.n_days = n_days
    self.nq_sales_gil = 0
    self.hq_sales_gil = 0
    self.nq_sales_quantity = 0
    self.hq_sales_quantity = 0
    self.entries = []
    return
  
  def __str__(self):
    return f"""Sale Stats for <{self.name}> over the last {self.n_days} days on {self.server}:
  NQ Sales (Gil):        {self.nq_sales_gil:>12,}
  NQ Sales (Quantity):   {self.nq_sales_quantity:>12,}
  NQ Sales (Avg. Price): {self.nq_average:>12,}

  HQ Sales (Gil):        {self.hq_sales_gil:>12,}
  HQ Sales (Quantity):   {self.hq_sales_quantity:>12,}
  HQ Sales (Avg. Price): {self.hq_average:>12,}
"""

  def __repr__(self):
    return f"<SaleStats({self.name})>"

  def __add__(self, other):
    if other == 0:
      return self
    answer = SaleStats(self.name, self.item_id, self.server, self.n_days)
    answer.nq_sales_gil = self.nq_sales_gil + other.nq_sales_gil
    answer.hq_sales_gil = self.hq_sales_gil + other.hq_sales_gil
    answer.nq_sales_quantity = self.nq_sales_quantity + other.nq_sales_quantity
    answer.hq_sales_quantity = self.hq_sales_quantity + other.hq_sales_quantity
    answer.entries = [*self.entries, *other.entries]
    return answer

  def __radd__(self, other):
    if other == 0:
      return self
    return self.__add__(other)


  @property
  def nq_average(self):
    if self.nq_sales_quantity == 0:
      return 0
    return round(self.nq_sales_gil / self.nq_sales_quantity)

  @property
  def hq_average(self):
    if self.hq_sales_quantity == 0:
      return 0
    return round(self.hq_sales_gil / self.hq_sales_quantity)

  def update(self, entry):
    if entry["hq"]:
      self.hq_sales_quantity += entry["quantity"]
      self.hq_sales_gil += entry["quantity"]*entry["pricePerUnit"]
    elif not entry["hq"]:
      self.nq_sales_quantity += entry["quantity"]
      self.nq_sales_gil += entry["quantity"]*entry["pricePerUnit"]
    self.entries.append(entry)
    return

  def remove_outliers(self, threshold=3):
    ixs_to_remove = []
    for n, entry in enumerate(self.entries):
      # Get average if this entry was removed
      average_entry_price = entry["pricePerUnit"]
      if entry["hq"]:
        temp_sales_quantity = self.hq_sales_quantity - entry["quantity"]
        temp_sales_gil = self.hq_sales_gil - entry["quantity"]*entry["pricePerUnit"]
        new_average = round(temp_sales_gil / temp_sales_quantity) # without the entry
        if average_entry_price > threshold*new_average:
          ixs_to_remove.append(n)
          self.hq_sales_quantity = temp_sales_quantity
          self.hq_sales_gil = temp_sales_gil
      if not entry["hq"]:
        temp_sales_quantity = self.nq_sales_quantity - entry["quantity"]
        temp_sales_gil = self.nq_sales_gil - entry["quantity"]*entry["pricePerUnit"]
        new_average = round(temp_sales_gil / temp_sales_quantity) # without the entry
        if average_entry_price > threshold*new_average:
          ixs_to_remove.append(n)
          self.nq_sales_quantity = temp_sales_quantity
          self.nq_sales_gil = temp_sales_gil
    for ix in ixs_to_remove[::-1]:
      # print("Removing", self.entries[ix])
      self.entries.pop(ix)
    
    