#!/usr/bin/env python3
"""Utopia Game Studio 0.3 - 2D/2.5D Wii U homebrew editor."""
import base64, json, shutil
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk
from blueprint_editor import BlueprintPanel, default_graph

APP_NAME, VERSION = "Utopia Game Studio", "0.3"
ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "runtime_template"
DEFAULT = {"format":"utopia-project-3","title":"My Utopia Game","author":"Homebrew Developer",
 "game_style":"2D / 2.5D","background":"#18365c","player_color":"#f4d35e",
 "player_x":560,"player_y":320,"player_width":80,"player_height":80,"player_speed":6,
 "animations":{},"active_animation":"","blueprint":default_graph()}

def fresh(): return json.loads(json.dumps(DEFAULT))
def rgba(value): return "0x" + value.lstrip("#").upper() + "FFu"

class Editor(tk.Tk):
 def __init__(self):
  super().__init__(); self.title(f"{APP_NAME} {VERSION}"); self.geometry("1120x750"); self.minsize(900,650)
  self.project=fresh(); self.project_path=None; self.photos={}; self.job=None; self.drag=None
  self.build_ui(); self.load_project()

 def build_ui(self):
  bar=ttk.Frame(self,padding=8); bar.pack(fill="x")
  for label,fn in (("New",self.new),("Open",self.open),("Save",self.save),("Save As",self.save_as),("Export Wii U Project",self.export)):
   ttk.Button(bar,text=label,command=fn).pack(side="left",padx=3)
  ttk.Label(bar,text="2D / 2.5D",foreground="#356fa6").pack(side="right",padx=8)
  tabs=ttk.Notebook(self); tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
  self.status=tk.StringVar(value="Ready"); ttk.Label(self,textvariable=self.status,relief="sunken",anchor="w",padding=4).pack(fill="x")
  scene=ttk.Frame(tabs,padding=8); anim=ttk.Frame(tabs,padding=8); logic=ttk.Frame(tabs)
  tabs.add(scene,text="Scene"); tabs.add(anim,text="Animated Character"); tabs.add(logic,text="Blueprint Logic")
  self.build_scene(scene); self.build_anim(anim); self.blueprint=BlueprintPanel(logic,lambda:self.project,self.status);self.blueprint.pack(fill="both",expand=True)

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
  ttk.Label(panel,text="Drag the character to position it.\nA rectangle is used until frames exist.").grid(row=row+3,column=0,columnspan=2,sticky="w",pady=16)
  self.canvas=tk.Canvas(view,width=640,height=360,highlightthickness=1,highlightbackground="#777"); self.canvas.pack(fill="both",expand=True)
  self.canvas.bind("<Configure>",lambda _e:self.redraw()); self.canvas.bind("<Button-1>",self.drag_start); self.canvas.bind("<B1-Motion>",self.drag_move); self.canvas.bind("<ButtonRelease-1>",lambda _e:setattr(self,"drag",None))

 def build_anim(self,parent):
  parent.columnconfigure(1,weight=1); parent.rowconfigure(0,weight=1)
  left=ttk.LabelFrame(parent,text="Animations",padding=8); mid=ttk.LabelFrame(parent,text="Frames",padding=8); right=ttk.LabelFrame(parent,text="Preview",padding=8)
  left.grid(row=0,column=0,sticky="nsew",padx=(0,6)); mid.grid(row=0,column=1,sticky="nsew",padx=6); right.grid(row=0,column=2,sticky="nsew",padx=(6,0)); mid.columnconfigure(0,weight=1); mid.rowconfigure(0,weight=1)
  self.anim_list=tk.Listbox(left,width=23,height=20,exportselection=False); self.anim_list.pack(fill="both",expand=True); self.anim_list.bind("<<ListboxSelect>>",lambda _e:self.refresh_frames())
  ttk.Button(left,text="New animation",command=self.add_animation).pack(fill="x",pady=(8,2)); ttk.Button(left,text="Delete animation",command=self.delete_animation).pack(fill="x")
  self.frame_list=tk.Listbox(mid,height=20,exportselection=False); self.frame_list.grid(row=0,column=0,columnspan=3,sticky="nsew"); self.frame_list.bind("<<ListboxSelect>>",lambda _e:self.show_frame())
  ttk.Button(mid,text="Import PNG frame(s)",command=self.import_frames).grid(row=1,column=0,columnspan=3,sticky="ew",pady=(8,2))
  ttk.Button(mid,text="Up",command=lambda:self.move_frame(-1)).grid(row=2,column=0,sticky="ew"); ttk.Button(mid,text="Down",command=lambda:self.move_frame(1)).grid(row=2,column=1,sticky="ew"); ttk.Button(mid,text="Delete",command=self.delete_frame).grid(row=2,column=2,sticky="ew")
  opts=ttk.Frame(right); opts.pack(fill="x"); ttk.Label(opts,text="FPS").pack(side="left")
  self.fps=tk.StringVar(value="8"); ttk.Spinbox(opts,from_=1,to=60,width=6,textvariable=self.fps,command=self.options_changed).pack(side="left",padx=5)
  self.loop=tk.BooleanVar(value=True); ttk.Checkbutton(opts,text="Loop",variable=self.loop,command=self.options_changed).pack(side="left")
  self.anim_canvas=tk.Canvas(right,width=280,height=280,background="#303030",highlightthickness=1,highlightbackground="#777"); self.anim_canvas.pack(pady=12)
  buttons=ttk.Frame(right); buttons.pack(); ttk.Button(buttons,text="Play",command=self.play).pack(side="left",padx=3); ttk.Button(buttons,text="Stop",command=self.stop).pack(side="left",padx=3)
  ttk.Label(right,text="PNG only • Maximum 128×128\nAll frames must match size.",justify="center").pack(pady=12)

 def names(self): return list(self.project["animations"])
 def selected_anim(self):
  s=self.anim_list.curselection(); n=self.names(); return n[s[0]] if s and s[0]<len(n) else None
 def photo(self,frame):
  key=frame["png_base64"]
  if key not in self.photos:self.photos[key]=tk.PhotoImage(data=key)
  return self.photos[key]
 def load_project(self):
  for k,v in self.vars.items():v.set(str(self.project[k]))
  self.photos.clear(); self.refresh_animations(); self.blueprint.refresh(); self.redraw()
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
   if data.get("format") not in ("utopia-project-3","utopia-project-2","wugc-project-1"):raise ValueError("Unsupported project format")
   data["format"]="utopia-project-3";self.project={**fresh(),**data};self.project.setdefault("animations",{});self.project.setdefault("blueprint",default_graph());self.project_path=Path(path);self.load_project();self.status.set(f"Opened {Path(path).name}")
  except Exception as e:messagebox.showerror(APP_NAME,f"Open failed:\n{e}")
 def save(self):
  if self.project_path is None:return self.save_as()
  self.project_path.write_text(json.dumps(self.project,indent=2)+"\n",encoding="utf-8");self.status.set(f"Saved {self.project_path.name}");return True
 def save_as(self):
  path=filedialog.asksaveasfilename(defaultextension=".ugs",filetypes=[("Utopia project","*.ugs")])
  if not path:return False
  self.project_path=Path(path);return self.save()

 def write_frames(self,out):
  a=self.project["animations"].get(self.project.get("active_animation",""),{});frames=a.get("frames",[]);lines=["#pragma once","#include <stdint.h>",f"#define HAS_ANIMATION {int(bool(frames))}"]
  if not frames:lines += ["#define FRAME_COUNT 0","#define FRAME_WIDTH 1","#define FRAME_HEIGHT 1","#define FRAME_DELAY 1","#define ANIMATION_LOOP 1"]
  else:
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
    lines.append(f"static const uint32_t frame_{n}[] = {{")
    for i in range(0,len(pixels),8):lines.append("    "+", ".join(pixels[i:i+8]) + ",")
    lines.append("};")
   lines += [f"#define FRAME_COUNT {len(frames)}",f"#define FRAME_WIDTH {frames[0]['width']}",f"#define FRAME_HEIGHT {frames[0]['height']}",f"#define FRAME_DELAY {max(1,60//max(1,a.get('fps',8)))}",f"#define ANIMATION_LOOP {int(a.get('loop',True))}","static const uint32_t *const animation_frames[FRAME_COUNT] = {"+", ".join(f"frame_{i}" for i in range(len(frames)))+"};"]
  (out/"source"/"animation_frames.h").write_text("\n".join(lines)+"\n",encoding="utf-8")
 def export(self):
  folder=filedialog.askdirectory(title="Choose export destination")
  if not folder:return
  out=Path(folder)/"utopia_wiiu_export"
  try:
   if out.exists():
    if not messagebox.askyesno(APP_NAME,f"Replace existing export folder?\n{out}"):return
    shutil.rmtree(out)
   shutil.copytree(TEMPLATE,out);p=self.project
   config=("#pragma once\n"+f"#define GAME_TITLE \"{p['title'].replace(chr(34),'')}\"\n#define START_X {p['player_x']}\n#define START_Y {p['player_y']}\n#define PLAYER_W {p['player_width']}\n#define PLAYER_H {p['player_height']}\n#define PLAYER_SPEED {p['player_speed']}\n#define BACKGROUND_COLOR {rgba(p['background'])}\n#define PLAYER_COLOR {rgba(p['player_color'])}\n")
   (out/"source"/"game_config.h").write_text(config,encoding="utf-8");self.write_frames(out);self.blueprint.write_header(out/"source"/"blueprint_logic.h")
   m=(out/"Makefile").read_text(encoding="utf-8").replace("APP_NAME := Utopia Game Studio Test",f"APP_NAME := {p['title']}").replace("APP_AUTHOR := Utopia",f"APP_AUTHOR := {p['author']}");(out/"Makefile").write_text(m,encoding="utf-8");(out/"project.ugs").write_text(json.dumps(p,indent=2)+"\n",encoding="utf-8")
   self.status.set(f"Exported to {out}");messagebox.showinfo(APP_NAME,f"Exported to:\n{out}\n\nBuild with: make")
  except Exception as e:messagebox.showerror(APP_NAME,f"Export failed:\n{e}")

if __name__=="__main__":Editor().mainloop()
