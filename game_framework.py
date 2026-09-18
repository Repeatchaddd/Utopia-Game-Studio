#!/usr/bin/env python3
"""Utopia Game Studio v1.95.002.001 generic game-framework skeleton."""
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

OBJECT_KINDS=("Player","NPC","Enemy","Item","Generic")
EVENT_TYPES=("Game Start","Room Start","Update","Collision","Interact")
ACTION_TYPES=("Set Variable","Change Variable","Destroy Self","Hide Self","Show Self","Change Room","Move Self","Add Item")
COMPARE_OPS=("==","!=", "<","<=",">",">=")
PRESET_OBJECT_VARIABLES=("X","Y","Visible","Active","Width","Height","Solid")
def object_variable_names(obj):
 names=[f"Self.{n}" for n in PRESET_OBJECT_VARIABLES]
 names += [f"Self.{n}" for n in obj.get("variables",{}) if n not in PRESET_OBJECT_VARIABLES]
 return names

def default_framework():
 return {
  "start_room":"Room 1",
  "rooms":[{"name":"Room 1","room_map":[],"instances":[]}],
  "objects":[],
  "next_instance_id":1
 }

def ensure_framework(project):
 fw=project.setdefault("framework",default_framework())
 fw.setdefault("start_room","Room 1");fw.setdefault("objects",[]);fw.setdefault("rooms",[]);fw.setdefault("next_instance_id",1)
 if not fw["rooms"]:fw["rooms"].append({"name":"Room 1","room_map":list(project.get("room_map",[])),"instances":[]})
 for room in fw["rooms"]:
  room.setdefault("room_map",list(project.get("room_map",[])));room.setdefault("instances",[])
  if not room["room_map"]:room["room_map"]=list(project.get("room_map",[]))
  if len(room["room_map"])<40*23:room["room_map"]=(room["room_map"]+[-1]*(40*23))[:40*23]
 for obj in fw["objects"]:
  obj.setdefault("kind","Generic");obj.setdefault("width",48);obj.setdefault("height",48);obj.setdefault("color","#ff8c42")
  obj.setdefault("visible",True);obj.setdefault("solid",False);obj.setdefault("variables",{});obj.setdefault("events",[]);obj.setdefault("interact_range",72)
 names=[r["name"] for r in fw["rooms"]]
 if fw["start_room"] not in names:fw["start_room"]=names[0]
 return fw

def find_room(project,name):
 fw=ensure_framework(project)
 return next((r for r in fw["rooms"] if r["name"]==name),fw["rooms"][0])

def find_object(project,name):
 return next((o for o in ensure_framework(project)["objects"] if o["name"]==name),None)

class FrameworkPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status,changed=None):
  super().__init__(parent,padding=8);self.get_project=project_getter;self.status=status;self.changed=changed or (lambda:None)
  self.build();self.refresh()
 def fw(self):return ensure_framework(self.get_project())
 def build(self):
  self.columnconfigure(1,weight=1);self.rowconfigure(0,weight=1)
  left=ttk.LabelFrame(self,text="Game Objects",padding=8);left.grid(row=0,column=0,sticky="ns",padx=(0,8))
  mid=ttk.LabelFrame(self,text="Rooms / Instances",padding=8);mid.grid(row=0,column=1,sticky="nsew",padx=(0,8));mid.columnconfigure(0,weight=1);mid.rowconfigure(1,weight=1)
  right=ttk.LabelFrame(self,text="Object Events / Actions",padding=8);right.grid(row=0,column=2,sticky="ns")
  self.object_list=tk.Listbox(left,width=25,height=18,exportselection=False);self.object_list.pack(fill="both",expand=True);self.object_list.bind("<<ListboxSelect>>",lambda e:self.refresh_events())
  ttk.Button(left,text="Add Object",command=self.add_object).pack(fill="x",pady=(8,2));ttk.Button(left,text="Edit Object",command=self.edit_object).pack(fill="x");ttk.Button(left,text="Object Variables",command=self.manage_object_variables).pack(fill="x",pady=(2,0));ttk.Button(left,text="Delete Object",command=self.delete_object).pack(fill="x",pady=(2,0))
  top=ttk.Frame(mid);top.grid(row=0,column=0,sticky="ew");self.room=tk.StringVar();self.room_box=ttk.Combobox(top,textvariable=self.room,state="readonly",width=25);self.room_box.pack(side="left",fill="x",expand=True);self.room_box.bind("<<ComboboxSelected>>",lambda e:self.refresh_instances())
  ttk.Button(top,text="+ Room",command=self.add_room).pack(side="left",padx=3);ttk.Button(top,text="Start",command=self.set_start_room).pack(side="left")
  self.instance_list=tk.Listbox(mid,height=18,exportselection=False);self.instance_list.grid(row=1,column=0,sticky="nsew",pady=(8,6))
  ib=ttk.Frame(mid);ib.grid(row=2,column=0,sticky="ew");ttk.Button(ib,text="Place Object",command=self.place_object).pack(side="left");ttk.Button(ib,text="Edit Instance",command=self.edit_instance).pack(side="left",padx=3);ttk.Button(ib,text="Delete Instance",command=self.delete_instance).pack(side="left")
  self.event_list=tk.Listbox(right,width=38,height=12,exportselection=False);self.event_list.pack(fill="both",expand=True)
  ttk.Button(right,text="Add Event",command=self.add_event).pack(fill="x",pady=(8,2));ttk.Button(right,text="Add Action",command=self.add_action).pack(fill="x");ttk.Button(right,text="Delete Event",command=self.delete_event).pack(fill="x",pady=(2,0))
  ttk.Label(right,text="Programming skeleton:\nStart / Room Start / Update / Collision / Interact\nVariables, room changes, visibility,\ndestroy and simple movement.",justify="left").pack(anchor="w",pady=(12,0))
 def selected_object(self):
  s=self.object_list.curselection();objs=self.fw()["objects"];return objs[s[0]] if s and s[0]<len(objs) else None
 def selected_room(self):return find_room(self.get_project(),self.room.get())
 def refresh(self):
  fw=self.fw();self.object_list.delete(0,"end")
  for o in fw["objects"]:self.object_list.insert("end",f"{o['name']}  [{o['kind']}]")
  rooms=[r["name"] for r in fw["rooms"]];self.room_box["values"]=rooms
  if self.room.get() not in rooms:self.room.set(rooms[0] if rooms else "")
  self.refresh_instances();self.refresh_events()
 def refresh_instances(self):
  self.instance_list.delete(0,"end");room=self.selected_room()
  if room:
   for i in room["instances"]:self.instance_list.insert("end",f"#{i['id']} {i['object']}  ({i['x']},{i['y']})")
 def refresh_events(self):
  self.event_list.delete(0,"end");obj=self.selected_object()
  if not obj:return
  for n,e in enumerate(obj["events"]):
   extra=f" -> {e.get('other','')}" if e["type"]=="Collision" else (" [near player]" if e["type"]=="Interact" else "")
   self.event_list.insert("end",f"{n+1:02d} {e['type']}{extra}  [{len(e.get('actions',[]))} action(s)]")
 def add_object(self):
  name=simpledialog.askstring("Utopia Game Studio","Object name:",parent=self)
  if not name:return
  name=name.strip()
  if not name or find_object(self.get_project(),name):messagebox.showerror("Utopia Game Studio","Object names must be unique.");return
  kind=simpledialog.askstring("Utopia Game Studio","Kind: Player, NPC, Enemy, Item, Generic",initialvalue="Generic",parent=self) or "Generic"
  if kind not in OBJECT_KINDS:kind="Generic"
  self.fw()["objects"].append({"name":name,"kind":kind,"width":48,"height":48,"color":"#ff8c42","visible":True,"solid":False,"variables":{},"events":[],"interact_range":72});self.refresh();self.changed();self.status.set("Game object created")
 def edit_object(self):
  o=self.selected_object()
  if not o:return
  w=simpledialog.askinteger("Object Properties","Width:",initialvalue=o["width"],minvalue=1,maxvalue=512,parent=self);h=simpledialog.askinteger("Object Properties","Height:",initialvalue=o["height"],minvalue=1,maxvalue=512,parent=self)
  if w is not None:o["width"]=w
  if h is not None:o["height"]=h
  solid=messagebox.askyesno("Object Properties","Should this object block/collide as solid?",parent=self);o["solid"]=solid
  rng=simpledialog.askinteger("Object Properties","Interaction range in pixels:",initialvalue=o.get("interact_range",72),minvalue=1,maxvalue=512,parent=self)
  if rng is not None:o["interact_range"]=rng
  self.refresh();self.changed()
 def manage_object_variables(self):
  o=self.selected_object()
  if not o:return
  while True:
   custom=[n for n in o.get("variables",{}) if n not in PRESET_OBJECT_VARIABLES]
   choice=simpledialog.askstring("Object Variables","Preset variables are always available:\nX, Y, Visible, Active, Width, Height, Solid\n\nCustom variables: "+(", ".join(custom) if custom else "(none)")+"\n\nEnter a custom variable name to add/edit, or leave blank to close:",parent=self)
   if not choice:break
   name="".join(ch if ch.isalnum() or ch=="_" else "_" for ch in choice.strip())[:32]
   if not name or name in PRESET_OBJECT_VARIABLES:
    messagebox.showinfo("Object Variables","That name is reserved for a preset object variable.",parent=self);continue
   value=simpledialog.askinteger("Object Variables",f"Starting value for {name}:",initialvalue=int(o.get("variables",{}).get(name,0)),parent=self)
   if value is not None:o.setdefault("variables",{})[name]=value;self.changed();self.status.set("Object variable updated")
 def delete_object(self):
  o=self.selected_object()
  if not o:return
  if not messagebox.askyesno("Utopia Game Studio",f"Delete object '{o['name']}' and all placed instances?",parent=self):return
  self.fw()["objects"].remove(o)
  for room in self.fw()["rooms"]:room["instances"]=[i for i in room["instances"] if i["object"]!=o["name"]]
  self.refresh();self.changed()
 def add_room(self):
  name=simpledialog.askstring("Utopia Game Studio","Room name:",parent=self)
  if not name:return
  name=name.strip()
  if not name or any(r["name"]==name for r in self.fw()["rooms"]):messagebox.showerror("Utopia Game Studio","Room names must be unique.");return
  self.fw()["rooms"].append({"name":name,"room_map":[-1]*(40*23),"instances":[]});self.room.set(name);self.refresh();self.changed()
 def set_start_room(self):
  if self.room.get():self.fw()["start_room"]=self.room.get();self.status.set(f"Start room: {self.room.get()}");self.changed()
 def place_object(self):
  o=self.selected_object();room=self.selected_room()
  if not o or not room:messagebox.showinfo("Utopia Game Studio","Select an object and a room first.");return
  x=simpledialog.askinteger("Place Object","X position:",initialvalue=100,minvalue=0,maxvalue=1279,parent=self)
  if x is None:return
  y=simpledialog.askinteger("Place Object","Y position:",initialvalue=100,minvalue=0,maxvalue=719,parent=self)
  if y is None:return
  fw=self.fw();ident=fw["next_instance_id"];fw["next_instance_id"]+=1;room["instances"].append({"id":ident,"object":o["name"],"x":x,"y":y,"visible":True,"active":True,"variables":{}})
  self.refresh_instances();self.changed()
 def selected_instance(self):
  room=self.selected_room();s=self.instance_list.curselection();return (room["instances"][s[0]] if room and s and s[0]<len(room["instances"]) else None)
 def edit_instance(self):
  i=self.selected_instance()
  if not i:return
  x=simpledialog.askinteger("Instance","X:",initialvalue=i["x"],minvalue=0,maxvalue=1279,parent=self);y=simpledialog.askinteger("Instance","Y:",initialvalue=i["y"],minvalue=0,maxvalue=719,parent=self)
  if x is not None:i["x"]=x
  if y is not None:i["y"]=y
  self.refresh_instances();self.changed()
 def delete_instance(self):
  room=self.selected_room();i=self.selected_instance()
  if room and i:room["instances"].remove(i);self.refresh_instances();self.changed()
 def add_event(self):
  o=self.selected_object()
  if not o:return
  et=simpledialog.askstring("Add Event","Event: Game Start, Room Start, Update, Collision, Interact",initialvalue="Update",parent=self)
  if et not in EVENT_TYPES:return
  event={"type":et,"actions":[]}
  if et=="Collision":
   other=simpledialog.askstring("Collision Event","Other object name:",parent=self)
   if not other:return
   event["other"]=other
  o["events"].append(event);self.refresh_events();self.changed()
 def selected_event(self):
  o=self.selected_object();s=self.event_list.curselection();return (o["events"][s[0]] if o and s and s[0]<len(o["events"]) else None)
 def add_action(self):
  event=self.selected_event()
  if not event:messagebox.showinfo("Utopia Game Studio","Select an event first.");return
  kind=simpledialog.askstring("Add Action","Action: "+", ".join(ACTION_TYPES),initialvalue="Change Variable",parent=self)
  if kind not in ACTION_TYPES:return
  a={"type":kind}
  if kind in ("Set Variable","Change Variable"):
   o=self.selected_object();globals_=[v.get("name","") for v in self.get_project().get("variables",[]) if v.get("name")]
   choices=object_variable_names(o)+globals_
   d=tk.Toplevel(self);d.title("Choose Variable");d.transient(self.winfo_toplevel());d.grab_set()
   ttk.Label(d,text="Variable").grid(row=0,column=0,padx=8,pady=8,sticky="w")
   vv=tk.StringVar(value=choices[0] if choices else "Self.X");box=ttk.Combobox(d,textvariable=vv,values=choices,state="readonly",width=28);box.grid(row=0,column=1,padx=8,pady=8)
   result={"ok":False}
   def accept():result["ok"]=True;d.destroy()
   ttk.Button(d,text="OK",command=accept).grid(row=1,column=1,padx=8,pady=(0,8),sticky="e");d.wait_window()
   if not result["ok"]:return
   a["variable"]=vv.get()
   a["value"]=simpledialog.askinteger("Action","Value:",initialvalue=1,parent=self) or 0
  elif kind=="Change Room":
   a["room"]=simpledialog.askstring("Action","Destination room:",initialvalue=self.fw()["start_room"],parent=self) or self.fw()["start_room"]
  elif kind=="Move Self":
   a["dx"]=simpledialog.askinteger("Action","Move X per update:",initialvalue=0,parent=self) or 0;a["dy"]=simpledialog.askinteger("Action","Move Y per update:",initialvalue=0,parent=self) or 0
  elif kind=="Add Item":
   from inventory_system import item_names
   names=item_names(self.get_project());a["item"]=simpledialog.askstring("Action","Item to add:\n"+", ".join(names),initialvalue=names[0] if names else "",parent=self) or ""
   if a["item"] not in names:return
   a["quantity"]=simpledialog.askinteger("Action","Quantity:",initialvalue=1,minvalue=1,parent=self) or 1
  event["actions"].append(a);self.refresh_events();self.changed()
 def delete_event(self):
  o=self.selected_object();e=self.selected_event()
  if o and e:o["events"].remove(e);self.refresh_events();self.changed()

