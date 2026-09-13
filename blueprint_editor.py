"""Original node-based visual scripting panel for Utopia Game Studio."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

NODE_COLORS={"Start":"#6b4f8a","Update":"#8a4f6b","GamePad Input":"#315d83","Move Character":"#3f7a55","Run Modifier":"#8a6335"}
BUTTONS=("LEFT","RIGHT","UP","DOWN","A","B","X","Y")
DIRECTIONS={"Left":(-1,0),"Right":(1,0),"Up":(0,-1),"Down":(0,1)}

class MovePropertiesDialog(simpledialog.Dialog):
 def __init__(self,parent,props):self.props=props;self.result=None;super().__init__(parent,"Move Character")
 def body(self,parent):
  ttk.Label(parent,text="Direction").grid(row=0,column=0,sticky="w",pady=5);current=next((name for name,value in DIRECTIONS.items() if value==(self.props.get("dx",1),self.props.get("dy",0))),"Right")
  self.direction=tk.StringVar(value=current);ttk.Combobox(parent,textvariable=self.direction,values=list(DIRECTIONS),state="readonly",width=18).grid(row=0,column=1,padx=(8,0),pady=5)
  ttk.Label(parent,text="Speed").grid(row=1,column=0,sticky="w",pady=5);self.speed=tk.StringVar(value=str(self.props.get("speed_percent",100)))
  speed=ttk.Spinbox(parent,textvariable=self.speed,from_=1,to=400,width=8);speed.grid(row=1,column=1,sticky="w",padx=(8,0),pady=5);ttk.Label(parent,text="% of project movement speed").grid(row=1,column=2,sticky="w",padx=(5,0))
  return speed
 def validate(self):
  try:value=int(self.speed.get())
  except ValueError:value=0
  if not 1<=value<=400:messagebox.showerror("Utopia Game Studio","Speed must be from 1% through 400%.",parent=self);return False
  return True
 def apply(self):self.result=(*DIRECTIONS[self.direction.get()],int(self.speed.get()))

class RunPropertiesDialog(simpledialog.Dialog):
 def __init__(self,parent,props):self.props=props;self.result=None;super().__init__(parent,"Run Modifier")
 def body(self,parent):
  ttk.Label(parent,text="Running speed").grid(row=0,column=0,sticky="w",pady=5);self.speed=tk.StringVar(value=str(self.props.get("speed_percent",175)))
  speed=ttk.Spinbox(parent,textvariable=self.speed,from_=101,to=400,width=8);speed.grid(row=0,column=1,sticky="w",padx=(8,0),pady=5);ttk.Label(parent,text="% of walking speed").grid(row=0,column=2,sticky="w",padx=(5,0));return speed
 def validate(self):
  try:value=int(self.speed.get())
  except ValueError:value=0
  if not 101<=value<=400:messagebox.showerror("Utopia Game Studio","Running speed must be from 101% through 400%.",parent=self);return False
  return True
 def apply(self):self.result=int(self.speed.get())

def default_graph():
 nodes=[];links=[];ident=1
 nodes.append({"id":ident,"type":"Update","x":40,"y":40,"props":{}});ident+=1
 for row,(button,dx,dy) in enumerate((("LEFT",-1,0),("RIGHT",1,0),("UP",0,-1),("DOWN",0,1))):
  source=ident;nodes.append({"id":source,"type":"GamePad Input","x":260,"y":30+row*115,"props":{"button":button}});ident+=1
  target=ident;nodes.append({"id":target,"type":"Move Character","x":520,"y":30+row*115,"props":{"dx":dx,"dy":dy,"speed_percent":100}});ident+=1
  links.append({"from":source,"to":target})
 source=ident;nodes.append({"id":source,"type":"GamePad Input","x":260,"y":490,"props":{"button":"B"}});ident+=1
 target=ident;nodes.append({"id":target,"type":"Run Modifier","x":520,"y":490,"props":{"speed_percent":175}});ident+=1;links.append({"from":source,"to":target})
 return {"next_id":ident,"nodes":nodes,"links":links}

class BlueprintPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status):
  super().__init__(parent);self.get_project=project_getter;self.status=status;self.selected=None;self.link_from=None;self.drag=None
  tools=ttk.Frame(self,padding=6);tools.pack(fill="x")
  self.kind=tk.StringVar(value="GamePad Input");ttk.Combobox(tools,textvariable=self.kind,state="readonly",values=list(NODE_COLORS),width=18).pack(side="left")
  ttk.Button(tools,text="Add Node",command=self.add_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Connect",command=self.begin_link).pack(side="left",padx=4)
  ttk.Button(tools,text="Edit Properties",command=self.edit_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Delete",command=self.delete_node).pack(side="left",padx=4)
  ttk.Button(tools,text="Clear Links",command=self.clear_links).pack(side="left",padx=4)
  ttk.Label(tools,text="Click and drag nodes • Connect: select source, click Connect, then select destination").pack(side="right")
  self.canvas=tk.Canvas(self,background="#20242b",scrollregion=(0,0,1600,1000),highlightthickness=0)
  xs=ttk.Scrollbar(self,orient="horizontal",command=self.canvas.xview);ys=ttk.Scrollbar(self,orient="vertical",command=self.canvas.yview)
  self.canvas.configure(xscrollcommand=xs.set,yscrollcommand=ys.set);self.canvas.pack(fill="both",expand=True,side="left");ys.pack(fill="y",side="right");xs.pack(fill="x",side="bottom")
  self.canvas.bind("<Button-1>",self.click);self.canvas.bind("<B1-Motion>",self.move);self.canvas.bind("<ButtonRelease-1>",lambda _e:setattr(self,"drag",None));self.canvas.bind("<Double-Button-1>",lambda _e:self.edit_node())
 def graph(self):
  p=self.get_project();p.setdefault("blueprint",default_graph());return p["blueprint"]
 def node(self,ident):return next((n for n in self.graph()["nodes"] if n["id"]==ident),None)
 def refresh(self):
  self.canvas.delete("all");g=self.graph();lookup={n["id"]:n for n in g["nodes"]}
  for link in g["links"]:
   a,b=lookup.get(link["from"]),lookup.get(link["to"])
   if a and b:self.canvas.create_line(a["x"]+180,a["y"]+40,b["x"],b["y"]+40,fill="#e7b74f",width=3,smooth=True,arrow="last")
  for n in g["nodes"]:self.draw_node(n)
 def draw_node(self,n):
  x,y=n["x"],n["y"];tag=f"node_{n['id']}";outline="#ffffff" if n["id"]==self.selected else "#101216"
  self.canvas.create_rectangle(x,y,x+180,y+80,fill="#323842",outline=outline,width=3,tags=(tag,"node"))
  self.canvas.create_rectangle(x,y,x+180,y+25,fill=NODE_COLORS[n["type"]],outline="",tags=(tag,"node"))
  self.canvas.create_text(x+8,y+13,text=n["type"],anchor="w",fill="white",font=("Segoe UI",10,"bold"),tags=(tag,"node"))
  props=n.get("props",{});detail=""
  if n["type"]=="GamePad Input":detail="Button: "+props.get("button","A")
  elif n["type"]=="Move Character":
   direction=next((name for name,value in DIRECTIONS.items() if value==(props.get("dx",0),props.get("dy",0))),f"{props.get('dx',0)}, {props.get('dy',0)}");detail=f"{direction} • Speed: {props.get('speed_percent',100)}%"
  elif n["type"]=="Run Modifier":detail=f"Running speed: {props.get('speed_percent',175)}%"
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
  if kind=="Move Character":props={"dx":1,"dy":0,"speed_percent":100}
  if kind=="Run Modifier":props={"speed_percent":175}
  ident=g["next_id"];g["next_id"]+=1;g["nodes"].append({"id":ident,"type":kind,"x":80+len(g["nodes"])*25,"y":80+len(g["nodes"])*20,"props":props});self.selected=ident;self.refresh()
 def begin_link(self):
  if self.selected is None:messagebox.showinfo("Utopia Game Studio","Select the source node first.");return
  self.link_from=self.selected;self.status.set("Select the destination node")
 def edit_node(self):
  n=self.node(self.selected)
  if not n:return
  if n["type"]=="GamePad Input":
   value=simpledialog.askstring("GamePad Input","Button: LEFT, RIGHT, UP, DOWN, A, B, X, or Y",initialvalue=n["props"].get("button","A"))
   if value and value.upper() in BUTTONS:n["props"]["button"]=value.upper()
   elif value:messagebox.showerror("Utopia Game Studio","Unsupported GamePad button.")
  elif n["type"]=="Move Character":
   dialog=MovePropertiesDialog(self,n["props"])
   if dialog.result:
    dx,dy,speed=dialog.result;n["props"].update(dx=dx,dy=dy,speed_percent=speed)
  elif n["type"]=="Run Modifier":
   dialog=RunPropertiesDialog(self,n["props"])
   if dialog.result:n["props"]["speed_percent"]=dialog.result
  self.refresh()
 def delete_node(self):
  if self.selected is None:return
  g=self.graph();g["nodes"]=[n for n in g["nodes"] if n["id"]!=self.selected];g["links"]=[x for x in g["links"] if self.selected not in (x["from"],x["to"])];self.selected=None;self.refresh()
 def clear_links(self):
  if messagebox.askyesno("Utopia Game Studio","Remove every blueprint connection?"):self.graph()["links"]=[];self.refresh()
 def movement_config(self):
  g=self.graph();lookup={n["id"]:n for n in g["nodes"]};moves={b:0 for b in ("LEFT","RIGHT","UP","DOWN")};run_button="B";run_speed=0
  for link in g["links"]:
   a,b=lookup.get(link["from"]),lookup.get(link["to"])
   if not a or not b or a["type"]!="GamePad Input":continue
   button=a["props"].get("button","")
   if b["type"]=="Run Modifier" and button in BUTTONS:run_button=button;run_speed=max(101,min(400,int(b["props"].get("speed_percent",175))));continue
   if b["type"]=="Move Character" and button in moves:
    dx,dy=b["props"].get("dx",0),b["props"].get("dy",0)
    expected={"LEFT":(-1,0),"RIGHT":(1,0),"UP":(0,-1),"DOWN":(0,1)}[button]
    if (dx,dy)==expected:moves[button]=max(1,min(400,int(b["props"].get("speed_percent",100))))
  return moves,run_button,run_speed
 def write_header(self,path):
  moves,run_button,run_speed=self.movement_config()
  lines=["#pragma once"]
  for key,speed in moves.items():lines.extend((f"#define BP_MOVE_{key} {int(bool(speed))}",f"#define BP_MOVE_{key}_SPEED {speed or 100}"))
  lines.extend((f"#define BP_RUN_ENABLED {int(bool(run_speed))}",f"#define BP_RUN_BUTTON VPAD_BUTTON_{run_button}",f"#define BP_RUN_SPEED {run_speed or 175}"))
  text="\n".join(lines)+"\n"
  path.write_text(text,encoding="utf-8")
