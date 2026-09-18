"""Original node-based visual scripting panel for Utopia Game Studio."""
import copy
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from rpg_stats import ensure_stats, stat_names
from inventory_system import SLOTS, item_names, ensure_inventory
from input_controls import action_names

NODE_COLORS={
 "Start":"#6b4f8a","Update":"#8a4f6b","GamePad Input":"#315d83","Input Action":"#315d83",
 "Move Character":"#3f7a55","Run Modifier":"#8a6335",
 "Set Variable":"#75558c","Change Variable":"#66519a","Compare Variable":"#8c5555",
 "Set Stat":"#7a5b3f","Change Stat":"#8b643c","Set Max Stat":"#9a713f","Compare Stat":"#9a4f4f",
 "Add Item":"#527a68","Remove Item":"#7a5252","Has Item":"#6b6f8a","Equip Item":"#526f7a","Unequip Slot":"#7a6b52","Interact":"#477a72","Toggle Inventory":"#6a5f82"
}
BUTTONS=("LEFT","RIGHT","UP","DOWN","A","B","X","Y")
DIRECTIONS={"Left":(-1,0),"Right":(1,0),"Up":(0,-1),"Down":(0,1)}
COMPARE_OPS=("==","!=","<","<=",">",">=")
OP_CODES={"==":0,"!=":1,"<":2,"<=":3,">":4,">=":5}

def clean_name(value):
 value=re.sub(r"[^A-Za-z0-9_]","_",value.strip())
 if value and value[0].isdigit():value="_"+value
 return value[:32]

def variables(project):
 project.setdefault("variables",[])
 return project["variables"]

PRESET_PLAYER_VARIABLES=("Player.X","Player.Y","Player.Visible","Player.Active","Player.Width","Player.Height","Player.Solid")
def variable_names(project):return [v["name"] for v in variables(project)]
def blueprint_variable_names(project):return list(PRESET_PLAYER_VARIABLES)+variable_names(project)

class VariableManager(simpledialog.Dialog):
 def __init__(self,parent,project):self.project=project;super().__init__(parent,"Blueprint Variables")
 def body(self,parent):
  self.list=tk.Listbox(parent,width=36,height=12,exportselection=False);self.list.grid(row=0,column=0,columnspan=3,sticky="nsew")
  ttk.Button(parent,text="Add",command=self.add).grid(row=1,column=0,sticky="ew",pady=5)
  ttk.Button(parent,text="Edit",command=self.edit).grid(row=1,column=1,sticky="ew",padx=5,pady=5)
  ttk.Button(parent,text="Delete",command=self.delete).grid(row=1,column=2,sticky="ew",pady=5)
  self.refresh();return self.list
 def buttonbox(self):
  box=ttk.Frame(self);ttk.Button(box,text="Close",command=self.ok).pack(side="right",padx=5,pady=5);box.pack(fill="x")
 def refresh(self):
  self.list.delete(0,"end")
  for v in variables(self.project):self.list.insert("end",f"{v['name']} = {v.get('value',0)}")
 def add(self):
  name=simpledialog.askstring("Variable","Variable name:",parent=self)
  if not name:return
  name=clean_name(name)
  if not name or name in variable_names(self.project):messagebox.showerror("Utopia Game Studio","Use a unique variable name.",parent=self);return
  value=simpledialog.askinteger("Variable","Starting whole-number value:",initialvalue=0,parent=self)
  if value is None:return
  variables(self.project).append({"name":name,"value":value});self.refresh()
 def edit(self):
  s=self.list.curselection()
  if not s:return
  v=variables(self.project)[s[0]]
  value=simpledialog.askinteger("Variable",f"Starting value for {v['name']}:",initialvalue=v.get("value",0),parent=self)
  if value is not None:v["value"]=value;self.refresh()
 def delete(self):
  s=self.list.curselection()
  if not s:return
  name=variables(self.project)[s[0]]["name"]
  if messagebox.askyesno("Utopia Game Studio",f"Delete variable '{name}'?",parent=self):
   del variables(self.project)[s[0]]
   g=self.project.get("blueprint",{})
   for n in g.get("nodes",[]):
    p=n.get("props",{})
    for key in ("variable","speed_variable"):
     if p.get(key)==name:p[key]=""
   self.refresh()

