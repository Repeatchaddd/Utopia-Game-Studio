"""RPG stat editor for Utopia Game Studio."""
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

DEFAULT_STATS=[
 {"name":"Life","current":100,"minimum":0,"maximum":100,"resource":True},
 {"name":"Mana","current":50,"minimum":0,"maximum":50,"resource":True},
 {"name":"Stamina","current":100,"minimum":0,"maximum":100,"resource":True},
 {"name":"Level","current":1,"minimum":1,"maximum":99,"resource":False},
 {"name":"Experience","current":0,"minimum":0,"maximum":999999,"resource":False},
]

def clean_stat_name(value):
 value=re.sub(r"[^A-Za-z0-9_]","_",value.strip())
 if value and value[0].isdigit():value="_"+value
 return value[:32]

def default_stats():
 return [dict(x) for x in DEFAULT_STATS]

def ensure_stats(project):
 if "rpg_stats" not in project:project["rpg_stats"]=default_stats()
 for s in project["rpg_stats"]:
  s.setdefault("minimum",0);s.setdefault("maximum",100);s.setdefault("current",s["maximum"]);s.setdefault("resource",True)
  if s["maximum"]<s["minimum"]:s["maximum"]=s["minimum"]
  s["current"]=max(s["minimum"],min(s["maximum"],s["current"]))
 return project["rpg_stats"]

def stat_names(project):return [s["name"] for s in ensure_stats(project)]

class StatDialog(simpledialog.Dialog):
 def __init__(self,parent,title,stat=None):
  self.stat=stat or {"name":"","current":0,"minimum":0,"maximum":100,"resource":True};self.result=None;super().__init__(parent,title)
 def body(self,parent):
  fields=(("Name","name"),("Starting value","current"),("Minimum","minimum"),("Maximum","maximum"))
  self.vars={}
  for row,(label,key) in enumerate(fields):
   ttk.Label(parent,text=label).grid(row=row,column=0,sticky="w",pady=4)
   v=tk.StringVar(value=str(self.stat.get(key,"")));self.vars[key]=v;ttk.Entry(parent,textvariable=v,width=20).grid(row=row,column=1,padx=(8,0),pady=4)
  self.resource=tk.BooleanVar(value=bool(self.stat.get("resource",True)));ttk.Checkbutton(parent,text="Resource stat (current / maximum)",variable=self.resource).grid(row=4,column=0,columnspan=2,sticky="w",pady=6)
  return parent
 def validate(self):
  name=clean_stat_name(self.vars["name"].get())
  if not name:messagebox.showerror("Utopia Game Studio","Enter a stat name.",parent=self);return False
  try:cur=int(self.vars["current"].get());lo=int(self.vars["minimum"].get());hi=int(self.vars["maximum"].get())
  except ValueError:messagebox.showerror("Utopia Game Studio","Stat values must be whole numbers.",parent=self);return False
  if hi<lo:messagebox.showerror("Utopia Game Studio","Maximum must be greater than or equal to minimum.",parent=self);return False
  if not lo<=cur<=hi:messagebox.showerror("Utopia Game Studio","Starting value must be between minimum and maximum.",parent=self);return False
  return True
 def apply(self):
  self.result={"name":clean_stat_name(self.vars["name"].get()),"current":int(self.vars["current"].get()),"minimum":int(self.vars["minimum"].get()),"maximum":int(self.vars["maximum"].get()),"resource":self.resource.get()}

class RPGStatsPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status,changed=None):
  super().__init__(parent,padding=10);self.get_project=project_getter;self.status=status;self.changed=changed or (lambda:None);self.build();self.refresh()
 def stats(self):return ensure_stats(self.get_project())
 def build(self):
  self.columnconfigure(0,weight=1);self.rowconfigure(1,weight=1)
  ttk.Label(self,text="RPG Stats",font=("Segoe UI",14,"bold")).grid(row=0,column=0,sticky="w")
  ttk.Label(self,text="Built-in defaults can be edited or removed. Add custom stats for your RPG. Values are clamped to Minimum / Maximum in Test Run and Wii U export.").grid(row=0,column=1,sticky="e")
  cols=("name","current","minimum","maximum","type")
  self.tree=ttk.Treeview(self,columns=cols,show="headings",height=16,selectmode="browse")
  for key,label,width in (("name","Stat",180),("current","Start",90),("minimum","Min",90),("maximum","Max",90),("type","Display",160)):
   self.tree.heading(key,text=label);self.tree.column(key,width=width,anchor="center" if key!="name" else "w")
  self.tree.grid(row=1,column=0,columnspan=2,sticky="nsew",pady=10);self.tree.bind("<Double-1>",lambda e:self.edit())
  buttons=ttk.Frame(self);buttons.grid(row=2,column=0,columnspan=2,sticky="w")
  ttk.Button(buttons,text="Add Stat",command=self.add).pack(side="left")
  ttk.Button(buttons,text="Edit Stat",command=self.edit).pack(side="left",padx=5)
  ttk.Button(buttons,text="Delete Stat",command=self.delete).pack(side="left")
  ttk.Button(buttons,text="Restore RPG Defaults",command=self.restore).pack(side="left",padx=(18,0))
 def refresh(self):
  ensure_stats(self.get_project())
  for i in self.tree.get_children():self.tree.delete(i)
  for n,s in enumerate(self.stats()):
   display="Current / Maximum" if s.get("resource",True) else "Value"
   self.tree.insert("", "end", iid=str(n), values=(s["name"],s["current"],s["minimum"],s["maximum"],display))
 def selected(self):
  s=self.tree.selection()
  if not s:return None,None
  i=int(s[0]);return (i,self.stats()[i]) if i<len(self.stats()) else (None,None)
 def add(self):
  d=StatDialog(self,"Add RPG Stat")
  if not d.result:return
  if d.result["name"] in stat_names(self.get_project()):messagebox.showerror("Utopia Game Studio","Stat names must be unique.");return
  self.stats().append(d.result);self.refresh();self.changed();self.status.set("RPG stat added")
 def edit(self):
  i,s=self.selected()
  if s is None:return
  old=s["name"];d=StatDialog(self,"Edit RPG Stat",dict(s))
  if not d.result:return
  if d.result["name"]!=old and d.result["name"] in stat_names(self.get_project()):messagebox.showerror("Utopia Game Studio","Stat names must be unique.");return
  self.stats()[i]=d.result
  for n in self.get_project().get("blueprint",{}).get("nodes",[]):
   if n.get("props",{}).get("stat")==old:n["props"]["stat"]=d.result["name"]
  self.refresh();self.changed();self.status.set("RPG stat updated")
 def delete(self):
  i,s=self.selected()
  if s is None:return
  if not messagebox.askyesno("Utopia Game Studio",f"Delete RPG stat '{s['name']}'?"):return
  name=s["name"];del self.stats()[i]
  for n in self.get_project().get("blueprint",{}).get("nodes",[]):
   if n.get("props",{}).get("stat")==name:n["props"]["stat"]=""
  self.refresh();self.changed();self.status.set("RPG stat deleted")
 def restore(self):
  if not messagebox.askyesno("Utopia Game Studio","Restore Life, Mana, Stamina, Level and Experience defaults? Existing custom stats are kept."):return
  names=set(stat_names(self.get_project()))
  for s in default_stats():
   if s["name"] not in names:self.stats().append(s)
  self.refresh();self.changed();self.status.set("RPG defaults restored")
