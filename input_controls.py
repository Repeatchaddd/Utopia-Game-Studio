"""Project-defined input/control mappings for Utopia Game Studio."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

GAMEPAD_INPUTS=("DPAD_LEFT","DPAD_RIGHT","DPAD_UP","DPAD_DOWN","A","B","X","Y","L","R","ZL","ZR","PLUS","MINUS","L_STICK","R_STICK")

def default_controls():
 return {"actions":[]}

def ensure_controls(project):
 controls=project.setdefault("controls",default_controls())
 controls.setdefault("actions",[])
 for a in controls["actions"]:
  a.setdefault("name","Action");a.setdefault("keyboard",[]);a.setdefault("gamepad",[])
 return controls

def action_names(project):return [a["name"] for a in ensure_controls(project)["actions"]]

class ControlsPanel(ttk.Frame):
 def __init__(self,parent,project_getter,status):
  super().__init__(parent,padding=10);self.get_project=project_getter;self.status=status;self.build();self.refresh()
 def controls(self):return ensure_controls(self.get_project())
 def build(self):
  self.columnconfigure(0,weight=1);self.rowconfigure(1,weight=1)
  ttk.Label(self,text="Project Input Actions",font=("Segoe UI",12,"bold")).grid(row=0,column=0,sticky="w")
  ttk.Label(self,text="Utopia assigns no controls automatically. Create named actions, then bind keyboard and/or Wii U gamepad inputs.",justify="left").grid(row=0,column=1,sticky="e")
  self.list=tk.Listbox(self,height=20,exportselection=False);self.list.grid(row=1,column=0,columnspan=2,sticky="nsew",pady=8)
  bar=ttk.Frame(self);bar.grid(row=2,column=0,columnspan=2,sticky="ew")
  for label,fn in (("Add Action",self.add),("Rename",self.rename),("Keyboard Bindings",self.keyboard),("Gamepad Bindings",self.gamepad),("Delete",self.delete)):
   ttk.Button(bar,text=label,command=fn).pack(side="left",padx=3)
 def selected(self):
  s=self.list.curselection();a=self.controls()["actions"];return a[s[0]] if s and s[0]<len(a) else None
 def refresh(self):
  self.list.delete(0,"end")
  for a in self.controls()["actions"]:
   kb=", ".join(a["keyboard"]) or "—";gp=", ".join(a["gamepad"]) or "—"
   self.list.insert("end",f"{a['name']}    Keyboard: {kb}    Gamepad: {gp}")
 def add(self):
  name=simpledialog.askstring("Input Action","Action name:",parent=self)
  if not name:return
  name=name.strip()
  if not name or any(a["name"].lower()==name.lower() for a in self.controls()["actions"]):messagebox.showerror("Utopia Game Studio","Use a unique action name.",parent=self);return
  self.controls()["actions"].append({"name":name,"keyboard":[],"gamepad":[]});self.refresh();self.status.set("Input action created")
 def rename(self):
  a=self.selected()
  if not a:return
  old=a["name"];name=simpledialog.askstring("Input Action","Action name:",initialvalue=old,parent=self)
  if not name:return
  name=name.strip()
  if any(x is not a and x["name"].lower()==name.lower() for x in self.controls()["actions"]):messagebox.showerror("Utopia Game Studio","Use a unique action name.",parent=self);return
  a["name"]=name
  for n in self.get_project().get("blueprint",{}).get("nodes",[]):
   if n.get("type")=="Input Action" and n.get("props",{}).get("action")==old:n["props"]["action"]=name
  self.refresh()
 def keyboard(self):
  a=self.selected()
  if not a:return
  value=simpledialog.askstring("Keyboard Bindings","Key names separated by commas (examples: e, space, up, left, escape):",initialvalue=", ".join(a["keyboard"]),parent=self)
  if value is not None:a["keyboard"]=[x.strip().lower() for x in value.split(",") if x.strip()];self.refresh()
 def gamepad(self):
  a=self.selected()
  if not a:return
  value=simpledialog.askstring("Wii U Gamepad Bindings","Inputs separated by commas:\n"+", ".join(GAMEPAD_INPUTS),initialvalue=", ".join(a["gamepad"]),parent=self)
  if value is None:return
  vals=[x.strip().upper() for x in value.split(",") if x.strip()]
  bad=[x for x in vals if x not in GAMEPAD_INPUTS]
  if bad:messagebox.showerror("Utopia Game Studio","Unsupported input(s): "+", ".join(bad),parent=self);return
  a["gamepad"]=vals;self.refresh()
 def delete(self):
  a=self.selected()
  if not a:return
  if messagebox.askyesno("Utopia Game Studio",f"Delete input action '{a['name']}'?",parent=self):
   self.controls()["actions"].remove(a)
   for n in self.get_project().get("blueprint",{}).get("nodes",[]):
    if n.get("type")=="Input Action" and n.get("props",{}).get("action")==a["name"]:n["props"]["action"]=""
   self.refresh()
