#!/usr/bin/env python3
"""Utopia Game Studio v1.95.001.003 - 2D/2.5D Wii U game creator."""
import base64, json, shutil, struct, zlib
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk
from blueprint_editor import BlueprintPanel, default_graph
from game_framework import FrameworkPanel, GameRuntime, default_framework, ensure_framework
from splash_part1 import SPLASH_PART_1
from splash_part2 import SPLASH_PART_2

APP_NAME, VERSION = "Utopia Game Studio", "1.95.001.003"
ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "runtime_template"
ANIMATION_STATES=("idle_down","idle_left","idle_right","idle_up","walk_down","walk_left","walk_right","walk_up")

def show_splash(duration_ms=1800):
 """Display the embedded Utopia editor splash before the main window opens."""
 splash=tk.Tk();splash.overrideredirect(True);splash.configure(background="black")
 try:
  source=tk.PhotoImage(data=SPLASH_PART_1+SPLASH_PART_2);shown=source.zoom(2,2)
  splash._source_image=source;splash._shown_image=shown
  tk.Label(splash,image=shown,borderwidth=0,highlightthickness=0).pack()
  splash.update_idletasks();width,height=shown.width(),shown.height()
  x=max(0,(splash.winfo_screenwidth()-width)//2);y=max(0,(splash.winfo_screenheight()-height)//2)
  splash.geometry(f"{width}x{height}+{x}+{y}");splash.lift()
  try:splash.attributes("-topmost",True)
  except tk.TclError:pass
  splash.after(150,lambda:splash.attributes("-topmost",False))
  splash.after(duration_ms,splash.destroy);splash.mainloop()
 except tk.TclError:
  splash.destroy()
DEFAULT = {"format":"utopia-project-8","title":"My Utopia RPG","author":"Homebrew Developer",
 "game_style":"2D / 2.5D RPG","background":"#18365c","player_color":"#f4d35e",
 "player_x":560,"player_y":320,"player_width":80,"player_height":80,"player_speed":6,
 "animations":{},"active_animation":"","directional_animations":{key:"" for key in ANIMATION_STATES},"blueprint":default_graph(),
 "tiles":[],"room_map":[-1]*(40*23),"variables":[],"framework":default_framework()}

def fresh(): return json.loads(json.dumps(DEFAULT))
def rgba(value): return "0x" + value.lstrip("#").upper() + "FFu"

def png_rgba(width,height,pixels):
 def chunk(kind,data):
  return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
 raw=b"".join(b"\0"+bytes(channel for pixel in pixels[y*width:(y+1)*width] for channel in pixel) for y in range(height))
 return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")

class PixelFrameEditor(tk.Toplevel):
 def __init__(self,parent,width,height,pixels=None,title="Create frame",copy_sources=None):
  super().__init__(parent);self.title(title);self.transient(parent);self.resizable(False,False);self.result=None
  self.width,self.height=width,height;self.pixels=list(pixels or [(0,0,0,0)]*(width*height));self.color="#f4d35e";self.cells=[];self.shape_start=None;self.shape_base=None
  self.scale=max(4,min(20,512//max(width,height)));cw,ch=width*self.scale,height*self.scale
  tools=ttk.Frame(self,padding=8);tools.pack(fill="x");self.tool=tk.StringVar(value="pencil");self.filled=tk.BooleanVar(value=False)
  self.color_button=tk.Button(tools,text="Draw color",background=self.color,command=self.choose_color);self.color_button.grid(row=0,column=0,padx=(0,5))
  ttk.Button(tools,text="Eraser",command=lambda:setattr(self,"color",None)).grid(row=0,column=1,padx=(0,5));ttk.Button(tools,text="Clear",command=self.clear).grid(row=0,column=2,padx=(0,10))
  for column,(value,label) in enumerate((("pencil","Pencil"),("line","Line"),("rectangle","Rectangle"),("ellipse","Ellipse")),3):ttk.Radiobutton(tools,text=label,value=value,variable=self.tool).grid(row=0,column=column,padx=2)
  ttk.Checkbutton(tools,text="Filled",variable=self.filled).grid(row=0,column=7,padx=(8,0))
  self.copy_sources={label:list(source_pixels) for label,source_pixels in (copy_sources or [])};self.copy_choice=tk.StringVar()
  if self.copy_sources:
   copy_box=ttk.Combobox(tools,textvariable=self.copy_choice,values=list(self.copy_sources),state="readonly",width=28);copy_box.grid(row=1,column=0,columnspan=4,sticky="ew",pady=(6,0));copy_box.current(0)
   ttk.Button(tools,text="Copy frame into current",command=self.copy_frame).grid(row=1,column=4,columnspan=4,sticky="ew",padx=(6,0),pady=(6,0))
  ttk.Label(tools,text="Left-drag draws • Right-drag erases").grid(row=2,column=0,columnspan=8,sticky="w",pady=(5,0))
  self.canvas=tk.Canvas(self,width=cw,height=ch,background="#707070",highlightthickness=1,highlightbackground="#333");self.canvas.pack(padx=8)
  for y in range(height):
   for x in range(width):
    item=self.canvas.create_rectangle(x*self.scale,y*self.scale,(x+1)*self.scale,(y+1)*self.scale,outline="#555",width=1)
    self.cells.append(item);self.paint_cell(x,y,False)
  self.canvas.bind("<ButtonPress-1>",self.draw_start);self.canvas.bind("<B1-Motion>",self.draw_drag);self.canvas.bind("<ButtonRelease-1>",self.draw_end);self.canvas.bind("<Button-3>",self.erase);self.canvas.bind("<B3-Motion>",self.erase)
  buttons=ttk.Frame(self,padding=8);buttons.pack(fill="x");ttk.Button(buttons,text="Cancel",command=self.destroy).pack(side="right");ttk.Button(buttons,text="Save frame",command=self.save).pack(side="right",padx=6)
  self.protocol("WM_DELETE_WINDOW",self.destroy);self.wait_visibility();self.grab_set();self.focus_set()
 def choose_color(self):
  value=colorchooser.askcolor(self.color or "#f4d35e",parent=self)[1]
  if value:self.color=value;self.color_button.configure(background=value)
 def paint_cell(self,x,y,set_pixel=True,erase=False):
  if not (0<=x<self.width and 0<=y<self.height):return
  i=y*self.width+x
  if set_pixel:
   if erase or self.color is None:self.pixels[i]=(0,0,0,0)
   else:
    c=self.color.lstrip("#");self.pixels[i]=tuple(int(c[n:n+2],16) for n in (0,2,4))+(255,)
  r,g,b,a=self.pixels[i];fill=f"#{r:02x}{g:02x}{b:02x}" if a else ("#b8b8b8" if (x+y)%2 else "#e0e0e0")
  self.canvas.itemconfigure(self.cells[i],fill=fill)
 def event_cell(self,event,erase=False):self.paint_cell(event.x//self.scale,event.y//self.scale,True,erase)
 def event_xy(self,event):return max(0,min(self.width-1,event.x//self.scale)),max(0,min(self.height-1,event.y//self.scale))
 def draw_start(self,event):
  if self.tool.get()=="pencil":self.event_cell(event);return
  self.shape_start=self.event_xy(event);self.shape_base=list(self.pixels);self.draw_shape(self.shape_start)
 def draw_drag(self,event):
  if self.tool.get()=="pencil":self.event_cell(event)
  elif self.shape_start:self.draw_shape(self.event_xy(event))
 def draw_end(self,event):
  if self.tool.get()!="pencil" and self.shape_start:self.draw_shape(self.event_xy(event))
  self.shape_start=None;self.shape_base=None
 def line_points(self,x0,y0,x1,y1):
  points=[];dx=abs(x1-x0);sx=1 if x0<x1 else -1;dy=-abs(y1-y0);sy=1 if y0<y1 else -1;error=dx+dy
  while True:
   points.append((x0,y0))
   if x0==x1 and y0==y1:return points
   twice=2*error
   if twice>=dy:error+=dy;x0+=sx
   if twice<=dx:error+=dx;y0+=sy
 def shape_points(self,x0,y0,x1,y1):
  tool=self.tool.get()
  if tool=="line":return self.line_points(x0,y0,x1,y1)
  left,right=sorted((x0,x1));top,bottom=sorted((y0,y1));filled=self.filled.get()
  if tool=="rectangle":
   if filled:return [(x,y) for y in range(top,bottom+1) for x in range(left,right+1)]
   return list(dict.fromkeys([(x,top) for x in range(left,right+1)]+[(x,bottom) for x in range(left,right+1)]+[(left,y) for y in range(top,bottom+1)]+[(right,y) for y in range(top,bottom+1)]))
  cx,cy=(left+right)/2,(top+bottom)/2;rx,ry=max(.5,(right-left)/2),max(.5,(bottom-top)/2);points=[]
  for y in range(top,bottom+1):
   for x in range(left,right+1):
    inside=((x-cx)/rx)**2+((y-cy)/ry)**2<=1.08
    if not inside:continue
    edge=any(((x+dx-cx)/rx)**2+((y+dy-cy)/ry)**2>1.08 for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)))
    if filled or edge:points.append((x,y))
  return points
 def draw_shape(self,end):
  previous=self.pixels;updated=list(self.shape_base);x0,y0=self.shape_start;x1,y1=end
  for x,y in self.shape_points(x0,y0,x1,y1):
   i=y*self.width+x
   if self.color is None:updated[i]=(0,0,0,0)
   else:
    c=self.color.lstrip("#");updated[i]=tuple(int(c[n:n+2],16) for n in (0,2,4))+(255,)
  self.pixels=updated
  for i,(old,new) in enumerate(zip(previous,updated)):
   if old!=new:self.paint_cell(i%self.width,i//self.width,False)
 def erase(self,event):self.event_cell(event,True)
 def redraw_cells(self):
  for y in range(self.height):
   for x in range(self.width):self.paint_cell(x,y,False)
 def clear(self):
  self.pixels=[(0,0,0,0)]*(self.width*self.height)
  self.redraw_cells()
 def copy_frame(self):
  source=self.copy_sources.get(self.copy_choice.get())
  if source is not None:self.pixels=list(source);self.shape_start=None;self.shape_base=None;self.redraw_cells()
 def save(self):self.result=base64.b64encode(png_rgba(self.width,self.height,self.pixels)).decode("ascii");self.destroy()

class TestRunner(tk.Toplevel):
 KEY_GROUPS={"LEFT":{"left","a"},"RIGHT":{"right","d"},"UP":{"up","w"},"DOWN":{"down","s"}}
 BUTTON_KEYS={"A":"z","B":"x","X":"c","Y":"v"}
 def __init__(self,parent,project,movement):
  super().__init__(parent);self.title(f"{APP_NAME} Test Run");self.geometry("960x600");self.minsize(640,400);self.project=json.loads(json.dumps(project));self.bp=movement
  self.bp_vars=dict(self.bp.get("variables",{}));self.game=GameRuntime(self.project,self.bp_vars);self.first_tick=True
  self.pressed=set();self.x=float(self.project["player_x"]);self.y=float(self.project["player_y"]);self.facing="down";self.frame=0;self.anim_tick=0;self.last_anim=None;self.photos={};self.closed=False
  info=ttk.Frame(self,padding=6);info.pack(fill="x");ttk.Label(info,text="Move: Arrow keys or WASD   •   Wii U A=Z, B=X, X=C, Y=V   •   Shift also tests connected Run Modifier nodes   •   Esc: Stop",anchor="center").pack(fill="x")
  self.canvas=tk.Canvas(self,background=self.project["background"],highlightthickness=0);self.canvas.pack(fill="both",expand=True)
  self.bind("<KeyPress>",self.key_down);self.bind("<KeyRelease>",self.key_up);self.bind("<Escape>",lambda _e:self.close());self.bind("<FocusOut>",lambda _e:self.pressed.clear());self.protocol("WM_DELETE_WINDOW",self.close);self.focus_force();self.after(16,self.tick)
 def close(self):self.closed=True;self.destroy()
 def key_down(self,event):
  key=event.keysym.lower();fresh=key not in self.pressed;self.pressed.add(key)
  if fresh:
   button=next((b for b,k in self.BUTTON_KEYS.items() if k==key),None)
   if button is None:button=next((b for b,keys in self.KEY_GROUPS.items() if key in keys),None)
   if button:self.apply_input_actions(button)
 def key_up(self,event):self.pressed.discard(event.keysym.lower())
 def button_held(self,name):
  if name in self.KEY_GROUPS:return bool(self.KEY_GROUPS[name]&self.pressed)
  return self.BUTTON_KEYS.get(name,"") in self.pressed
 def compare(self,left,op,right):
  return {"==":left==right,"!=":left!=right,"<":left<right,"<=":left<=right,">":left>right,">=":left>=right}.get(op,True)
 def gates_ok(self,action):
  return all(self.compare(self.bp_vars.get(g["variable"],0),g.get("op","=="),int(g.get("value",0))) for g in action.get("gates",[]))
 def action_speed(self,action,lo,hi):
  value=self.bp_vars.get(action.get("speed_variable",""),action.get("speed",100))
  return max(lo,min(hi,int(value)))
 def apply_variable_action(self,action):
  if not self.gates_ok(action):return
  name=action.get("variable","");value=int(action.get("value",0))
  if name not in self.bp_vars:return
  if action["type"]=="Set Variable":self.bp_vars[name]=value
  else:self.bp_vars[name]=self.bp_vars.get(name,0)+value
 def apply_input_actions(self,button):
  for action in self.bp.get("actions",[]):
   if action.get("source")=="input" and action.get("button")==button and action.get("type") in ("Set Variable","Change Variable"):self.apply_variable_action(action)
 def apply_frame_variable_actions(self,first):
  for action in self.bp.get("actions",[]):
   if action.get("type") not in ("Set Variable","Change Variable"):continue
   source=action.get("source")
   if source=="update" or (source=="start" and first):self.apply_variable_action(action)
 def action_active(self,action,first):
  source=action.get("source")
  if source=="start":return first
  if source=="update":return True
  return self.button_held(action.get("button",""))
 def collect_movement(self,first):
  vx100=vy100=0;run_percent=100;shift=bool({"shift_l","shift_r"}&self.pressed)
  for action in self.bp.get("actions",[]):
   t=action.get("type")
   if t not in ("Move Character","Run Modifier") or not self.gates_ok(action):continue
   active=self.action_active(action,first)
   if t=="Run Modifier" and action.get("source")=="input" and shift:active=True
   if not active:continue
   if t=="Move Character":
    speed=self.action_speed(action,1,400);vx100+=int(action.get("dx",0))*speed;vy100+=int(action.get("dy",0))*speed
   else:run_percent=self.action_speed(action,101,400)
  return vx100,vy100,run_percent
 def current_animation(self,moving):
  key=("walk_" if moving else "idle_")+self.facing;assigned=self.project.get("directional_animations",{}).get(key,"") or self.project.get("active_animation","")
  animation=self.project.get("animations",{}).get(assigned,{})
  if not animation.get("frames"):
   partner=("idle_" if moving else "walk_")+self.facing;assigned=self.project.get("directional_animations",{}).get(partner,"") or self.project.get("active_animation","");animation=self.project.get("animations",{}).get(assigned,{})
  return assigned,animation
 def photo(self,frame):
  key=frame["png_base64"]
  if key not in self.photos:self.photos[key]=tk.PhotoImage(data=key)
  return self.photos[key]
 def tick(self):
  if self.closed or not self.winfo_exists():return
  first=self.first_tick;self.apply_frame_variable_actions(first);vx100,vy100,run_percent=self.collect_movement(first);self.first_tick=False
  dx=self.project["player_speed"]*vx100/100.0;dy=self.project["player_speed"]*vy100/100.0
  if run_percent!=100:dx*=run_percent/100.0;dy*=run_percent/100.0
  if dx and dy:dx*=181/256;dy*=181/256
  nx=max(0,min(1280-self.project["player_width"],self.x+dx));ny=max(0,min(720-self.project["player_height"],self.y+dy))
  if not self.blocked(nx,self.y):self.x=nx
  if not self.blocked(self.x,ny):self.y=ny
  if dy>0:self.facing="down"
  elif dx<0:self.facing="left"
  elif dx>0:self.facing="right"
  elif dy<0:self.facing="up"
  self.game.step(self,first)
  name,animation=self.current_animation(bool(dx or dy));frames=animation.get("frames",[])
  if name!=self.last_anim:self.frame=0;self.anim_tick=0;self.last_anim=name
  if frames:
   self.anim_tick+=1;delay=max(1,60//max(1,animation.get("fps",8)))
   if self.anim_tick>=delay:
    self.anim_tick=0
    if self.frame+1<len(frames):self.frame+=1
    elif animation.get("loop",True):self.frame=0
  self.redraw(frames);self.after(16,self.tick)
 def blocked(self,x,y):
  tw=32;tiles=self.project.get("tiles",[]);room=self.game.room_map()
  points=((x,y),(x+self.project["player_width"]-1,y),(x,y+self.project["player_height"]-1),(x+self.project["player_width"]-1,y+self.project["player_height"]-1))
  for px,py in points:
   cx,cy=int(px)//tw,int(py)//tw
   if 0<=cx<40 and 0<=cy<23:
    i=room[cy*40+cx] if cy*40+cx<len(room) else -1
    if 0<=i<len(tiles) and tiles[i].get("solid",False):return True
  return False
 def redraw(self,frames):
  self.canvas.delete("all");w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height());scale=min(w/1280,h/720);ox=(w-1280*scale)/2;oy=(h-720*scale)/2
  self.canvas.create_rectangle(ox,oy,ox+1280*scale,oy+720*scale,fill=self.project["background"],outline="#888")
  tiles=self.project.get("tiles",[]);room=self.game.room_map()
  for gy in range(23):
   for gx in range(40):
    pos=gy*40+gx;i=room[pos] if pos<len(room) else -1
    if 0<=i<len(tiles):
     tile=tiles[i];key="tile:"+tile["png_base64"]
     if key not in self.photos:self.photos[key]=tk.PhotoImage(data=tile["png_base64"])
     pic=self.photos[key];factor=max(1,int(32*scale)//32);shown=pic.zoom(factor,factor) if factor>1 else pic
     if factor>1:self.photos[key+":shown"]=shown
     self.canvas.create_image(ox+gx*32*scale,oy+gy*32*scale,image=shown,anchor="nw")
  self.game.draw(self.canvas,scale,ox,oy)
  x=ox+self.x*scale;y=oy+self.y*scale;pw=self.project["player_width"]*scale;ph=self.project["player_height"]*scale
  if frames:
   pic=self.photo(frames[self.frame%len(frames)]);ratio=min(pw/max(1,pic.width()),ph/max(1,pic.height()))
   if ratio>=1:factor=max(1,int(ratio));shown=pic.zoom(factor,factor)
   else:factor=max(1,int(max(pic.width()/max(1,pw),pic.height()/max(1,ph))+.999));shown=pic.subsample(factor,factor)
   self.photos["shown"]=shown;self.canvas.create_image(x,y,image=shown,anchor="nw")
  else:self.canvas.create_rectangle(x,y,x+pw,y+ph,fill=self.project["player_color"],outline="white")
  self.canvas.create_text(ox+8,oy+8,text=self.project["title"] or "Untitled",fill="white",anchor="nw")

class Editor(tk.Tk):
 def __init__(self):
  super().__init__(); self.title(f"{APP_NAME} {VERSION}"); self.geometry("1120x750"); self.minsize(900,650)
  self.project=fresh(); self.project_path=None; self.photos={}; self.job=None; self.drag=None
  self.build_ui(); self.load_project()

 def build_ui(self):
  bar=ttk.Frame(self,padding=8); bar.pack(fill="x")
  for label,fn in (("New",self.new),("Open",self.open),("Save",self.save),("Save As",self.save_as),("Test Run",self.test_run),("Export Wii U Project",self.export)):
   ttk.Button(bar,text=label,command=fn).pack(side="left",padx=3)
  ttk.Label(bar,text="2D / 2.5D",foreground="#356fa6").pack(side="right",padx=8)
  tabs=ttk.Notebook(self); tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
  self.status=tk.StringVar(value="Ready"); ttk.Label(self,textvariable=self.status,relief="sunken",anchor="w",padding=4).pack(fill="x")
  scene=ttk.Frame(tabs,padding=8); room=ttk.Frame(tabs,padding=8); anim=ttk.Frame(tabs,padding=8); framework=ttk.Frame(tabs); logic=ttk.Frame(tabs)
  tabs.add(scene,text="Scene");tabs.add(room,text="Room / Tiles");tabs.add(anim,text="Animated Character");tabs.add(framework,text="Game Framework");tabs.add(logic,text="Blueprint Logic")
  self.build_scene(scene);self.build_room(room);self.build_anim(anim);self.framework=FrameworkPanel(framework,lambda:self.project,self.status,self.redraw);self.framework.pack(fill="both",expand=True);self.blueprint=BlueprintPanel(logic,lambda:self.project,self.status);self.blueprint.pack(fill="both",expand=True)

 def build_scene(self,parent):
  body=ttk.Panedwindow(parent,orient="horizontal"); body.pack(fill="both",expand=True)
  panel=ttk.LabelFrame(body,text="Project and character",padding=12); view=ttk.LabelFrame(body,text="1280 x 720 Scene Preview",padding=8)
  body.add(panel,weight=0); body.add(view,weight=1); self.vars={}
  fields=(("title","Game title"),("author","Author"),("player_x","Character X"),("player_y","Character Y"),("player_width","Display width"),("player_height","Display height"),("player_speed","Movement speed"))
  for row,(key,label) in enumerate(fields):
   ttk.Label(panel,text=label).grid(row=row,column=0,sticky="w",pady=4); v=tk.StringVar(); self.vars[key]=v
   ttk.Entry(panel,textvariable=v,width=24).grid(row=row,column=1,padx=(8,0),pady=4); v.trace_add("write",lambda *_:self.fields_changed())
  row=len(fields); ttk.Label(panel,text="Active animation").grid(row=row,column=0,sticky="w")
  self.active=tk.StringVar(); self.active_box=ttk.Combobox(panel,textvariable=self.active,state="readonly",width=21)
  self.active_box.grid(row=row,column=1,padx=(8,0)); self.active_box.bind("<<ComboboxSelected>>",self.active_changed)
  ttk.Button(panel,text="Background color",command=lambda:self.pick("background")).grid(row=row+1,column=0,columnspan=2,sticky="ew",pady=(14,4))
  ttk.Button(panel,text="Fallback character color",command=lambda:self.pick("player_color")).grid(row=row+2,column=0,columnspan=2,sticky="ew")
  ttk.Label(panel,text="Drag the character to position it.\nA rectangle is used until frames exist.\nDirectional states are assigned on the\nAnimated Character tab.").grid(row=row+3,column=0,columnspan=2,sticky="w",pady=16)
  self.canvas=tk.Canvas(view,width=640,height=360,highlightthickness=1,highlightbackground="#777"); self.canvas.pack(fill="both",expand=True)
  self.canvas.bind("<Configure>",lambda _e:self.redraw()); self.canvas.bind("<Button-1>",self.drag_start); self.canvas.bind("<B1-Motion>",self.drag_move); self.canvas.bind("<ButtonRelease-1>",lambda _e:setattr(self,"drag",None))

 def build_room(self,parent):
  parent.columnconfigure(1,weight=1);parent.rowconfigure(0,weight=1)
  left=ttk.LabelFrame(parent,text="32×32 Tiles",padding=8);left.grid(row=0,column=0,sticky="ns",padx=(0,8))
  view=ttk.LabelFrame(parent,text="Room 1280×720",padding=8);view.grid(row=0,column=1,sticky="nsew")
  view.columnconfigure(0,weight=1);view.rowconfigure(0,weight=1)
  self.tile_list=tk.Listbox(left,width=24,height=18,exportselection=False);self.tile_list.pack(fill="both",expand=True)
  self.tile_list.bind("<<ListboxSelect>>",lambda _e:self.tile_selected())
  ttk.Button(left,text="Import 32×32 PNG(s)",command=self.import_tiles).pack(fill="x",pady=(8,3))
  ttk.Button(left,text="Delete tile",command=self.delete_tile).pack(fill="x")
  self.tile_solid=tk.BooleanVar(value=False);ttk.Checkbutton(left,text="Solid collision",variable=self.tile_solid,command=self.tile_solid_changed).pack(anchor="w",pady=(10,6))
  self.room_tool=tk.StringVar(value="paint")
  for value,label in (("paint","Paint"),("erase","Erase"),("fill","Fill")):ttk.Radiobutton(left,text=label,value=value,variable=self.room_tool).pack(anchor="w")
  ttk.Label(left,text="Left-click edits the room.\nSolid tiles block Test Run\nand exported Wii U movement.",justify="left").pack(anchor="w",pady=(12,0))
  self.room_canvas=tk.Canvas(view,background="#202020",highlightthickness=1,highlightbackground="#777");self.room_canvas.grid(row=0,column=0,sticky="nsew")
  self.room_canvas.bind("<Configure>",lambda _e:self.redraw_room())
  self.room_canvas.bind("<Button-1>",self.room_click);self.room_canvas.bind("<B1-Motion>",self.room_click)

 def refresh_tiles(self):
  if not hasattr(self,"tile_list"):return
  self.tile_list.delete(0,"end")
  for i,t in enumerate(self.project.get("tiles",[])):self.tile_list.insert("end",f"{i:02d}  {t.get('name','tile')}"+("  [solid]" if t.get("solid") else ""))
  if self.project.get("tiles") and not self.tile_list.curselection():self.tile_list.selection_set(0)
  self.tile_selected();self.redraw_room()

 def tile_selected(self):
  if not hasattr(self,"tile_list"):return
  s=self.tile_list.curselection();tiles=self.project.get("tiles",[])
  self.tile_solid.set(bool(s and s[0]<len(tiles) and tiles[s[0]].get("solid",False)))

 def import_tiles(self):
  paths=filedialog.askopenfilenames(filetypes=[("PNG images","*.png")])
  try:
   for path in paths:
    if len(self.project["tiles"])>=255:raise ValueError("A room supports a maximum of 255 tile definitions.")
    data=base64.b64encode(Path(path).read_bytes()).decode("ascii");pic=tk.PhotoImage(data=data)
    if (pic.width(),pic.height())!=(32,32):raise ValueError(f"{Path(path).name} must be exactly 32×32")
    self.project["tiles"].append({"name":Path(path).name,"png_base64":data,"solid":False})
   self.photos.clear();self.refresh_tiles()
  except Exception as e:messagebox.showerror(APP_NAME,f"Tile import failed:\n{e}")

 def delete_tile(self):
  s=self.tile_list.curselection()
  if not s:return
  idx=s[0];del self.project["tiles"][idx]
  self.project["room_map"]=[(-1 if v==idx else v-1 if v>idx else v) for v in self.project["room_map"]]
  self.photos.clear();self.refresh_tiles()

 def tile_solid_changed(self):
  s=self.tile_list.curselection()
  if s and s[0]<len(self.project["tiles"]):self.project["tiles"][s[0]]["solid"]=bool(self.tile_solid.get());self.refresh_tiles();self.tile_list.selection_set(s[0])

 def room_geometry(self):
  w=max(1,self.room_canvas.winfo_width());h=max(1,self.room_canvas.winfo_height());scale=min(w/1280,h/720);return scale,(w-1280*scale)/2,(h-720*scale)/2

 def room_click(self,e):
  scale,ox,oy=self.room_geometry()
  gx=int((e.x-ox)/(32*scale));gy=int((e.y-oy)/(32*scale))
  if not (0<=gx<40 and 0<=gy<23):return
  pos=gy*40+gx;tool=self.room_tool.get();s=self.tile_list.curselection();value=s[0] if s else -1
  if tool=="erase":self.project["room_map"][pos]=-1
  elif tool=="paint" and value>=0:self.project["room_map"][pos]=value
  elif tool=="fill":
   old=self.project["room_map"][pos]
   if old==value:return
   q=[(gx,gy)];seen=set()
   while q:
    x,y=q.pop()
    if (x,y) in seen or not (0<=x<40 and 0<=y<23):continue
    seen.add((x,y));p=y*40+x
    if self.project["room_map"][p]!=old:continue
    self.project["room_map"][p]=value;q.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
  self.redraw_room()

 def redraw_room(self):
  if not hasattr(self,"room_canvas"):return
  self.room_canvas.delete("all");scale,ox,oy=self.room_geometry()
  self.room_canvas.create_rectangle(ox,oy,ox+1280*scale,oy+720*scale,fill=self.project["background"],outline="#777")
  tiles=self.project.get("tiles",[]);room=self.project.get("room_map",[])
  for gy in range(23):
   for gx in range(40):
    p=gy*40+gx;i=room[p] if p<len(room) else -1
    if 0<=i<len(tiles):
     key="roomtile:"+tiles[i]["png_base64"]
     if key not in self.photos:self.photos[key]=tk.PhotoImage(data=tiles[i]["png_base64"])
     pic=self.photos[key];target=max(1,int(round(32*scale)))
     if target>=32:factor=max(1,target//32);shown=pic.zoom(factor,factor)
     else:factor=max(1,32//target);shown=pic.subsample(factor,factor)
     self.photos[f"{key}:{gx}:{gy}"]=shown
     self.room_canvas.create_image(ox+gx*32*scale,oy+gy*32*scale,image=shown,anchor="nw")
  for gx in range(41):self.room_canvas.create_line(ox+gx*32*scale,oy,ox+gx*32*scale,oy+720*scale,fill="#555")
  for gy in range(24):self.room_canvas.create_line(ox,oy+gy*32*scale,ox+1280*scale,oy+gy*32*scale,fill="#555")

 def build_anim(self,parent):
  parent.columnconfigure(1,weight=1); parent.rowconfigure(0,weight=1)
  left=ttk.LabelFrame(parent,text="Animations",padding=8); mid=ttk.LabelFrame(parent,text="Frames",padding=8); right=ttk.LabelFrame(parent,text="Preview",padding=8)
  left.grid(row=0,column=0,sticky="nsew",padx=(0,6)); mid.grid(row=0,column=1,sticky="nsew",padx=6); right.grid(row=0,column=2,sticky="nsew",padx=(6,0)); mid.columnconfigure(0,weight=1); mid.rowconfigure(0,weight=1)
  self.anim_list=tk.Listbox(left,width=23,height=20,exportselection=False); self.anim_list.pack(fill="both",expand=True); self.anim_list.bind("<<ListboxSelect>>",lambda _e:self.refresh_frames())
  ttk.Button(left,text="New animation",command=self.add_animation).pack(fill="x",pady=(8,2)); ttk.Button(left,text="Delete animation",command=self.delete_animation).pack(fill="x")
  self.frame_list=tk.Listbox(mid,height=20,exportselection=False); self.frame_list.grid(row=0,column=0,columnspan=3,sticky="nsew"); self.frame_list.bind("<<ListboxSelect>>",lambda _e:self.show_frame())
  make=ttk.Frame(mid);make.grid(row=1,column=0,columnspan=3,sticky="ew",pady=(8,2))
  for column in range(3):make.columnconfigure(column,weight=1)
  ttk.Button(make,text="New frame",command=self.new_frame).grid(row=0,column=0,sticky="ew");ttk.Button(make,text="Edit selected",command=self.edit_frame).grid(row=0,column=1,sticky="ew",padx=3);ttk.Button(make,text="Import PNG(s)",command=self.import_frames).grid(row=0,column=2,sticky="ew")
  ttk.Button(mid,text="Up",command=lambda:self.move_frame(-1)).grid(row=2,column=0,sticky="ew"); ttk.Button(mid,text="Down",command=lambda:self.move_frame(1)).grid(row=2,column=1,sticky="ew"); ttk.Button(mid,text="Delete",command=self.delete_frame).grid(row=2,column=2,sticky="ew")
  opts=ttk.Frame(right); opts.pack(fill="x"); ttk.Label(opts,text="FPS").pack(side="left")
  self.fps=tk.StringVar(value="8"); ttk.Spinbox(opts,from_=1,to=60,width=6,textvariable=self.fps,command=self.options_changed).pack(side="left",padx=5)
  self.loop=tk.BooleanVar(value=True); ttk.Checkbutton(opts,text="Loop",variable=self.loop,command=self.options_changed).pack(side="left")
  self.anim_canvas=tk.Canvas(right,width=280,height=280,background="#303030",highlightthickness=1,highlightbackground="#777"); self.anim_canvas.pack(pady=12)
  buttons=ttk.Frame(right); buttons.pack(); ttk.Button(buttons,text="Play",command=self.play).pack(side="left",padx=3); ttk.Button(buttons,text="Stop",command=self.stop).pack(side="left",padx=3)
  ttk.Label(right,text="PNG only • Maximum 128×128\nAll frames in one animation must match.",justify="center").pack(pady=(12,5))
  roles=ttk.LabelFrame(right,text="RPG directional states",padding=6);roles.pack(fill="x",padx=4,pady=4)
  self.direction_vars={}
  labels=(("idle_down","Idle down"),("walk_down","Walk down"),("idle_left","Idle left"),("walk_left","Walk left"),("idle_right","Idle right"),("walk_right","Walk right"),("idle_up","Idle up"),("walk_up","Walk up"))
  for row,(key,label) in enumerate(labels):
   ttk.Label(roles,text=label).grid(row=row,column=0,sticky="w",pady=1);var=tk.StringVar();self.direction_vars[key]=var
   box=ttk.Combobox(roles,textvariable=var,state="readonly",width=15);box.grid(row=row,column=1,sticky="ew",padx=(5,0),pady=1);box.bind("<<ComboboxSelected>>",lambda _e,k=key:self.direction_changed(k));setattr(self,"direction_box_"+key,box)

 def names(self): return list(self.project["animations"])
 def selected_anim(self):
  s=self.anim_list.curselection(); n=self.names(); return n[s[0]] if s and s[0]<len(n) else None
 def photo(self,frame):
  key=frame["png_base64"]
  if key not in self.photos:self.photos[key]=tk.PhotoImage(data=key)
  return self.photos[key]
 def load_project(self):
  for k,v in self.vars.items():v.set(str(self.project[k]))
  self.project.setdefault("directional_animations",{})
  self.project.setdefault("tiles",[]);self.project.setdefault("room_map",[-1]*(40*23));self.project.setdefault("variables",[]);ensure_framework(self.project)
  if len(self.project["room_map"])<40*23:self.project["room_map"]=(self.project["room_map"]+[-1]*(40*23))[:40*23]
  for key in ANIMATION_STATES:self.project["directional_animations"].setdefault(key,"")
  self.photos.clear();self.refresh_animations();self.refresh_tiles();self.framework.refresh();self.blueprint.refresh();self.redraw()
 def fields_changed(self):
  for k in ("title","author"):self.project[k]=self.vars[k].get()
  for k in ("player_x","player_y","player_width","player_height","player_speed"):
   try:self.project[k]=max(0,int(self.vars[k].get()))
   except ValueError:pass
  self.redraw()
 def refresh_animations(self,choose=None):
  n=self.names(); self.anim_list.delete(0,"end")
  for x in n:self.anim_list.insert("end",x)
  self.active_box["values"]=[""]+n; active=self.project.get("active_animation","")
  if active not in n:active=n[0] if n else ""; self.project["active_animation"]=active
  self.active.set(active)
  for key in ANIMATION_STATES:
   box=getattr(self,"direction_box_"+key);box["values"]=[""]+n
   assigned=self.project["directional_animations"].get(key,"")
   if assigned not in n:assigned="";self.project["directional_animations"][key]=""
   self.direction_vars[key].set(assigned)
  if n:
   target=choose if choose in n else active; i=n.index(target) if target in n else 0; self.anim_list.selection_set(i)
  self.refresh_frames(); self.redraw()
 def refresh_frames(self):
  self.stop(); self.frame_list.delete(0,"end"); name=self.selected_anim()
  if not name:self.fps.set("8");self.loop.set(True);self.show_frame();return
  a=self.project["animations"][name];self.fps.set(str(a.get("fps",8)));self.loop.set(a.get("loop",True))
  for i,f in enumerate(a["frames"]):self.frame_list.insert("end",f"{i+1:02d}  {f['name']}")
  if a["frames"]:self.frame_list.selection_set(0)
  self.show_frame()
 def add_animation(self):
  name=simpledialog.askstring(APP_NAME,"Animation name (idle, walk, jump, etc.):",parent=self)
  if not name:return
  name=name.strip()
  if not name or name in self.project["animations"]:messagebox.showerror(APP_NAME,"Enter a unique animation name.");return
  self.project["animations"][name]={"fps":8,"loop":True,"frames":[]}
  if not self.project["active_animation"]:self.project["active_animation"]=name
  self.refresh_animations(name)
 def delete_animation(self):
  name=self.selected_anim()
  if name and messagebox.askyesno(APP_NAME,f"Delete animation '{name}'?"):del self.project["animations"][name];self.refresh_animations()
 def import_frames(self):
  name=self.selected_anim()
  if not name:messagebox.showinfo(APP_NAME,"Create or select an animation first.");return
  paths=filedialog.askopenfilenames(filetypes=[("PNG images","*.png")]); a=self.project["animations"][name]
  try:
   for path in paths:
    data=base64.b64encode(Path(path).read_bytes()).decode("ascii"); pic=tk.PhotoImage(data=data); size=(pic.width(),pic.height())
    if max(size)>128:raise ValueError(f"{Path(path).name} exceeds 128×128")
    if a["frames"] and size!=(a["frames"][0]["width"],a["frames"][0]["height"]):raise ValueError(f"{Path(path).name} has a different frame size")
    a["frames"].append({"name":Path(path).name,"width":size[0],"height":size[1],"png_base64":data})
   self.photos.clear();self.refresh_frames();self.redraw()
  except Exception as e:messagebox.showerror(APP_NAME,f"Import failed:\n{e}")
 def new_frame(self):
  name=self.selected_anim()
  if not name:messagebox.showinfo(APP_NAME,"Create or select an animation first.");return
  frames=self.project["animations"][name]["frames"];selected=self.frame_list.curselection()
  if frames:
   source_index=selected[0] if selected else len(frames)-1;source=frames[source_index];width,height=source["width"],source["height"];pixels=self.frame_pixels(source);insert_at=source_index+1
  else:
   width=simpledialog.askinteger(APP_NAME,"Frame width (1–128 pixels):",parent=self,minvalue=1,maxvalue=128,initialvalue=32)
   if width is None:return
   height=simpledialog.askinteger(APP_NAME,"Frame height (1–128 pixels):",parent=self,minvalue=1,maxvalue=128,initialvalue=32)
   if height is None:return
   pixels=None;insert_at=0
  copy_sources=self.frame_copy_sources(frames)
  editor=PixelFrameEditor(self,width,height,pixels,title=f"Create frame for {name}",copy_sources=copy_sources);self.wait_window(editor)
  if editor.result:
   frames.insert(insert_at,{"name":f"drawn_frame_{len(frames)+1:02d}.png","width":width,"height":height,"png_base64":editor.result})
   self.photos.clear();self.refresh_frames();self.frame_list.selection_clear(0,"end");self.frame_list.selection_set(insert_at);self.show_frame();self.redraw()
 def frame_pixels(self,frame):
  pic=self.photo(frame);pixels=[]
  for y in range(pic.height()):
   for x in range(pic.width()):
    if pic.transparency_get(x,y):pixels.append((0,0,0,0));continue
    value=pic.get(x,y)
    if isinstance(value,str):value=value.lstrip("#");rgb=tuple(int(value[n:n+2],16) for n in (0,2,4))
    else:rgb=tuple(value[:3])
    pixels.append(rgb+(255,))
  return pixels
 def frame_copy_sources(self,frames,exclude=None):
  return [(f"Frame {i+1:02d} - {frame['name']}",self.frame_pixels(frame)) for i,frame in enumerate(frames) if i!=exclude]
 def edit_frame(self):
  name=self.selected_anim();selected=self.frame_list.curselection()
  if not name or not selected:messagebox.showinfo(APP_NAME,"Select a frame to edit first.");return
  index=selected[0];frame=self.project["animations"][name]["frames"][index];pixels=self.frame_pixels(frame)
  copy_sources=self.frame_copy_sources(self.project["animations"][name]["frames"],index)
  editor=PixelFrameEditor(self,frame["width"],frame["height"],pixels,f"Edit {frame['name']}",copy_sources);self.wait_window(editor)
  if editor.result:
   frame["png_base64"]=editor.result;self.photos.clear();self.refresh_frames();self.frame_list.selection_set(index);self.show_frame();self.redraw()
 def move_frame(self,d):
  name=self.selected_anim();s=self.frame_list.curselection()
  if not name or not s:return
  f=self.project["animations"][name]["frames"];old=s[0];new=old+d
  if 0<=new<len(f):f[old],f[new]=f[new],f[old];self.refresh_frames();self.frame_list.selection_clear(0,"end");self.frame_list.selection_set(new);self.show_frame()
 def delete_frame(self):
  name=self.selected_anim();s=self.frame_list.curselection()
  if name and s:del self.project["animations"][name]["frames"][s[0]];self.photos.clear();self.refresh_frames();self.redraw()
 def options_changed(self):
  name=self.selected_anim()
  if not name:return
  try:value=max(1,min(60,int(self.fps.get())))
  except ValueError:value=8
  self.project["animations"][name].update(fps=value,loop=self.loop.get())
 def show_frame(self,index=None):
  self.anim_canvas.delete("all");name=self.selected_anim()
  if not name or not self.project["animations"][name]["frames"]:return
  frames=self.project["animations"][name]["frames"];s=self.frame_list.curselection();index=index if index is not None else (s[0] if s else 0)
  pic=self.photo(frames[index]);scale=max(1,min(8,240//max(pic.width(),pic.height())));shown=pic.zoom(scale,scale);self.photos["anim_show"]=shown;self.anim_canvas.create_image(140,140,image=shown)
 def play(self):
  self.stop();name=self.selected_anim()
  if name and self.project["animations"][name]["frames"]:self.options_changed();self.preview_i=0;self.play_tick(name)
 def play_tick(self,name):
  if name!=self.selected_anim():return
  a=self.project["animations"][name];self.show_frame(self.preview_i);self.redraw(self.preview_i);self.preview_i+=1
  if self.preview_i>=len(a["frames"]):
   if not a["loop"]:self.job=None;return
   self.preview_i=0
  self.job=self.after(max(16,1000//a["fps"]),lambda:self.play_tick(name))
 def stop(self):
  if self.job is not None:self.after_cancel(self.job);self.job=None
 def active_changed(self,_e=None):self.project["active_animation"]=self.active.get();self.redraw()
 def direction_changed(self,key):
  self.project["directional_animations"][key]=self.direction_vars[key].get()

 def redraw(self,index=0):
  if not hasattr(self,"canvas"):return
  w,h=max(1,self.canvas.winfo_width()),max(1,self.canvas.winfo_height());sx,sy=w/1280,h/720;p=self.project;self.canvas.delete("all");self.canvas.configure(background=p["background"])
  frames=p["animations"].get(p.get("active_animation",""),{}).get("frames",[])
  if frames:
   pic=self.photo(frames[index%len(frames)]);scale=max(1,min(max(1,int(p["player_width"]*sx))//pic.width(),max(1,int(p["player_height"]*sy))//pic.height()));shown=pic.zoom(scale,scale);self.photos["scene_show"]=shown
   self.canvas.create_image(p["player_x"]*sx,p["player_y"]*sy,image=shown,anchor="nw",tags="player")
  else:self.canvas.create_rectangle(p["player_x"]*sx,p["player_y"]*sy,(p["player_x"]+p["player_width"])*sx,(p["player_y"]+p["player_height"])*sy,fill=p["player_color"],outline="white",tags="player")
  self.canvas.create_text(10,10,text=p["title"] or "Untitled",fill="white",anchor="nw")
 def drag_start(self,e):
  if "player" in self.canvas.gettags("current"):
   sx,sy=self.canvas.winfo_width()/1280,self.canvas.winfo_height()/720;self.drag=(e.x/sx-self.project["player_x"],e.y/sy-self.project["player_y"])
 def drag_move(self,e):
  if self.drag is None:return
  sx,sy=self.canvas.winfo_width()/1280,self.canvas.winfo_height()/720;x=int(e.x/sx-self.drag[0]);y=int(e.y/sy-self.drag[1])
  self.vars["player_x"].set(str(max(0,min(1280-self.project["player_width"],x))));self.vars["player_y"].set(str(max(0,min(720-self.project["player_height"],y))))
 def pick(self,key):
  value=colorchooser.askcolor(self.project[key],parent=self)[1]
  if value:self.project[key]=value;self.redraw()
 def new(self):self.stop();self.project=fresh();self.project_path=None;self.load_project();self.status.set("New project")
 def open(self):
  path=filedialog.askopenfilename(filetypes=[("Utopia project","*.ugs"),("Version 0.1 project","*.wugc"),("JSON","*.json")])
  if not path:return
  try:
   data=json.loads(Path(path).read_text(encoding="utf-8"))
   if data.get("format") not in ("utopia-project-8","utopia-project-7","utopia-project-6","utopia-project-5","utopia-project-4","utopia-project-3","utopia-project-2","wugc-project-1"):raise ValueError("Unsupported project format")
   data["format"]="utopia-project-8";self.project={**fresh(),**data};self.project.setdefault("animations",{});self.project.setdefault("directional_animations",{});self.project.setdefault("blueprint",default_graph());self.project.setdefault("tiles",[]);self.project.setdefault("room_map",[-1]*(40*23));self.project.setdefault("variables",[]);ensure_framework(self.project);self.project_path=Path(path);self.load_project();self.status.set(f"Opened {Path(path).name}")
  except Exception as e:messagebox.showerror(APP_NAME,f"Open failed:\n{e}")
 def save(self):
  if self.project_path is None:return self.save_as()
  self.project_path.write_text(json.dumps(self.project,indent=2)+"\n",encoding="utf-8");self.status.set(f"Saved {self.project_path.name}");return True
 def save_as(self):
  path=filedialog.asksaveasfilename(defaultextension=".ugs",filetypes=[("Utopia project","*.ugs")])
  if not path:return False
  self.project_path=Path(path);return self.save()
 def test_run(self):
  self.fields_changed();TestRunner(self,self.project,self.blueprint.movement_config());self.status.set("Test Run started")

 def write_frames(self,out):
  lines=["#pragma once","#include <stdint.h>","typedef struct { const uint32_t *const *frames; unsigned int count, width, height, delay, loop; } UtopiaAnimation;"]
  assigned=self.project.get("directional_animations",{});fallback=self.project.get("active_animation","")
  has_any=False;written={}
  for state in ANIMATION_STATES:
   name=assigned.get(state,"") or fallback;a=self.project["animations"].get(name,{});frames=a.get("frames",[]);has_any=has_any or bool(frames)
   if frames and name in written:
    lines.append(f"#define ANIM_{state.upper()} ANIM_{written[name].upper()}");continue
   for n,frame in enumerate(frames):
    pic=self.photo(frame);pixels=[]
    for y in range(pic.height()):
     for x in range(pic.width()):
      if pic.transparency_get(x,y):pixels.append("0x00000000u")
      else:
       c=pic.get(x,y)
       if isinstance(c,str):c=c.lstrip("#");r,g,b=[int(c[i:i+2],16) for i in (0,2,4)]
       else:r,g,b=c[:3]
       pixels.append(f"0x{r:02X}{g:02X}{b:02X}FFu")
    lines.append(f"static const uint32_t anim_{state}_frame_{n}[] = {{")
    for i in range(0,len(pixels),8):lines.append("    "+", ".join(pixels[i:i+8]) + ",")
    lines.append("};")
   if frames:
    written[name]=state
    lines.append(f"static const uint32_t *const anim_{state}_frames[] = {{"+", ".join(f"anim_{state}_frame_{i}" for i in range(len(frames)))+"};")
    lines.append(f"static const UtopiaAnimation ANIM_{state.upper()} = {{anim_{state}_frames, {len(frames)}, {frames[0]['width']}, {frames[0]['height']}, {max(1,60//max(1,a.get('fps',8)))}, {int(a.get('loop',True))}}};")
   else:lines.append(f"static const UtopiaAnimation ANIM_{state.upper()} = {{0, 0, 1, 1, 1, 1}};")
  lines.insert(2,f"#define HAS_ANIMATION {int(has_any)}")
  (out/"source"/"animation_frames.h").write_text("\n".join(lines)+"\n",encoding="utf-8")
 def write_room(self,out):
  lines=["#pragma once","#include <stdint.h>","#define ROOM_COLS 40","#define ROOM_ROWS 23","#define TILE_SIZE 32",f"#define TILE_COUNT {len(self.project.get('tiles',[]))}"]
  tiles=self.project.get("tiles",[])
  for n,tile in enumerate(tiles):
   pic=tk.PhotoImage(data=tile["png_base64"]);pixels=[]
   for y in range(32):
    for x in range(32):
     if pic.transparency_get(x,y):pixels.append("0x00000000u")
     else:
      v=pic.get(x,y)
      if isinstance(v,str):v=v.lstrip("#");r,g,b=[int(v[i:i+2],16) for i in (0,2,4)]
      else:r,g,b=v[:3]
      pixels.append(f"0x{r:02X}{g:02X}{b:02X}FFu")
   lines.append(f"static const uint32_t tile_{n}[1024] = {{")
   for i in range(0,1024,8):lines.append("    "+", ".join(pixels[i:i+8])+",")
   lines.append("};")
  if tiles:
   lines.append("static const uint32_t *const ROOM_TILES[] = {"+", ".join(f"tile_{i}" for i in range(len(tiles)))+"};")
   lines.append("static const uint8_t ROOM_SOLID[] = {"+", ".join("1" if t.get("solid") else "0" for t in tiles)+"};")
  else:
   lines.append("static const uint32_t *const ROOM_TILES[1] = {0};");lines.append("static const uint8_t ROOM_SOLID[1] = {0};")
  room=self.project.get("room_map",[-1]*(40*23))
  encoded=[255 if v<0 or v>=len(tiles) else v for v in room[:40*23]]
  lines.append("static const uint8_t ROOM_MAP[ROOM_COLS*ROOM_ROWS] = {")
  for i in range(0,len(encoded),40):lines.append("    "+", ".join(str(v) for v in encoded[i:i+40])+",")
  lines.append("};")
  (out/"source"/"room_data.h").write_text("\n".join(lines)+"\n",encoding="utf-8")

 def export(self):
  folder=filedialog.askdirectory(title="Choose export destination")
  if not folder:return
  out=Path(folder)/("utopia_wiiu_export_v"+VERSION.replace(".","_"))
  try:
   if out.exists():
    if not messagebox.askyesno(APP_NAME,f"Replace existing export folder?\n{out}"):return
    shutil.rmtree(out)
   shutil.copytree(TEMPLATE,out);p=self.project
   config=("#pragma once\n"+f"#define GAME_TITLE \"{p['title'].replace(chr(34),'')}\"\n#define START_X {p['player_x']}\n#define START_Y {p['player_y']}\n#define PLAYER_W {p['player_width']}\n#define PLAYER_H {p['player_height']}\n#define PLAYER_SPEED {p['player_speed']}\n#define BACKGROUND_COLOR {rgba(p['background'])}\n#define PLAYER_COLOR {rgba(p['player_color'])}\n")
   (out/"source"/"game_config.h").write_text(config,encoding="utf-8");self.write_frames(out);self.write_room(out);self.blueprint.write_header(out/"source"/"blueprint_logic.h")
   m=(out/"Makefile").read_text(encoding="utf-8").replace("APP_NAME := Utopia Game Studio Test",f"APP_NAME := {p['title']}").replace("APP_AUTHOR := Utopia",f"APP_AUTHOR := {p['author']}");(out/"Makefile").write_text(m,encoding="utf-8");(out/"project.ugs").write_text(json.dumps(p,indent=2)+"\n",encoding="utf-8")
   self.status.set(f"Exported v{VERSION} to {out}");messagebox.showinfo(APP_NAME,f"Exported Utopia Game Studio v{VERSION} project to:\n{out}\n\nBuild with: make")
  except Exception as e:messagebox.showerror(APP_NAME,f"Export failed:\n{e}")

if __name__=="__main__":
 show_splash()
 Editor().mainloop()