class GameRuntime:
 def __init__(self,project,global_vars):
  self.project=project;self.fw=ensure_framework(project);self.vars=global_vars;self.room_name=self.fw["start_room"];self.destroyed=set();self.hidden=set();self.room_started=True;self.started=False
 def room(self):return find_room(self.project,self.room_name)
 def room_map(self):return self.room().get("room_map",self.project.get("room_map",[-1]*(40*23)))
 def instances(self):
  return [i for i in self.room()["instances"] if i.get("active",True) and i["id"] not in self.destroyed]
 def obj(self,inst):return find_object(self.project,inst["object"])
 def rect(self,inst):
  o=self.obj(inst) or {"width":32,"height":32};return (inst["x"],inst["y"],inst["x"]+o.get("width",32),inst["y"]+o.get("height",32))
 def hit(self,a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
 def _object_value(self,inst,name):
  o=self.obj(inst) or {}
  if name=="X":return int(inst.get("x",0))
  if name=="Y":return int(inst.get("y",0))
  if name=="Visible":return 0 if inst["id"] in self.hidden else int(inst.get("visible",True))
  if name=="Active":return int(inst.get("active",True))
  if name=="Width":return int(o.get("width",48))
  if name=="Height":return int(o.get("height",48))
  if name=="Solid":return int(o.get("solid",False))
  return int(inst.setdefault("variables",{}).get(name,o.get("variables",{}).get(name,0)))
 def _set_object_value(self,inst,name,value):
  value=int(value);o=self.obj(inst) or {}
  if name=="X":inst["x"]=value
  elif name=="Y":inst["y"]=value
  elif name=="Visible":
   inst["visible"]=bool(value);self.hidden.discard(inst["id"]) if value else self.hidden.add(inst["id"])
  elif name=="Active":inst["active"]=bool(value)
  elif name=="Width":o["width"]=max(1,value)
  elif name=="Height":o["height"]=max(1,value)
  elif name=="Solid":o["solid"]=bool(value)
  else:inst.setdefault("variables",{})[name]=value
 def actions(self,runner,inst,actions):
  for a in actions:
   t=a["type"]
   if t in ("Set Variable","Change Variable"):
    name=a.get("variable","");value=int(a.get("value",0))
    if name.startswith("Self."):
     key=name[5:];self._set_object_value(inst,key,value if t=="Set Variable" else self._object_value(inst,key)+value)
    elif t=="Set Variable":self.vars[name]=value
    else:self.vars[name]=self.vars.get(name,0)+value
   elif t=="Destroy Self":self.destroyed.add(inst["id"])
   elif t=="Hide Self":self.hidden.add(inst["id"])
   elif t=="Show Self":self.hidden.discard(inst["id"])
   elif t=="Move Self":inst["x"]+=int(a.get("dx",0));inst["y"]+=int(a.get("dy",0))
   elif t=="Add Item":
    from inventory_system import add_to_bag
    add_to_bag(self.project,a.get("item",""),int(a.get("quantity",1)))
   elif t=="Change Room":
    if any(r["name"]==a.get("room") for r in self.fw["rooms"]):self.room_name=a["room"];self.room_started=True
 def fire(self,runner,inst,event_type,other=None):
  o=self.obj(inst)
  if not o:return
  for e in o.get("events",[]):
   if e["type"]!=event_type:continue
   if event_type=="Collision" and e.get("other")!=other:continue
   self.actions(runner,inst,e.get("actions",[]))
 def interact(self,runner):
  px=runner.x+runner.project["player_width"]/2;py=runner.y+runner.project["player_height"]/2
  best=None;best_d=None
  for inst in self.instances():
   o=self.obj(inst)
   if not o or not any(e.get("type")=="Interact" for e in o.get("events",[])):continue
   cx=inst["x"]+o.get("width",48)/2;cy=inst["y"]+o.get("height",48)/2;dx=cx-px;dy=cy-py;d=(dx*dx+dy*dy)**0.5
   if d<=float(o.get("interact_range",72)) and (best_d is None or d<best_d):best=inst;best_d=d
  if best is not None:self.fire(runner,best,"Interact")
  return best is not None
 def step(self,runner,first=False):
  instances=list(self.instances())
  if not self.started:
   for i in instances:self.fire(runner,i,"Game Start")
   self.started=True
  if self.room_started:
   for i in instances:self.fire(runner,i,"Room Start")
   self.room_started=False
  for i in list(self.instances()):self.fire(runner,i,"Update")
  player_rect=(runner.x,runner.y,runner.x+runner.project["player_width"],runner.y+runner.project["player_height"])
  for i in list(self.instances()):
   o=self.obj(i)
   if not o:continue
   if self.hit(player_rect,self.rect(i)):self.fire(runner,i,"Collision","Player")
  instances=list(self.instances())
  for n,a in enumerate(instances):
   for b in instances[n+1:]:
    if self.hit(self.rect(a),self.rect(b)):
     self.fire(runner,a,"Collision",b["object"]);self.fire(runner,b,"Collision",a["object"])
 def draw(self,canvas,scale,ox,oy):
  for i in self.instances():
   if i["id"] in self.hidden:continue
   o=self.obj(i)
   if not o or not o.get("visible",True):continue
   x=ox+i["x"]*scale;y=oy+i["y"]*scale;w=o.get("width",48)*scale;h=o.get("height",48)*scale
   canvas.create_rectangle(x,y,x+w,y+h,fill=o.get("color","#ff8c42"),outline="white")
   canvas.create_text(x+w/2,y+h/2,text=o["name"],fill="white")