class StatActionDialog(simpledialog.Dialog):
 def __init__(self,parent,title,props,names,compare=False):
  self.props=props;self.names=names;self.compare=compare;self.result=None;super().__init__(parent,title)
 def body(self,parent):
  ttk.Label(parent,text="Stat").grid(row=0,column=0,sticky="w",pady=5);self.name=tk.StringVar(value=self.props.get("stat",self.names[0] if self.names else ""))
  ttk.Combobox(parent,textvariable=self.name,values=self.names,state="readonly",width=18).grid(row=0,column=1,padx=(8,0),pady=5);row=1
  if self.compare:
   ttk.Label(parent,text="Comparison").grid(row=row,column=0,sticky="w",pady=5);self.op=tk.StringVar(value=self.props.get("op","=="));ttk.Combobox(parent,textvariable=self.op,values=COMPARE_OPS,state="readonly",width=8).grid(row=row,column=1,sticky="w",padx=(8,0),pady=5);row+=1
  ttk.Label(parent,text="Value").grid(row=row,column=0,sticky="w",pady=5);self.value=tk.StringVar(value=str(self.props.get("value",0)));entry=ttk.Entry(parent,textvariable=self.value,width=12);entry.grid(row=row,column=1,sticky="w",padx=(8,0),pady=5);return entry
 def validate(self):
  if not self.name.get():messagebox.showerror("Utopia Game Studio","Create an RPG stat first.",parent=self);return False
  try:int(self.value.get())
  except ValueError:messagebox.showerror("Utopia Game Studio","Stat values must be whole numbers.",parent=self);return False
  return True
 def apply(self):self.result=(self.name.get(),int(self.value.get()),self.op.get() if self.compare else None)

class MovePropertiesDialog(simpledialog.Dialog):
 def __init__(self,parent,props,var_names):self.props=props;self.var_names=var_names;self.result=None;super().__init__(parent,"Move Character")
 def body(self,parent):
  ttk.Label(parent,text="Direction").grid(row=0,column=0,sticky="w",pady=5)
  current=next((name for name,value in DIRECTIONS.items() if value==(self.props.get("dx",1),self.props.get("dy",0))),"Right")
  self.direction=tk.StringVar(value=current);ttk.Combobox(parent,textvariable=self.direction,values=list(DIRECTIONS),state="readonly",width=18).grid(row=0,column=1,padx=(8,0),pady=5)
  ttk.Label(parent,text="Speed source").grid(row=1,column=0,sticky="w",pady=5)
  source=self.props.get("speed_variable","") or "Constant";self.source=tk.StringVar(value=source)
  ttk.Combobox(parent,textvariable=self.source,values=["Constant"]+self.var_names,state="readonly",width=18).grid(row=1,column=1,padx=(8,0),pady=5)
  ttk.Label(parent,text="Constant speed").grid(row=2,column=0,sticky="w",pady=5);self.speed=tk.StringVar(value=str(self.props.get("speed_percent",100)))
  speed=ttk.Spinbox(parent,textvariable=self.speed,from_=1,to=400,width=8);speed.grid(row=2,column=1,sticky="w",padx=(8,0),pady=5);ttk.Label(parent,text="% of project movement speed").grid(row=2,column=2,sticky="w",padx=(5,0))
  return speed
 def validate(self):
  try:value=int(self.speed.get())
  except ValueError:value=0
  if not 1<=value<=400:messagebox.showerror("Utopia Game Studio","Speed must be from 1% through 400%.",parent=self);return False
  return True
 def apply(self):
  source=self.source.get();self.result=(*DIRECTIONS[self.direction.get()],int(self.speed.get()),"" if source=="Constant" else source)

class RunPropertiesDialog(simpledialog.Dialog):
 def __init__(self,parent,props,var_names):self.props=props;self.var_names=var_names;self.result=None;super().__init__(parent,"Run Modifier")
 def body(self,parent):
  ttk.Label(parent,text="Speed source").grid(row=0,column=0,sticky="w",pady=5)
  source=self.props.get("speed_variable","") or "Constant";self.source=tk.StringVar(value=source)
  ttk.Combobox(parent,textvariable=self.source,values=["Constant"]+self.var_names,state="readonly",width=18).grid(row=0,column=1,padx=(8,0),pady=5)
  ttk.Label(parent,text="Constant running speed").grid(row=1,column=0,sticky="w",pady=5);self.speed=tk.StringVar(value=str(self.props.get("speed_percent",175)))
  speed=ttk.Spinbox(parent,textvariable=self.speed,from_=101,to=400,width=8);speed.grid(row=1,column=1,sticky="w",padx=(8,0),pady=5);ttk.Label(parent,text="% of walking speed").grid(row=1,column=2,sticky="w",padx=(5,0));return speed
 def validate(self):
  try:value=int(self.speed.get())
  except ValueError:value=0
  if not 101<=value<=400:messagebox.showerror("Utopia Game Studio","Running speed must be from 101% through 400%.",parent=self);return False
  return True
 def apply(self):
  source=self.source.get();self.result=(int(self.speed.get()),"" if source=="Constant" else source)

