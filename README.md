# Wii U Game Creator 0.1

This is a new, independent project. It does not use Next64 code, files, project formats, or versioning.

## What Version 0.1 does

- Runs as a small Windows editor using Python and Tkinter.
- Creates, opens, and saves `.wugc` JSON projects.
- Shows a 1280×720 preview with one colored player rectangle.
- Lets you drag the rectangle or enter its position and size.
- Exports a native Wii U WUT source project.
- Generated program draws on the TV and GamePad.
- Wii U GamePad D-pad moves the rectangle; Plus exits.

This version intentionally has no sprites, rooms, collision, audio, or visual logic.

## Run the editor on Windows

1. Install Python 3 from https://www.python.org/ and enable **Add Python to PATH**.
2. Double-click `run_editor.bat`.
3. Open `sample_project.wugc`, or make a new project.
4. Choose **Export Wii U Project** and select a destination folder.

## Install the Wii U build tools

Use the open-source devkitPro Wii U toolchain—not Nintendo's proprietary SDK.

1. Install devkitPro for Windows from https://devkitpro.org/wiki/Getting_Started
2. Open the **devkitPro MSYS2** terminal.
3. Install or update the Wii U packages:

   `pacman -Syu --needed wiiu-dev`

## Build the exported game

1. In the devkitPro MSYS2 terminal, change to the editor-created `wiiu_export` directory.
2. Run `make`.
3. A successful build creates `game.wuhb`.
4. Copy it to `wiiu/apps/wugc_test/game.wuhb` on the Aroma SD card.
5. Start it from the Wii U Menu. Use the GamePad D-pad; press Plus to exit.

## First hardware-test checklist

- Application appears on the Aroma Wii U Menu.
- It launches without returning immediately to the menu.
- TV and GamePad show the same background and rectangle.
- All four D-pad directions move correctly.
- The rectangle stays on screen.
- Plus exits cleanly.

Please report the exact failed checklist item and, for build failures, paste the complete terminal error.
