"""Inventory data model for Utopia Game Studio."""
SLOTS=("Head","Neck","Shoulders","Chest","Back","Hands","Waist","Legs","Feet","Main Hand","Off Hand","Ring 1","Ring 2","Accessory")
TYPES=("Consumable","Weapon","Armor","Shield","Accessory","Quest","Material","Key Item","Misc")

def default_inventory():
 return {"bag_capacity":24,"items":[],"bag":[],"equipped":{s:None for s in SLOTS}}

def ensure_inventory(project):
 inv=project.setdefault("inventory",default_inventory())
 inv.setdefault("bag_capacity",24);inv.setdefault("items",[]);inv.setdefault("bag",[]);inv.setdefault("equipped",{})
 for s in SLOTS:inv["equipped"].setdefault(s,None)
 return inv

def find_item(project,name):return next((i for i in ensure_inventory(project)["items"] if i["name"]==name),None)
def item_names(project):return [i["name"] for i in ensure_inventory(project)["items"]]
def bag_count(project,name):return sum(int(x.get("quantity",0)) for x in ensure_inventory(project)["bag"] if x.get("item")==name)

def add_to_bag(project,name,qty=1):
 inv=ensure_inventory(project);item=find_item(project,name)
 if not item:return False
 stack=max(1,int(item.get("max_stack",1)));qty=max(0,int(qty))
 for row in inv["bag"]:
  if row.get("item")==name and int(row.get("quantity",0))<stack:
   take=min(qty,stack-int(row["quantity"]));row["quantity"]+=take;qty-=take
 while qty:
  if len(inv["bag"])>=int(inv["bag_capacity"]):return False
  take=min(qty,stack);inv["bag"].append({"item":name,"quantity":take});qty-=take
 return True

def remove_from_bag(project,name,qty=1):
 inv=ensure_inventory(project);qty=max(0,int(qty))
 for row in list(inv["bag"]):
  if row.get("item")!=name:continue
  take=min(qty,int(row.get("quantity",0)));row["quantity"]-=take;qty-=take
  if row["quantity"]<=0:inv["bag"].remove(row)
  if qty<=0:return True
 return qty<=0

def equip_item(project,name,slot):
 inv=ensure_inventory(project);item=find_item(project,name)
 if not item or slot not in SLOTS or slot not in item.get("equip_slots",[]) or bag_count(project,name)<1:return False
 old=inv["equipped"].get(slot)
 if old and not add_to_bag(project,old,1):return False
 remove_from_bag(project,name,1);inv["equipped"][slot]=name;return True

def unequip_item(project,slot):
 inv=ensure_inventory(project);name=inv["equipped"].get(slot)
 if not name or not add_to_bag(project,name,1):return False
 inv["equipped"][slot]=None;return True

def equipment_modifiers(project):
 """Return summed stat bonuses from all equipped item definitions."""
 inv=ensure_inventory(project);totals={}
 for name in inv["equipped"].values():
  item=find_item(project,name) if name else None
  if not item:continue
  for stat,value in item.get("stats",{}).items():totals[stat]=totals.get(stat,0)+int(value)
 return totals

def effective_stat(base_stats,project,name):
 s=base_stats.get(name,{})
 return int(s.get("current",0))+equipment_modifiers(project).get(name,0)

def effective_maximum(base_stats,project,name):
 s=base_stats.get(name,{})
 return int(s.get("maximum",0))+equipment_modifiers(project).get(name,0)
