"""Inventory editor panel for Utopia Game Studio."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from inventory_system import SLOTS,TYPES,ensure_inventory,find_item,item_names,add_to_bag,remove_from_bag,equip_item,unequip_item

class InventoryPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status,changed):
  super().__init__(parent,padding=8);self.get_project=project_getter;self.status=status;self.changed=changed;self.build()
 def inv(self):return ensure_inventory(self.get_project())
 def build(self):
  top=ttk.Frame(self);top.pack(fill="x");ttk.Label(top,text="Bag capacity").pack(side="left");self.cap=tk.IntVar(value=self.inv()["bag_capacity"]);ttk.Spinbox(top,textvariable=self.cap,from_=1,to=200,width=6,command=self.set_capacity).pack(side="left",padx=6)
  body=ttk.Panedwindow(self,orient="horizontal");body.pack(fill="both",expand=True,pady=8)
  frames=[ttk.LabelFrame(body,text=t,padding=6) for t in ("Item Definitions","Bag Inventory","Equipped Items")]
  for f in frames:body.add(f)
  self.items=tk.Listbox(frames[0],width=32,exportselection=False);self.items.pack(fill="both",expand=True)
  for t,cmd in (("Add Item",self.add_item),("Edit Item",self.edit_item),("Delete Item",self.delete_item)):ttk.Button(frames[0],text=t,command=cmd).pack(fill="x",pady=2)
  self.bag=tk.Listbox(frames[1],width=28,exportselection=False);self.bag.pack(fill="both",expand=True)
  ttk.Button(frames[1],text="Add Item",command=self.add_bag).pack(fill="x",pady=2);ttk.Button(frames[1],text="Remove One",command=self.remove_bag).pack(fill="x",pady=2);ttk.Button(frames[1],text="Equip",command=self.equip_selected).pack(fill="x",pady=2)
  self.equip=tk.Listbox(frames[2],width=32,exportselection=False);self.equip.pack(fill="both",expand=True);ttk.Button(frames[2],text="Unequip",command=self.unequip_selected).pack(fill="x",pady=2)
  self.refresh()
 def set_capacity(self):self.inv()["bag_capacity"]=max(1,int(self.cap.get()));self.changed()
 def refresh(self):
  inv=self.inv();self.cap.set(inv["bag_capacity"]);self.items.delete(0,"end");self.bag.delete(0,"end");self.equip.delete(0,"end")
  for i in inv["items"]:self.items.insert("end",f"{i['name']} [{i['type']}] stack:{i['max_stack']}")
  for r in inv["bag"]:self.bag.insert("end",f"{r['item']} x{r['quantity']}")
  for s in SLOTS:self.equip.insert("end",f"{s}: {inv['equipped'].get(s) or '(empty)'}")
 def item_dialog(self,item=None):
  item=item or {};name=simpledialog.askstring("Item","Name:",initialvalue=item.get("name",""),parent=self)
  if not name:return None
  typ=simpledialog.askstring("Item","Type: "+", ".join(TYPES),initialvalue=item.get("type","Misc"),parent=self) or "Misc"
  if typ not in TYPES:typ="Misc"
  stack=simpledialog.askinteger("Item","Maximum stack:",initialvalue=item.get("max_stack",1),minvalue=1,maxvalue=999,parent=self)
  if stack is None:return None
  raw=simpledialog.askstring("Item","Allowed equipment slots (comma separated; blank for bag-only):\n"+", ".join(SLOTS),initialvalue=", ".join(item.get("equip_slots",[])),parent=self) or ""
  slots=[x.strip() for x in raw.split(",") if x.strip() in SLOTS]
  statraw=simpledialog.askstring("Item Stat Modifiers","Equipment bonuses as Stat=Value, comma separated.\nExamples: Attack=10, Defense=5, Mana=20",initialvalue=", ".join(f"{k}={v}" for k,v in item.get("stats",{}).items()),parent=self) or ""
  stats={}
  for part in statraw.split(","):
   if "=" not in part:continue
   k,v=part.split("=",1);k=k.strip()
   try:
    if k:stats[k]=int(v.strip())
   except ValueError:pass
  desc=simpledialog.askstring("Item Description","Description:",initialvalue=item.get("description",""),parent=self) or ""
  return {"name":name.strip()[:48],"type":typ,"max_stack":stack,"equip_slots":slots,"description":desc,"stats":stats}
 def add_item(self):
  x=self.item_dialog()
  if not x:return
  if find_item(self.get_project(),x["name"]):messagebox.showerror("Utopia Game Studio","Item name must be unique.",parent=self);return
  self.inv()["items"].append(x);self.refresh();self.changed()
 def edit_item(self):
  s=self.items.curselection()
  if not s:return
  old=self.inv()["items"][s[0]];x=self.item_dialog(old)
  if not x:return
  oldname=old["name"];self.inv()["items"][s[0]]=x
  for r in self.inv()["bag"]:
   if r["item"]==oldname:r["item"]=x["name"]
  for slot in SLOTS:
   if self.inv()["equipped"].get(slot)==oldname:self.inv()["equipped"][slot]=x["name"]
  self.refresh();self.changed()
 def delete_item(self):
  s=self.items.curselection()
  if not s:return
  name=self.inv()["items"][s[0]]["name"]
  if not messagebox.askyesno("Utopia Game Studio",f"Delete {name} everywhere?",parent=self):return
  del self.inv()["items"][s[0]];self.inv()["bag"]=[r for r in self.inv()["bag"] if r["item"]!=name]
  for slot in SLOTS:
   if self.inv()["equipped"].get(slot)==name:self.inv()["equipped"][slot]=None
  self.refresh();self.changed()
 def add_bag(self):
  names=item_names(self.get_project())
  if not names:return
  name=simpledialog.askstring("Bag","Item name:\n"+", ".join(names),parent=self)
  if name in names:add_to_bag(self.get_project(),name,1);self.refresh();self.changed()
 def remove_bag(self):
  s=self.bag.curselection()
  if s:remove_from_bag(self.get_project(),self.inv()["bag"][s[0]]["item"],1);self.refresh();self.changed()
 def equip_selected(self):
  s=self.bag.curselection()
  if not s:return
  name=self.inv()["bag"][s[0]]["item"];item=find_item(self.get_project(),name);slots=item.get("equip_slots",[]) if item else []
  if not slots:messagebox.showinfo("Utopia Game Studio","This is a bag-only item.",parent=self);return
  slot=simpledialog.askstring("Equip","Slot:\n"+", ".join(slots),initialvalue=slots[0],parent=self)
  if slot in slots:equip_item(self.get_project(),name,slot);self.refresh();self.changed()
 def unequip_selected(self):
  s=self.equip.curselection()
  if s:unequip_item(self.get_project(),SLOTS[s[0]]);self.refresh();self.changed()
