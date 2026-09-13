"""Original node-based visual scripting panel for Utopia Game Studio."""
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

NODE_COLORS={
 "Start":"#6b4f8a","Update":"#8a4f6b","GamePad Input":"#315d83",
 "Move Character":"#3f7a55","Run Modifier":"#8a6335",
 "Set Variable":"#75558c","Change Variable":"#66519a","Compare Variable":"#8c5555"
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

def variable_names(project):return [v["name"] for v in variables(project)]

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
 nodes=[];links=[];ident=1
 nodes.append({"id":ident,"type":"Update","x":40,"y":40,"props":{}});ident+=1
 for row,(button,dx,dy) in enumerate((("LEFT",-1,0),("RIGHT",1,0),("UP",0,-1),("DOWN",0,1))):
  source=ident;nodes.append({"id":source,"type":"GamePad Input","x":260,"y":30+row*115,"props":{"button":button}});ident+=1
  target=ident;nodes.append({"id":target,"type":"Move Character","x":520,"y":30+row*115,"props":{"dx":dx,"dy":dy,"speed_percent":100,"speed_variable":""}});ident+=1
  links.append({"from":source,"to":target})
 source=ident;nodes.append({"id":source,"type":"GamePad Input","x":260,"y":490,"props":{"button":"B"}});ident+=1
 target=ident;nodes.append({"id":target,"type":"Run Modifier","x":520,"y":490,"props":{"speed_percent":175,"speed_variable":""}});ident+=1;links.append({"from":source,"to":target})
 return {"next_id":ident,"nodes":nodes,"links":links}

class BlueprintPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status):
  super().__init__(parent);self.get_project=project_getter;self.status=status;self.selected=None;self.link_from=None;self.drag=None
  tools=ttk.Frame(self,padding=6);tools.pack(fill="x")
  self.kind=tk.StringVar(value="GamePad Input");ttk.Combobox(tools,textvariable=self.kind,state="readonly",values=list(NODE_COLORS),width=18).pack(side="left")
  ttk.Button(tools,text="Add Node",command=self.add_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Variables",command=self.manage_variables).pack(side="left",padx=4)
  ttk.Button(tools,text="Connect",command=self.begin_link).pack(side="left",padx=4)
  ttk.Button(tools,text="Edit Properties",command=self.edit_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Delete",command=self.delete_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Clear Links",command=self.clear_links).pack(side="left",padx=4)
  self.canvas=tk.Canvas(self,background="#20242b",scrollregion=(0,0,1900,1200),highlightthickness=0)
  xs=ttk.Scrollbar(self,orient="horizontal",command=self.canvas.xview);ys=ttk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
  self.canvas.configure(xscrollcommand=xs.set,yscrollcommand=ys.set);self.canvas.pack(fill="both",expand=True,side="left");ys.pack(fill="y",side="right");xs.pack(fill="x",side="bottom")
  self.canvas.bind("<Button-1>",self.click);self.canvas.bind("<B1-Motion>",self.move);self.canvas.bind("<ButtonRelease-1>",lambda _e:setattr(self,"drag",None));self.canvas.bind("<Double-Button-1>",lambda _e:self.edit_node())
 def graph(self):
  p=self.get_project();p.setdefault("blueprint",default_graph());p.setdefault("variables",[]);return p["blueprint"]
 def node(self,ident):return next((n for n in self.graph()["nodes"] if n["id"]==ident),None)
 def manage_variables(self):VariableManager(self,self.get_project());self.refresh()
 def refresh(self):
  self.canvas.delete("all");g=self.graph();lookup={n["id"]:n for n in g["nodes"]}
  for link in g["links"]:
   a,b=lookup.get(link["from"]),lookup.get(link["to"])
   if a and b:self.canvas.create_line(a["x"]+190,a["y"]+40,b["x"],b["y"]+40,fill="#e7b74f",width=3,smooth=True,arrow="last")
  for n in g["nodes"]:self.draw_node(n)
 def draw_node(self,n):
  x,y=n["x"],n["y"];tag=f"node_{n['id']}";outline="#ffffff" if n["id"]==self.selected else "#101216"
  self.canvas.create_rectangle(x,y,x+190,y+80,fill="#323842",outline=outline,width=3,tags=(tag,"node"))
  self.canvas.create_rectangle(x,y,x+190,y+25,fill=NODE_COLORS.get(n["type"],"#555"),outline="",tags=(tag,"node"))
  self.canvas.create_text(x+8,y+13,text=n["type"],anchor="w",fill="white",font=("Segoe UI",10,"bold"),tags=(tag,"node"))
  p=n.get("props",{});detail=""
  if n["type"]=="GamePad Input":detail="Button: "+p.get("button","A")
  elif n["type"]=="Move Character":
   d=next((name for name,value in DIRECTIONS.items() if value==(p.get("dx",0),p.get("dy",0))),"?");src=p.get("speed_variable","") or f"{p.get('speed_percent',100)}%";detail=f"{d} • Speed: {src}"
  elif n["type"]=="Run Modifier":detail="Run speed: "+(p.get("speed_variable","") or f"{p.get('speed_percent',175)}%")
  elif n["type"]=="Set Variable":detail=f"{p.get('variable','?')} = {p.get('value',0)}"
  elif n["type"]=="Change Variable":detail=f"{p.get('variable','?')} += {p.get('value',0)}"
  elif n["type"]=="Compare Variable":detail=f"{p.get('variable','?')} {p.get('op','==')} {p.get('value',0)}"
  else:detail="Execution event"
  self.canvas.create_text(x+10,y+51,text=detail,anchor="w",fill="#d7dce2",tags=(tag,"node"))
 def event_node(self,e):
  items=self.canvas.find_overlapping(self.canvas.canvasx(e.x),self.canvas.canvasy(e.y),self.canvas.canvasx(e.x),self.canvas.canvasy(e.y))
  for item in reversed(items):
   for tag in self.canvas.gettags(item):
    if tag.startswith("node_"):return int(tag[5:])
  return None
 def click(self,e):
  ident=self.event_node(e)
  if ident is None:self.selected=None;self.refresh();return
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
  elif kind=="Move Character":props={"dx":1,"dy":0,"speed_percent":100,"speed_variable":""}
  elif kind=="Run Modifier":props={"speed_percent":175,"speed_variable":""}
  elif kind in ("Set Variable","Change Variable"):props={"variable":"","value":0}
  elif kind=="Compare Variable":props={"variable":"","op":"==","value":0}
  ident=g["next_id"];g["next_id"]+=1;g["nodes"].append({"id":ident,"type":kind,"x":80+len(g["nodes"])*25,"y":80+len(g["nodes"])*20,"props":props});self.selected=ident;self.refresh()
 def begin_link(self):
  if self.selected is None:messagebox.showinfo("Utopia Game Studio","Select the source node first.");return
  self.link_from=self.selected;self.status.set("Select the destination node")
 def edit_node(self):
  n=self.node(self.selected)
  if not n:return
  vars_=variable_names(self.get_project())
  if n["type"]=="GamePad Input":
   value=simpledialog.askstring("GamePad Input","Button: LEFT, RIGHT, UP, DOWN, A, B, X, or Y",initialvalue=n["props"].get("button","A"))
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
  self.refresh()
 def delete_node(self):
  if self.selected is None:return
  g=self.graph();g["nodes"]=[n for n in g["nodes"] if n["id"]!=self.selected];g["links"]=[x for x in g["links"] if self.selected not in (x["from"],x["to"])];self.selected=None;self.refresh()
 def clear_links(self):
  if messagebox.askyesno("Utopia Game Studio","Remove every blueprint connection?"):self.graph()["links"]=[];self.refresh()
 def compiled_config(self):
  p=self.get_project();g=self.graph();lookup={n["id"]:n for n in g["nodes"]};outs={}
  for l in g["links"]:outs.setdefault(l["from"],[]).append(l["to"])
  cfg={"variables":{v["name"]:int(v.get("value",0)) for v in variables(p)},"moves":{b:{"enabled":False,"speed":100,"speed_variable":"","gate":None} for b in ("LEFT","RIGHT","UP","DOWN")},"run":{"button":"B","enabled":False,"speed":175,"speed_variable":"","gate":None},"actions":{b:[] for b in BUTTONS}}
  def add_action(button,node,gate=None):
   t=node["type"];pr=node.get("props",{})
   if t in ("Set Variable","Change Variable") and pr.get("variable") in cfg["variables"]:
    cfg["actions"][button].append({"type":"set" if t=="Set Variable" else "change","variable":pr["variable"],"value":int(pr.get("value",0)),"gate":gate})
   elif t=="Move Character" and button in cfg["moves"]:
    expected={"LEFT":(-1,0),"RIGHT":(1,0),"UP":(0,-1),"DOWN":(0,1)}[button]
    if (pr.get("dx",0),pr.get("dy",0))==expected:cfg["moves"][button]={"enabled":True,"speed":max(1,min(400,int(pr.get("speed_percent",100)))),"speed_variable":pr.get("speed_variable","") if pr.get("speed_variable","") in cfg["variables"] else "","gate":gate}
   elif t=="Run Modifier":
    cfg["run"]={"button":button,"enabled":True,"speed":max(101,min(400,int(pr.get("speed_percent",175)))),"speed_variable":pr.get("speed_variable","") if pr.get("speed_variable","") in cfg["variables"] else "","gate":gate}
  for n in g["nodes"]:
   if n["type"]!="GamePad Input":continue
   button=n.get("props",{}).get("button","")
   if button not in BUTTONS:continue
   for target_id in outs.get(n["id"],[]):
    target=lookup.get(target_id)
    if not target:continue
    if target["type"]=="Compare Variable":
     pr=target.get("props",{});name=pr.get("variable","")
     if name not in cfg["variables"]:continue
     gate={"variable":name,"op":pr.get("op","=="),"value":int(pr.get("value",0))}
     for next_id in outs.get(target["id"],[]):
      child=lookup.get(next_id)
      if child:add_action(button,child,gate)
    else:add_action(button,target,None)
  return cfg
 def movement_config(self):return self.compiled_config()
 def write_header(self,path):
  cfg=self.compiled_config();names=list(cfg["variables"]);index={n:i for i,n in enumerate(names)}
  init=", ".join(str(cfg["variables"][n]) for n in names) or "0"
  lines=["#pragma once","#include <stdint.h>",f"#define BP_VAR_COUNT {len(names)}",f"static int bp_vars[{max(1,len(names))}] = {{{init}}};"]
  for n,i in index.items():lines.append(f"#define BP_VAR_{clean_name(n).upper()} {i}")
  lines += [
   "static inline int bp_compare_value(int left,int op,int right){switch(op){case 0:return left==right;case 1:return left!=right;case 2:return left<right;case 3:return left<=right;case 4:return left>right;case 5:return left>=right;default:return 1;}}",
   "static inline int bp_gate(int idx,int op,int value){return idx<0?1:bp_compare_value(bp_vars[idx],op,value);}"
  ]
  def gate_fields(g):
   if not g:return (-1,0,0)
   return (index.get(g["variable"],-1),OP_CODES.get(g["op"],0),int(g["value"]))
  for key,m in cfg["moves"].items():
   gi,go,gv=gate_fields(m["gate"]);vi=index.get(m["speed_variable"],-1)
   lines += [f"#define BP_MOVE_{key} {int(m['enabled'])}",f"#define BP_MOVE_{key}_SPEED {m['speed']}",f"#define BP_MOVE_{key}_SPEED_VAR {vi}",f"#define BP_MOVE_{key}_GATE_VAR {gi}",f"#define BP_MOVE_{key}_GATE_OP {go}",f"#define BP_MOVE_{key}_GATE_VALUE {gv}"]
  run=cfg["run"];gi,go,gv=gate_fields(run["gate"]);vi=index.get(run["speed_variable"],-1)
  lines += [f"#define BP_RUN_ENABLED {int(run['enabled'])}",f"#define BP_RUN_BUTTON VPAD_BUTTON_{run['button']}",f"#define BP_RUN_SPEED {run['speed']}",f"#define BP_RUN_SPEED_VAR {vi}",f"#define BP_RUN_GATE_VAR {gi}",f"#define BP_RUN_GATE_OP {go}",f"#define BP_RUN_GATE_VALUE {gv}"]
  lines.append("static inline void BPApplyTriggered(uint32_t trigger){")
  for button,actions in cfg["actions"].items():
   for a in actions:
    idx=index[a["variable"]];gi,go,gv=gate_fields(a["gate"]);op="=" if a["type"]=="set" else "+="
    lines.append(f" if((trigger & VPAD_BUTTON_{button}) && bp_gate({gi},{go},{gv})) bp_vars[{idx}] {op} {int(a['value'])};")
  lines.append("}")
  path.write_text("\n".join(lines)+"\n",encoding="utf-8")
