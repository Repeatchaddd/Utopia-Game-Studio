# Utopia Game Studio 0.3

Utopia Game Studio is an independent visual creator for native Wii U homebrew games, focused on **2D and 2.5D games**.

## Blueprint-style visual logic

Version 0.3 introduces Utopia's original node-based logic editor. It is inspired by the general idea of visual scripting, but does not use Unreal Engine code, assets, or branding.

- Draggable, color-coded nodes on a scrollable workspace.
- Execution links drawn between nodes.
- Add, edit, connect, move, and delete nodes.
- Start and Update event nodes.
- Configurable GamePad Input nodes.
- Configurable Move Character nodes.
- Default working D-pad movement graph.
- Blueprint graph saved inside the portable `.ugs` project.
- Connected D-pad-to-movement nodes are compiled into the native Wii U project.
- Version 0.1 and 0.2 projects open and upgrade automatically.

Version 0.2 animated-character tools remain included: named animations, multiple PNG frames, ordering, FPS, looping, preview playback, transparency, and native TV/GamePad animation.

## Using Blueprint Logic

1. Open the **Blueprint Logic** tab.
2. Select a node type and choose **Add Node**.
3. Select a source node and choose **Connect**.
4. Select the destination node.
5. Double-click a GamePad Input or Move Character node to edit it.

For this first version, the compiler recognizes these connected pairs:

- GamePad Input `LEFT` → Move Character `-1,0`
- GamePad Input `RIGHT` → Move Character `1,0`
- GamePad Input `UP` → Move Character `0,-1`
- GamePad Input `DOWN` → Move Character `0,1`

Removing one of those links disables that direction in the exported game. Start, Update, and non-directional GamePad buttons are groundwork for later logic actions.

## Run and build

1. Install Python 3 from https://www.python.org/ and enable **Add Python to PATH**.
2. Double-click `run_editor.bat`.
3. Save a `.ugs` project and choose **Export Wii U Project**.
4. Install devkitPro and `wiiu-dev` from https://devkitpro.org/wiki/Getting_Started.
5. In the devkitPro MSYS2 terminal, enter the exported `utopia_wiiu_export` directory and run `make`.
6. Copy `game.wuhb` to `wiiu/apps/utopia_test/game.wuhb` on the Aroma SD card.

## Version 0.3 test

First export the untouched default blueprint and confirm all four directions. Then remove only the LEFT link, export again, and confirm that Left is disabled while the other directions still work.

Utopia Game Studio is not affiliated with or endorsed by Nintendo, Epic Games, or YoYo Games.
