"""Reusable project dialogue data and editor for Utopia Game Studio."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

def default_dialogue():return {"conversations":[]}
def ensure_dialogue(project):
 d=project.setdefault("dialogue",default_dialogue());d.setdefault("conversations",[])
 for c in d["conversations"]:c.setdefault("pages",[])
 return d
def conversation_names(project):return [c["name"] for c in ensure_dialogue(project)["conversations"]]
def find_conversation(project,name):return next((c for c in ensure_dialogue(project)["conversations"] if c["name"]==name),None)

class DialoguePanel(ttk.Frame):
 def __init__(self,parent,project_getter,status):
  super().__init__(parent,padding=8);self.get_project=project_getter;self.status=status;self.build();self.refresh()
 def data(self):return ensure_dialogue(self.get_project())
 def build(self):
  self.columnconfigure(0,weight=1);self.columnconfigure(1,weight=2);self.rowconfigure(1,weight=1)
  ttk.Label(self,text="Conversations",font=("Segoe UI",11,"bold")).grid(row=0,column=0,sticky="w")
  ttk.Label(self,text="Dialogue Pages",font=("Segoe UI",11,"bold")).grid(row=0,column=1,sticky="w")
  self.conv=tk.Listbox(self,exportselection=False);self.conv.grid(row=1,column=0,sticky="nsew",padx=(0,8));self.conv.bind("<<ListboxSelect>>",lambda e:self.refresh_pages())
  self.pages=tk.Listbox(self,exportselection=False);self.pages.grid(row=1,column=1,sticky="nsew");self.pages.bind("<Double-Button-1>",lambda e:self.edit_page())
  a=ttk.Frame(self);a.grid(row=2,column=0,sticky="ew",pady=6);ttk.Button(a,text="Add",command=self.add_conv).pack(side="left");ttk.Button(a,text="Rename",command=self.rename).pack(side="left");ttk.Button(a,text="Delete",command=self.delete_conv).pack(side="left")
  b=ttk.Frame(self);b.grid(row=2,column=1,sticky="ew",pady=6);ttk.Button(b,text="Add Page",command=self.add_page).pack(side="left");ttk.Button(b,text="Edit Page",command=self.edit_page).pack(side="left");ttk.Button(b,text="Delete Page",command=self.delete_page).pack(side="left");ttk.Button(b,text="Move Up",command=lambda:self.move(-1)).pack(side="left");ttk.Button(b,text="Move Down",command=lambda:self.move(1)).pack(side="left")
 def selected_conv(self):
  s=self.conv.curselection();cs=self.data()["conversations"];return cs[s[0]] if s and s[0]<len(cs) else None
 def refresh(self):
  self.conv.delete(0,"end")
  for c in self.data()["conversations"]:self.conv.insert("end",c["name"])
  self.refresh_pages()
 def refresh_pages(self):
  self.pages.delete(0,"end");c=self.selected_conv()
  if c:
   for i,p in enumerate(c["pages"]):self.pages.insert("end",f"{i+1:02d}  {p.get('speaker','')}: {p.get('text','')[:80]}")
 def add_conv(self):
  n=simpledialog.askstring("Dialogue","Conversation name:",parent=self)
  if not n:return
  n=n.strip()
  if not n or n in conversation_names(self.get_project()):messagebox.showerror("Utopia Game Studio","Use a unique conversation name.",parent=self);return
  self.data()["conversations"].append({"name":n,"pages":[]});self.refresh();self.status.set("Conversation created")
 def rename(self):
  c=self.selected_conv()
  if not c:return
  old=c["name"];n=simpledialog.askstring("Dialogue","Conversation name:",initialvalue=old,parent=self)
  if not n:return
  n=n.strip()
  if n!=old and n in conversation_names(self.get_project()):return
  c["name"]=n
  for o in self.get_project().get("framework",{}).get("objects",[]):
   for e in o.get("events",[]):
    for a in e.get("actions",[]):
     if a.get("type")=="Show Dialogue" and a.get("conversation")==old:a["conversation"]=n
  self.refresh()
 def delete_conv(self):
  c=self.selected_conv()
  if c and messagebox.askyesno("Utopia Game Studio",f"Delete '{c['name']}'?",parent=self):self.data()["conversations"].remove(c);self.refresh()
 def page_dialog(self,page=None):
  d=tk.Toplevel(self);d.title("Dialogue Page");d.transient(self.winfo_toplevel());d.grab_set()
  ttk.Label(d,text="Speaker").grid(row=0,column=0,sticky="w",padx=8,pady=8);sv=tk.StringVar(value=(page or {}).get("speaker",""));ttk.Entry(d,textvariable=sv,width=32).grid(row=0,column=1,padx=8,pady=8)
  ttk.Label(d,text="Text").grid(row=1,column=0,sticky="nw",padx=8);txt=tk.Text(d,width=60,height=10,wrap="word");txt.grid(row=1,column=1,padx=8,pady=8);txt.insert("1.0",(page or {}).get("text",""))
  result={}
  def ok():result.update(speaker=sv.get().strip(),text=txt.get("1.0","end-1c").strip());d.destroy()
  ttk.Button(d,text="OK",command=ok).grid(row=2,column=1,sticky="e",padx=8,pady=8);d.wait_window();return result or None
 def add_page(self):
  c=self.selected_conv()
  if not c:return
  p=self.page_dialog()
  if p:c["pages"].append(p);self.refresh_pages()
 def edit_page(self):
  c=self.selected_conv();s=self.pages.curselection()
  if not c or not s:return
  p=self.page_dialog(c["pages"][s[0]])
  if p:c["pages"][s[0]]=p;self.refresh_pages()
 def delete_page(self):
  c=self.selected_conv();s=self.pages.curselection()
  if c and s:del c["pages"][s[0]];self.refresh_pages()
 def move(self,delta):
  c=self.selected_conv();s=self.pages.curselection()
  if not c or not s:return
  i=s[0];j=i+delta
  if 0<=j<len(c["pages"]):c["pages"][i],c["pages"][j]=c["pages"][j],c["pages"][i];self.refresh_pages();self.pages.selection_set(j)
