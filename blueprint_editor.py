"""Original node-based visual scripting panel for Utopia Game Studio."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

NODE_COLORS={"Start":"#6b4f8a","Update":"#8a4f6b","GamePad Input":"#315d83","Move Character":"#3f7a55"}
BUTTONS=("LEFT","RIGHT","UP","DOWN","A","B","X","Y")

def default_graph():
 nodes=[];links=[];ident=1
 nodes.append({"id":ident,"type":"Update","x":40,"y":40,"props":{}});ident+=1
 for row,(button,dx,dy) in enumerate((("LEFT",-1,0),("RIGHT",1,0),("UP",0,-1),("DOWN",0,1))):
  source=ident;nodes.append({"id":source,"type":"GamePad Input","x":260,"y":30+row*115,"props":{"button":button}});ident+=1
  target=ident;nodes.append({"id":target,"type":"Move Character","x":520,"y":30+row*115,"props":{"dx":dx,"dy":dy}});ident+=1
  links.append({"from":source,"to":target})
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
  elif n["type"]=="Move Character":detail=f"Direction: {props.get('dx',0)}, {props.get('dy',0)}"
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
  if kind=="Move Character":props={"dx":1,"dy":0}
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
   value=simpledialog.askstring("Move Character","Direction as X,Y (-1,0 moves left):",initialvalue=f"{n['props'].get('dx',0)},{n['props'].get('dy',0)}")
   try:
    if value:
     dx,dy=(int(x.strip()) for x in value.split(","));n["props"].update(dx=max(-1,min(1,dx)),dy=max(-1,min(1,dy)))
   except ValueError:messagebox.showerror("Utopia Game Studio","Enter two whole numbers separated by a comma.")
  self.refresh()
 def delete_node(self):
  if self.selected is None:return
  g=self.graph();g["nodes"]=[n for n in g["nodes"] if n["id"]!=self.selected];g["links"]=[x for x in g["links"] if self.selected not in (x["from"],x["to"])];self.selected=None;self.refresh()
 def clear_links(self):
  if messagebox.askyesno("Utopia Game Studio","Remove every blueprint connection?"):self.graph()["links"]=[];self.refresh()
 def write_header(self,path):
  g=self.graph();lookup={n["id"]:n for n in g["nodes"]};moves={b:False for b in ("LEFT","RIGHT","UP","DOWN")}
  for link in g["links"]:
   a,b=lookup.get(link["from"]),lookup.get(link["to"])
   if not a or not b or a["type"]!="GamePad Input" or b["type"]!="Move Character":continue
   button=a["props"].get("button","");dx,dy=b["props"].get("dx",0),b["props"].get("dy",0)
   if button in moves:
    expected={"LEFT":(-1,0),"RIGHT":(1,0),"UP":(0,-1),"DOWN":(0,1)}[button];moves[button]=(dx,dy)==expected
  text="#pragma once\n"+"\n".join(f"#define BP_MOVE_{k} {int(v)}" for k,v in moves.items())+"\n"
  path.write_text(text,encoding="utf-8")
