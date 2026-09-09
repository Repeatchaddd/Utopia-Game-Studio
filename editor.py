#!/usr/bin/env python3
"""Wii U Game Creator 0.1 - independent baseline editor."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

APP_NAME = "Wii U Game Creator"
VERSION = "0.1"
ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "runtime_template"

DEFAULT_PROJECT = {
    "format": "wugc-project-1",
    "title": "My Wii U Game",
    "author": "Homebrew Developer",
    "background": "#18365c",
    "player_color": "#f4d35e",
    "player_x": 560,
    "player_y": 320,
    "player_width": 80,
    "player_height": 80,
    "player_speed": 6,
}


def rgb32(value):
    value = value.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return f"0x{r:02X}{g:02X}{b:02X}FFu"


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {VERSION}")
        self.geometry("1020x690")
        self.minsize(860, 600)
        self.project = dict(DEFAULT_PROJECT)
        self.project_path = None
        self._drag_offset = None
        self._build_ui()
        self._load_fields()

    def _build_ui(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        for label, command in (("New", self.new), ("Open", self.open),
                               ("Save", self.save), ("Save As", self.save_as),
                               ("Export Wii U Project", self.export)):
            ttk.Button(bar, text=label, command=command).pack(side="left", padx=3)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        settings = ttk.LabelFrame(body, text="Project", padding=12)
        preview = ttk.LabelFrame(body, text="1280 x 720 Preview", padding=8)
        body.add(settings, weight=0)
        body.add(preview, weight=1)

        self.vars = {}
        fields = (("title", "Game title"), ("author", "Author"),
                  ("player_x", "Player X"), ("player_y", "Player Y"),
                  ("player_width", "Player width"), ("player_height", "Player height"),
                  ("player_speed", "Speed"))
        for row, (key, label) in enumerate(fields):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            self.vars[key] = var
            entry = ttk.Entry(settings, textvariable=var, width=24)
            entry.grid(row=row, column=1, pady=4, padx=(8, 0))
            var.trace_add("write", lambda *_: self._fields_changed())

        row = len(fields)
        ttk.Button(settings, text="Background color", command=lambda: self.pick("background"))\
            .grid(row=row, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        ttk.Button(settings, text="Player color", command=lambda: self.pick("player_color"))\
            .grid(row=row + 1, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Separator(settings).grid(row=row + 2, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(settings, text="Drag the rectangle to position it.\nD-pad movement is generated automatically.",
                  wraplength=250).grid(row=row + 3, column=0, columnspan=2, sticky="w")

        self.canvas = tk.Canvas(preview, width=640, height=360, highlightthickness=1,
                                highlightbackground="#777")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<Button-1>", self.drag_start)
        self.canvas.bind("<B1-Motion>", self.drag_move)
        self.canvas.bind("<ButtonRelease-1>", lambda _e: setattr(self, "_drag_offset", None))

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=4).pack(fill="x")

    def _load_fields(self):
        for key, var in self.vars.items():
            var.set(str(self.project[key]))
        self.redraw()

    def _fields_changed(self):
        for key in ("title", "author"):
            self.project[key] = self.vars[key].get()
        for key in ("player_x", "player_y", "player_width", "player_height", "player_speed"):
            try:
                self.project[key] = max(0, int(self.vars[key].get()))
            except ValueError:
                pass
        self.redraw()

    def redraw(self):
        if not hasattr(self, "canvas"):
            return
        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        sx, sy = w / 1280, h / 720
        p = self.project
        self.canvas.delete("all")
        self.canvas.configure(background=p["background"])
        self.canvas.create_rectangle(p["player_x"] * sx, p["player_y"] * sy,
                                     (p["player_x"] + p["player_width"]) * sx,
                                     (p["player_y"] + p["player_height"]) * sy,
                                     fill=p["player_color"], outline="white", tags="player")
        self.canvas.create_text(10, 10, text=p["title"] or "Untitled", fill="white", anchor="nw")

    def drag_start(self, event):
        if "player" not in self.canvas.gettags("current"):
            return
        p = self.project
        sx, sy = self.canvas.winfo_width() / 1280, self.canvas.winfo_height() / 720
        self._drag_offset = (event.x / sx - p["player_x"], event.y / sy - p["player_y"])

    def drag_move(self, event):
        if self._drag_offset is None:
            return
        sx, sy = self.canvas.winfo_width() / 1280, self.canvas.winfo_height() / 720
        x = int(event.x / sx - self._drag_offset[0])
        y = int(event.y / sy - self._drag_offset[1])
        self.vars["player_x"].set(str(max(0, min(1280 - self.project["player_width"], x))))
        self.vars["player_y"].set(str(max(0, min(720 - self.project["player_height"], y))))

    def pick(self, key):
        value = colorchooser.askcolor(self.project[key], parent=self)[1]
        if value:
            self.project[key] = value
            self.redraw()

    def new(self):
        self.project, self.project_path = dict(DEFAULT_PROJECT), None
        self._load_fields()
        self.status.set("New project")

    def open(self):
        path = filedialog.askopenfilename(filetypes=[("Wii U Game Creator project", "*.wugc"),
                                                     ("JSON", "*.json")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if data.get("format") != "wugc-project-1":
                raise ValueError("Not a Version 0.1 project")
            self.project = {**DEFAULT_PROJECT, **data}
            self.project_path = Path(path)
            self._load_fields()
            self.status.set(f"Opened {self.project_path.name}")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not open project:\n{exc}")

    def save(self):
        if self.project_path is None:
            return self.save_as()
        self.project_path.write_text(json.dumps(self.project, indent=2) + "\n", encoding="utf-8")
        self.status.set(f"Saved {self.project_path.name}")
        return True

    def save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".wugc",
                                            filetypes=[("Wii U Game Creator project", "*.wugc")])
        if not path:
            return False
        self.project_path = Path(path)
        return self.save()

    def export(self):
        folder = filedialog.askdirectory(title="Choose export destination")
        if not folder:
            return
        out = Path(folder) / "wiiu_export"
        try:
            if out.exists():
                if not messagebox.askyesno(APP_NAME, f"Replace existing export folder?\n{out}"):
                    return
                shutil.rmtree(out)
            shutil.copytree(TEMPLATE, out)
            p = self.project
            config = ("#pragma once\n"
                      f"#define GAME_TITLE \"{p['title'].replace(chr(34), '')}\"\n"
                      f"#define START_X {p['player_x']}\n#define START_Y {p['player_y']}\n"
                      f"#define PLAYER_W {p['player_width']}\n#define PLAYER_H {p['player_height']}\n"
                      f"#define PLAYER_SPEED {p['player_speed']}\n"
                      f"#define BACKGROUND_COLOR {rgb32(p['background'])}\n"
                      f"#define PLAYER_COLOR {rgb32(p['player_color'])}\n")
            (out / "source" / "game_config.h").write_text(config, encoding="utf-8")
            makefile = (out / "Makefile").read_text(encoding="utf-8")
            makefile = makefile.replace("APP_NAME := Wii U Game Creator Test", f"APP_NAME := {p['title']}")
            makefile = makefile.replace("APP_AUTHOR := WUGC", f"APP_AUTHOR := {p['author']}")
            (out / "Makefile").write_text(makefile, encoding="utf-8")
            (out / "project.wugc").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
            self.status.set(f"Exported to {out}")
            messagebox.showinfo(APP_NAME, f"Wii U project exported to:\n{out}\n\nBuild it from the devkitPro MSYS2 shell with: make")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Export failed:\n{exc}")


if __name__ == "__main__":
    Editor().mainloop()