class VariableActionDialog(simpledialog.Dialog):
 def __init__(self,parent,title,props,var_names,compare=False):self.props=props;self.var_names=var_names;self.compare=compare;self.result=None;super().__init__(parent,title)
 def body(self,parent):
  ttk.Label(parent,text="Variable").grid(row=0,column=0,sticky="w",pady=5);self.name=tk.StringVar(value=self.props.get("variable",self.var_names[0] if self.var_names else ""))
  ttk.Combobox(parent,textvariable=self.name,values=self.var_names,state="readonly",width=18).grid(row=0,column=1,padx=(8,0),pady=5)
  row=1
  if self.compare:
   ttk.Label(parent,text="Comparison").grid(row=row,column=0,sticky="w",pady=5);self.op=tk.StringVar(value=self.props.get("op","=="));ttk.Combobox(parent,textvariable=self.op,values=COMPARE_OPS,state="readonly",width=8).grid(row=row,column=1,sticky="w",padx=(8,0),pady=5);row+=1
  ttk.Label(parent,text="Value").grid(row=row,column=0,sticky="w",pady=5);self.value=tk.StringVar(value=str(self.props.get("value",0)));entry=ttk.Entry(parent,textvariable=self.value,width=12);entry.grid(row=row,column=1,sticky="w",padx=(8,0),pady=5);return entry
 def validate(self):
  if not self.name.get():messagebox.showerror("Utopia Game Studio","Create a variable first.",parent=self);return False
  try:int(self.value.get())
  except ValueError:messagebox.showerror("Utopia Game Studio","Variable values must be whole numbers.",parent=self);return False
  return True
 def apply(self):self.result=(self.name.get(),int(self.value.get()),self.op.get() if self.compare else None)

def default_graph():
 return {"next_id":2,"nodes":[{"id":1,"type":"Update","x":40,"y":40,"props":{}}],"links":[]}


class BlueprintPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status):
  super().__init__(parent);self.get_project=project_getter;self.status=status;self.selected=None;self.selected_link=None;self.link_from=None;self.drag=None;self.node_clipboard=None
  tools=ttk.Frame(self,padding=6);tools.pack(fill="x")
  self.kind=tk.StringVar(value="GamePad Input");ttk.Combobox(tools,textvariable=self.kind,state="readonly",values=list(NODE_COLORS),width=18).pack(side="left")
  ttk.Button(tools,text="Add Node",command=self.add_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Variables",command=self.manage_variables).pack(side="left",padx=4)
  ttk.Button(tools,text="Connect",command=self.begin_link).pack(side="left",padx=4)
  ttk.Button(tools,text="Edit Properties",command=self.edit_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Delete",command=self.delete_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Delete Link",command=self.delete_link).pack(side="left",padx=4)
  ttk.Button(tools,text="Cut",command=self.cut_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Copy",command=self.copy_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Paste",command=self.paste_node).pack(side="left",padx=4)
  self.canvas=tk.Canvas(self,background="#20242b",scrollregion=(0,0,1900,1200),highlightthickness=0)
  xs=ttk.Scrollbar(self,orient="horizontal",command=self.canvas.xview);ys=ttk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
  self.canvas.configure(xscrollcommand=xs.set,yscrollcommand=ys.set);self.canvas.pack(fill="both",expand=True,side="left");ys.pack(fill="y",side="right");xs.pack(fill="x",side="bottom")
  self.canvas.bind("<Button-1>",self.click);self.canvas.bind("<B1-Motion>",self.move);self.canvas.bind("<ButtonRelease-1>",lambda _e:setattr(self,"drag",None));self.canvas.bind("<Double-Button-1>",lambda _e:self.edit_node())
  self.bind_all("<Delete>",self._key_delete,add="+");self.bind_all("<Control-x>",self._key_cut,add="+");self.bind_all("<Control-X>",self._key_cut,add="+");self.bind_all("<Control-c>",self._key_copy,add="+");self.bind_all("<Control-C>",self._key_copy,add="+");self.bind_all("<Control-v>",self._key_paste,add="+");self.bind_all("<Control-V>",self._key_paste,add="+")
 def graph(self):
  p=self.get_project();p.setdefault("blueprint",default_graph());p.setdefault("variables",[]);return p["blueprint"]
 def node(self,ident):return next((n for n in self.graph()["nodes"] if n["id"]==ident),None)
 def manage_variables(self):VariableManager(self,self.get_project());self.refresh()
 def refresh(self):
  self.canvas.delete("all");g=self.graph();lookup={n["id"]:n for n in g["nodes"]}
  for i,link in enumerate(g["links"]):
   a,b=lookup.get(link["from"]),lookup.get(link["to"])
   if a and b:
    selected=i==self.selected_link;self.canvas.create_line(a["x"]+190,a["y"]+40,b["x"],b["y"]+40,fill="#ff6b6b" if selected else "#e7b74f",width=5 if selected else 3,smooth=True,arrow="last",tags=(f"link_{i}","link"))
  for n in g["nodes"]:self.draw_node(n)
 def draw_node(self,n):
  x,y=n["x"],n["y"];tag=f"node_{n['id']}";outline="#ffffff" if n["id"]==self.selected else "#101216"
  self.canvas.create_rectangle(x,y,x+190,y+80,fill="#323842",outline=outline,width=3,tags=(tag,"node"))
  self.canvas.create_rectangle(x,y,x+190,y+25,fill=NODE_COLORS.get(n["type"],"#555"),outline="",tags=(tag,"node"))
  self.canvas.create_text(x+8,y+13,text=n["type"],anchor="w",fill="white",font=("Segoe UI",10,"bold"),tags=(tag,"node"))
  p=n.get("props",{});detail=""
  if n["type"]=="GamePad Input":detail="Legacy button: "+p.get("button","A")
  elif n["type"]=="Input Action":detail="Action: "+(p.get("action","") or "(not assigned)")
  elif n["type"]=="Move Character":
   d=next((name for name,value in DIRECTIONS.items() if value==(p.get("dx",0),p.get("dy",0))),"?");src=p.get("speed_variable","") or f"{p.get('speed_percent',100)}%";detail=f"{d} • Speed: {src}"
  elif n["type"]=="Run Modifier":detail="Run speed: "+(p.get("speed_variable","") or f"{p.get('speed_percent',175)}%")
  elif n["type"]=="Set Variable":detail=f"{p.get('variable','?')} = {p.get('value',0)}"
  elif n["type"]=="Change Variable":detail=f"{p.get('variable','?')} += {p.get('value',0)}"
  elif n["type"]=="Compare Variable":detail=f"{p.get('variable','?')} {p.get('op','==')} {p.get('value',0)}"
  elif n["type"]=="Set Stat":detail=f"{p.get('stat','?')} = {p.get('value',0)}"
  elif n["type"]=="Change Stat":detail=f"{p.get('stat','?')} += {p.get('value',0)}"
  elif n["type"]=="Set Max Stat":detail=f"Max {p.get('stat','?')} = {p.get('value',0)}"
  elif n["type"]=="Compare Stat":detail=f"{p.get('stat','?')} {p.get('op','==')} {p.get('value',0)}"
  elif n["type"] in ("Add Item","Remove Item","Has Item"):detail=f"{p.get('item','?')} x{p.get('quantity',1)}"
  elif n["type"]=="Equip Item":detail=f"{p.get('item','?')} -> {p.get('slot','?')}"
  elif n["type"]=="Unequip Slot":detail=f"Slot: {p.get('slot','?')}"
  elif n["type"]=="Interact":detail="Interact with nearest object"
  elif n["type"]=="Toggle Inventory":detail="Open / close inventory"
  else:detail="Execution event"
  self.canvas.create_text(x+10,y+51,text=detail,anchor="w",fill="#d7dce2",tags=(tag,"node"))
 def event_node(self,e):
  items=self.canvas.find_overlapping(self.canvas.canvasx(e.x),self.canvas.canvasy(e.y),self.canvas.canvasx(e.x),self.canvas.canvasy(e.y))
  for item in reversed(items):
   for tag in self.canvas.gettags(item):
    if tag.startswith("node_"):return int(tag[5:])
  return None
 def event_link(self,e):
  x,y=self.canvas.canvasx(e.x),self.canvas.canvasy(e.y);items=self.canvas.find_overlapping(x-5,y-5,x+5,y+5)
  for item in reversed(items):
   for tag in self.canvas.gettags(item):
    if tag.startswith("link_"):return int(tag[5:])
  return None
 def click(self,e):
  ident=self.event_node(e)
  if ident is None:
   link=self.event_link(e);self.selected=None;self.selected_link=link;self.drag=None
   if link is not None:self.status.set("Blueprint link selected - use Delete Link to remove only this connection")
   self.refresh();return
  self.selected_link=None
  if self.link_from is not None and ident!=self.link_from:
   link={"from":self.link_from,"to":ident}
   if link not in self.graph()["links"]:self.graph()["links"].append(link)
   self.link_from=None;self.status.set("Blueprint nodes connected")
  self.selected=ident;n=self.node(ident);self.drag=(ident,self.canvas.canvasx(e.x)-n["x"],self.canvas.canvasy(e.y)-n["y"]);self.refresh()
 def move(self,e):
  if not self.drag:return
  n=self.node(self.drag[0]);n["x"]=max(0,int(self.canvas.canvasx(e.x)-self.drag[1]));n["y"]=max(0,int(self.canvas.canvasy(e.y)-self.drag[2]));self.refresh()
 def add_node(self):
  g=self.graph();kind=self.kind.get();props={}
  if kind=="GamePad Input":props={"button":"A"}
  elif kind=="Input Action":props={"action":""}
  elif kind=="Move Character":props={"dx":1,"dy":0,"speed_percent":100,"speed_variable":""}
  elif kind=="Run Modifier":props={"speed_percent":175,"speed_variable":""}
  elif kind in ("Set Variable","Change Variable"):props={"variable":"","value":0}
  elif kind=="Compare Variable":props={"variable":"","op":"==","value":0}
  elif kind in ("Set Stat","Change Stat","Set Max Stat"):props={"stat":"","value":0}
  elif kind=="Compare Stat":props={"stat":"","op":"==","value":0}
  elif kind in ("Add Item","Remove Item","Has Item"):props={"item":"","quantity":1}
  elif kind=="Equip Item":props={"item":"","slot":"Main Hand"}
  elif kind=="Unequip Slot":props={"slot":"Main Hand"}
  ident=g["next_id"];g["next_id"]+=1;g["nodes"].append({"id":ident,"type":kind,"x":80+len(g["nodes"])*25,"y":80+len(g["nodes"])*20,"props":props});self.selected=ident;self.refresh()
 def begin_link(self):
  if self.selected is None:messagebox.showinfo("Utopia Game Studio","Select the source node first.");return
  self.link_from=self.selected;self.status.set("Select the destination node")
 def edit_node(self):
  n=self.node(self.selected)
  if not n:return
  vars_=blueprint_variable_names(self.get_project())
  if n["type"]=="Input Action":
   names=action_names(self.get_project())
   if not names:messagebox.showinfo("Utopia Game Studio","Create an Input Action on the Controls tab first.",parent=self);return
   value=simpledialog.askstring("Input Action","Action name:\n"+", ".join(names),initialvalue=n["props"].get("action",names[0]),parent=self)
   if value in names:n["props"]["action"]=value
   elif value:messagebox.showerror("Utopia Game Studio","Choose an existing project Input Action.",parent=self)
  elif n["type"]=="GamePad Input":
   value=simpledialog.askstring("GamePad Input","Legacy button: LEFT, RIGHT, UP, DOWN, A, B, X, or Y",initialvalue=n["props"].get("button","A"))
   if value and value.upper() in BUTTONS:n["props"]["button"]=value.upper()
   elif value:messagebox.showerror("Utopia Game Studio","Unsupported GamePad button.")
  elif n["type"]=="Move Character":
   d=MovePropertiesDialog(self,n["props"],vars_)
   if d.result:
    dx,dy,speed,var=d.result;n["props"].update(dx=dx,dy=dy,speed_percent=speed,speed_variable=var)
  elif n["type"]=="Run Modifier":
   d=RunPropertiesDialog(self,n["props"],vars_)
   if d.result:n["props"].update(speed_percent=d.result[0],speed_variable=d.result[1])
  elif n["type"] in ("Set Variable","Change Variable","Compare Variable"):
   d=VariableActionDialog(self,n["type"],n["props"],vars_,n["type"]=="Compare Variable")
   if d.result:
    name,value,op=d.result;n["props"].update(variable=name,value=value)
    if op is not None:n["props"]["op"]=op
  elif n["type"] in ("Add Item","Remove Item","Has Item","Equip Item"):
   names=item_names(self.get_project());name=simpledialog.askstring(n["type"],"Item:\n"+", ".join(names),initialvalue=n["props"].get("item",names[0] if names else ""),parent=self)
   if name in names:
    n["props"]["item"]=name
    if n["type"] in ("Add Item","Remove Item","Has Item"):n["props"]["quantity"]=simpledialog.askinteger(n["type"],"Quantity:",initialvalue=n["props"].get("quantity",1),minvalue=1,parent=self) or 1
    elif n["type"]=="Equip Item":n["props"]["slot"]=simpledialog.askstring("Equip Item","Slot:\n"+", ".join(SLOTS),initialvalue=n["props"].get("slot","Main Hand"),parent=self) or "Main Hand"
  elif n["type"]=="Unequip Slot":
   n["props"]["slot"]=simpledialog.askstring("Unequip Slot","Slot:\n"+", ".join(SLOTS),initialvalue=n["props"].get("slot","Main Hand"),parent=self) or "Main Hand"
  elif n["type"] in ("Set Stat","Change Stat","Set Max Stat","Compare Stat"):
   d=StatActionDialog(self,n["type"],n["props"],stat_names(self.get_project()),n["type"]=="Compare Stat")
   if d.result:
    name,value,op=d.result;n["props"].update(stat=name,value=value)
    if op is not None:n["props"]["op"]=op
  self.refresh()
 def _blueprint_has_focus(self):
  w=self.focus_get()
  while w is not None:
   if w is self:return True
   w=getattr(w,"master",None)
  return False
 def _key_delete(self,_e):
  if self._blueprint_has_focus():self.delete_node();return "break"
 def _key_cut(self,_e):
  if self._blueprint_has_focus():self.cut_node();return "break"
 def _key_copy(self,_e):
  if self._blueprint_has_focus():self.copy_node();return "break"
 def _key_paste(self,_e):
  if self._blueprint_has_focus():self.paste_node();return "break"
 def copy_node(self):
  n=self.node(self.selected)
  if not n:return
  self.node_clipboard=copy.deepcopy(n);self.status.set(f"Copied Blueprint node: {n['type']}")
 def cut_node(self):
  n=self.node(self.selected)
  if not n:return
  self.node_clipboard=copy.deepcopy(n);kind=n["type"];self.delete_node();self.status.set(f"Cut Blueprint node: {kind}")
 def paste_node(self):
  if not self.node_clipboard:return
  g=self.graph();n=copy.deepcopy(self.node_clipboard);n["id"]=g["next_id"];g["next_id"]+=1;n["x"]=max(0,int(n.get("x",80))+24);n["y"]=max(0,int(n.get("y",80))+24)
  g["nodes"].append(n);self.node_clipboard=copy.deepcopy(n);self.selected=n["id"];self.selected_link=None;self.link_from=None;self.refresh();self.status.set(f"Pasted Blueprint node: {n['type']}")
 def delete_node(self):
  if self.selected is None:return
  g=self.graph();g["nodes"]=[n for n in g["nodes"] if n["id"]!=self.selected];g["links"]=[x for x in g["links"] if self.selected not in (x["from"],x["to"])];self.selected=None;self.selected_link=None;self.link_from=None;self.refresh();self.status.set("Blueprint node deleted")
 def delete_link(self):
  g=self.graph()
  if self.selected_link is None or not (0<=self.selected_link<len(g["links"])):
   messagebox.showinfo("Utopia Game Studio","Click a connection line first, then choose Delete Link.");return
  link=g["links"][self.selected_link]
  if messagebox.askyesno("Utopia Game Studio",f"Remove only this connection?\n\nNode {link['from']} → Node {link['to']}"):
   del g["links"][self.selected_link];self.status.set("One Blueprint link removed")
  self.selected_link=None;self.refresh()
 def compiled_config(self):
  p=self.get_project();g=self.graph();lookup={n["id"]:n for n in g["nodes"]};outs={}
  for l in g["links"]:outs.setdefault(l["from"],[]).append(l["to"])
  preset={"Player.X":int(p.get("player_x",0)),"Player.Y":int(p.get("player_y",0)),"Player.Visible":1,"Player.Active":1,"Player.Width":int(p.get("player_width",48)),"Player.Height":int(p.get("player_height",48)),"Player.Solid":1}
  cfg={"variables":{**preset,**{v["name"]:int(v.get("value",0)) for v in variables(p)}},"stats":{s["name"]:{"current":int(s["current"]),"minimum":int(s["minimum"]),"maximum":int(s["maximum"])} for s in ensure_stats(p)},"inventory":ensure_inventory(p),"actions":[]}
  def walk(node_id,source,button=None,gates=None,path=None):
   gates=list(gates or []);path=set(path or ())
   if node_id in path:return
   path.add(node_id);node=lookup.get(node_id)
   if not node:return
   t=node["type"];pr=node.get("props",{})
   if t=="Compare Stat":
    name=pr.get("stat","")
    if name not in cfg["stats"]:return
    gates.append({"stat":name,"op":pr.get("op","=="),"value":int(pr.get("value",0))})
   elif t=="Compare Variable":
    name=pr.get("variable","")
    if name not in cfg["variables"]:return
    gates.append({"variable":name,"op":pr.get("op","=="),"value":int(pr.get("value",0))})
   elif t=="Has Item":
    name=pr.get("item","")
    if name not in item_names(p):return
    gates.append({"item":name,"quantity":max(1,int(pr.get("quantity",1)))})
   elif t in ("Move Character","Run Modifier","Set Variable","Change Variable","Set Stat","Change Stat","Set Max Stat","Add Item","Remove Item","Equip Item","Unequip Slot","Interact","Toggle Inventory"):
    action={"type":t,"source":source,"button":button,"gates":list(gates)}
    if t=="Move Character":
     action.update(dx=int(pr.get("dx",0)),dy=int(pr.get("dy",0)),speed=max(1,min(400,int(pr.get("speed_percent",100)))),speed_variable=pr.get("speed_variable","") if pr.get("speed_variable","") in cfg["variables"] else "")
    elif t=="Run Modifier":
     action.update(speed=max(101,min(400,int(pr.get("speed_percent",175)))),speed_variable=pr.get("speed_variable","") if pr.get("speed_variable","") in cfg["variables"] else "")
    elif t in ("Set Variable","Change Variable"):
     name=pr.get("variable","")
     if name in cfg["variables"]:action.update(variable=name,value=int(pr.get("value",0)));cfg["actions"].append(action)
     action=None
    elif t in ("Add Item","Remove Item"):
     name=pr.get("item","")
     if name in item_names(p):action.update(item=name,quantity=max(1,int(pr.get("quantity",1))));cfg["actions"].append(action)
     action=None
    elif t=="Equip Item":
     name=pr.get("item","");slot=pr.get("slot","Main Hand")
     if name in item_names(p) and slot in SLOTS:action.update(item=name,slot=slot);cfg["actions"].append(action)
     action=None
    elif t=="Unequip Slot":
     slot=pr.get("slot","Main Hand")
     if slot in SLOTS:action.update(slot=slot);cfg["actions"].append(action)
     action=None
    elif t in ("Set Stat","Change Stat","Set Max Stat"):
     name=pr.get("stat","")
     if name in cfg["stats"]:action.update(stat=name,value=int(pr.get("value",0)));cfg["actions"].append(action)
     action=None
    elif t in ("Interact","Toggle Inventory"):
     pass
    if action is not None:cfg["actions"].append(action)
   for child in outs.get(node_id,[]):walk(child,source,button,gates,path)
  for n in g["nodes"]:
   if n["type"]=="Start":
    for child in outs.get(n["id"],[]):walk(child,"start",None,[],{n["id"]})
   elif n["type"]=="Update":
    for child in outs.get(n["id"],[]):walk(child,"update",None,[],{n["id"]})
   elif n["type"]=="GamePad Input":
    button=n.get("props",{}).get("button","")
    if button in BUTTONS:
     for child in outs.get(n["id"],[]):walk(child,"input",button,[],{n["id"]})
   elif n["type"]=="Input Action":
    action_name=n.get("props",{}).get("action","")
    if action_name in action_names(p):
     for child in outs.get(n["id"],[]):walk(child,"action",action_name,[],{n["id"]})
  return cfg
 def movement_config(self):return self.compiled_config()
 def write_header(self,path):
  cfg=self.compiled_config();names=list(cfg["variables"]);index={n:i for i,n in enumerate(names)};statnames=list(cfg["stats"]);statindex={n:i for i,n in enumerate(statnames)}
  init=", ".join(str(cfg["variables"][n]) for n in names) or "0"
  stat_init=", ".join(str(cfg["stats"][n]["current"]) for n in statnames) or "0";stat_min=", ".join(str(cfg["stats"][n]["minimum"]) for n in statnames) or "0";stat_max=", ".join(str(cfg["stats"][n]["maximum"]) for n in statnames) or "0"
  lines=["#pragma once","#include <stdint.h>",f"#define BP_VAR_COUNT {len(names)}",f"static int bp_vars[{max(1,len(names))}] = {{{init}}};",f"#define RPG_STAT_COUNT {len(statnames)}",f"static int rpg_stats[{max(1,len(statnames))}] = {{{stat_init}}};",f"static int rpg_stat_min[{max(1,len(statnames))}] = {{{stat_min}}};",f"static int rpg_stat_max[{max(1,len(statnames))}] = {{{stat_max}}};"]
  for n,i in index.items():lines.append(f"#define BP_VAR_{clean_name(n).upper()} {i}")
  for n,i in statindex.items():lines.append(f"#define RPG_STAT_{clean_name(n).upper()} {i}")
  lines += [
   "static inline int bp_compare_value(int left,int op,int right){switch(op){case 0:return left==right;case 1:return left!=right;case 2:return left<right;case 3:return left<=right;case 4:return left>right;case 5:return left>=right;default:return 1;}}",
   "static inline int bp_gate(int idx,int op,int value){return idx<0?1:bp_compare_value(bp_vars[idx],op,value);}",
   "static inline int bp_speed_percent(int idx,int fallback,int lo,int hi){int value=idx>=0?bp_vars[idx]:fallback;if(value<lo)value=lo;if(value>hi)value=hi;return value;}",
   "static inline void rpg_clamp(int idx){if(idx<0)return;if(rpg_stats[idx]<rpg_stat_min[idx])rpg_stats[idx]=rpg_stat_min[idx];if(rpg_stats[idx]>rpg_stat_max[idx])rpg_stats[idx]=rpg_stat_max[idx];}"
  ]
  def gate_expr(action):
   parts=[]
   for g in action.get("gates",[]):
    if "stat" in g:parts.append(f"bp_compare_value(rpg_stats[{statindex.get(g['stat'],-1)}],{OP_CODES.get(g['op'],0)},{int(g['value'])})")
    else:parts.append(f"bp_gate({index.get(g['variable'],-1)},{OP_CODES.get(g['op'],0)},{int(g['value'])})")
   return " && ".join(parts) if parts else "1"
  def source_expr(action,trigger=False):
   source=action["source"]
   if source=="start":return "first_frame"
   if source=="update":return "1"
   button=action.get("button","A")
   return f"({'trigger' if trigger else 'hold'} & VPAD_BUTTON_{button})"
  lines.append("static inline void BPApplyFrameActions(uint32_t trigger,int first_frame){")
  for a in cfg["actions"]:
   if a["type"] not in ("Set Variable","Change Variable","Set Stat","Change Stat","Set Max Stat"):continue
   cond=f"({source_expr(a,True)}) && ({gate_expr(a)})"
   if a["type"] in ("Set Variable","Change Variable"):
    idx=index[a["variable"]];op="=" if a["type"]=="Set Variable" else "+=";lines.append(f" if({cond}) bp_vars[{idx}] {op} {int(a['value'])};")
   else:
    idx=statindex[a["stat"]]
    if a["type"]=="Set Max Stat":lines.append(f" if({cond}){{rpg_stat_max[{idx}]={int(a['value'])};if(rpg_stat_max[{idx}]<rpg_stat_min[{idx}])rpg_stat_max[{idx}]=rpg_stat_min[{idx}];rpg_clamp({idx});}}")
    else:
     op="=" if a["type"]=="Set Stat" else "+=";lines.append(f" if({cond}){{rpg_stats[{idx}] {op} {int(a['value'])};rpg_clamp({idx});}}")
  lines.append("}")
  lines.append("static inline void BPCollectMovement(uint32_t hold,int first_frame,int *move_x100,int *move_y100,int *run_percent){")
  lines.append(" *move_x100=0; *move_y100=0; *run_percent=100;")
  for a in cfg["actions"]:
   if a["type"] not in ("Move Character","Run Modifier"):continue
   cond=f"({source_expr(a,False)}) && ({gate_expr(a)})";vi=index.get(a.get("speed_variable",""),-1)
   if a["type"]=="Move Character":
    lines.append(f" if({cond}){{int s=bp_speed_percent({vi},{a['speed']},1,400);*move_x100 += {a['dx']}*s;*move_y100 += {a['dy']}*s;}}")
   else:
    lines.append(f" if({cond}) *run_percent=bp_speed_percent({vi},{a['speed']},101,400);")
  lines.append("}")
  path.write_text("\n".join(lines)+"\n",encoding="utf-8")

