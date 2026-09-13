# Utopia Game Studio v1.95.001.001

**Current development stage:** 1.95  
**Build:** 1.95.001.001

## v1.95.001.001 — Game Creator Skeleton

This release establishes Utopia as a simple general-purpose 2D/2.5D game creator rather than only a movement/animation editor.

New framework capabilities:
- reusable Game Objects: Player, NPC, Enemy, Item, and Generic
- multiple rooms with a selectable start room
- object instances placed into rooms
- Game Start, Room Start, Update, and Collision events
- event actions for variables, visibility, destroying objects, room changes, and simple movement
- global game-state variables shared with Test Run
- object-to-player and object-to-object collision event dispatch
- automatic migration of older Utopia project files into the new framework
- existing Blueprint movement and graph execution retained
- Test Run now executes both Blueprint logic and the generic game framework

The Game Framework tab is the first skeleton layer. More node types, visual instance placement, object animation assignment, richer conditions, and Wii U runtime parity will be expanded through later 1.95.xxx.xxx builds.

## v1.95.001.001 startup fix

- Corrected the packaged Python 3.14 startup issue where `tk.BooleanVar(False)` treated `False` as the Tk master argument.
- Packaged build now uses `tk.BooleanVar(value=False)`.
- No project-format or framework behavior change is intended by this patch.

---



Utopia Game Studio is an independent visual creator for native Wii U homebrew games. Its first complete framework is focused on **2D and 2.5D RPGs**, with other genres planned later.

## RPG player movement and directional animation

Version 0.4 adds the first RPG-ready player controller:

- D-pad movement on the TV and Wii U GamePad screens.
- Separate idle and walking animations for down, left, right, and up.
- The character keeps facing the last movement direction when stopped.
- Diagonal movement is normalized so it is not faster than straight movement.
- Missing idle/walk partners fall back to the available animation.
- Older projects open and upgrade automatically.

Create animations on the **Animated Character** tab, then assign them in the **RPG directional states** panel. PNG frames can be up to 128×128 pixels. Each animation may have its own frame size, speed, and looping setting.

## Built-in animation frame creator

Version 0.5 lets you create artwork directly inside the **Animated Character** tab—an outside graphics program is no longer required.

- **New frame** creates a transparent first frame from 1×1 through 128×128 pixels. After that, it duplicates the selected frame, inserts the copy directly after it, and opens the copy for editing. If no frame is selected, the final frame is duplicated.
- **Edit selected** opens any drawn or imported frame in the pixel editor.
- Left-drag draws with the selected color; right-drag or **Eraser** makes pixels transparent.
- **Clear** resets the entire frame to transparency.
- Saved artwork is embedded in the `.ugs` project and immediately works in preview, directional assignments, and Wii U export.

Version 0.6 adds basic shape tools to the frame creator:

- **Line** draws a straight pixel line between the drag points.
- **Rectangle** and **Ellipse** provide live previews while dragging.
- **Filled** switches rectangles and ellipses between outlines and solid shapes.
- Shape tools work with the selected drawing color or the transparent eraser.

Version 0.7 changes **New frame** to duplicate the preceding animation frame, making it quicker to draw small frame-to-frame movements without recreating the character.

Version 0.71 adds **Copy frame into current**. While creating or editing a frame, choose any other frame from the animation and copy its complete pixel artwork into the working frame. The source frame is not changed.

## Blueprint-style visual logic

Version 0.3 introduced Utopia's original node-based logic editor. It is inspired by the general idea of visual scripting, but does not use Unreal Engine code, assets, or branding.

Version 0.72 improves Blueprint movement speed control:

- **Move Character** properties now use a clear direction selector instead of raw X,Y entry.
- Each Move Character node has an adjustable walking-speed percentage from 1% through 400%.
- A new **Run Modifier** node sets running speed from 101% through 400% of walking speed.
- Connect a GamePad Input node to Run Modifier to choose the run button. New projects use **B** at 175% by default.
- Holding the connected run button changes actual exported Wii U movement speed; diagonal normalization still applies.
- Older Blueprint projects default existing movement nodes to 100% speed.

## Blueprint variables and conditional logic

Version 0.95 expands Blueprint logic into a reusable runtime variable system.

- Add named integer variables with starting values from the new **Variables** button in Blueprint Logic.
- **Set Variable** assigns a value when its connected GamePad input is triggered.
- **Change Variable** adds or subtracts from a variable.
- **Compare Variable** supports `==`, `!=`, `<`, `<=`, `>`, and `>=` and can gate connected actions.
- **Move Character** speed can use either a constant percentage or a variable value.
- **Run Modifier** speed can also use a variable value.
- Variable-driven movement is clamped to 1–400%; variable-driven running is clamped to 101–400%.
- GamePad Input → Compare Variable → Move/Run/Set/Change is compiled for both Test Run and the native Wii U runtime.
- Variable actions trigger once when a mapped button is pressed; movement and run nodes continue to respond while their inputs are held.
- Older projects load with an empty variable list and keep their existing constant movement values.

Example: create `WalkSpeed = 100`, select `WalkSpeed` as the speed source on a Move Character node, then connect another button to **Set Variable** or **Change Variable** to modify movement speed while the game is running.

Version 0.95.02 makes every currently available Blueprint node participate in actual graph execution:

- **GamePad Input** can drive any connected Move Character direction instead of being restricted to a matching D-pad direction.
- One input can fan out to multiple Move Character nodes, so a single button can produce diagonal or compound movement.
- **Move Character**, **Run Modifier**, **Set Variable**, and **Change Variable** execute from the graph path that reaches them.
- **Compare Variable** gates downstream actions and can be chained through Blueprint paths.
- **Start** now executes its downstream graph once when gameplay begins.
- **Update** now executes its downstream graph every frame.
- The same graph-driven behavior is used by **Test Run** and generated native Wii U runtime code.

Example: connect LEFT input to both Move Left and Move Down. Holding Left now moves the character down-left instead of silently ignoring the mismatched movement link.

Version 0.95.01 makes Blueprint link deletion safer:

- The dangerous **Clear Links** button has been removed completely.
- Click a single connection line to select it; the selected link is highlighted.
- Use **Delete Link** to remove only that selected connection.
- A confirmation dialog identifies the source and destination node before deletion.

Versioned export folders include the complete editor version, so this build exports to `utopia_wiiu_export_v0_95_02`. Version numbers may continue into additional sub-levels when useful.

## Native Wii U GX2 renderer

Version 0.8 replaces the original CPU pixel-plotting runtime with a native Wii U **GX2/WHBGfx GPU renderer**.

- TV and Wii U GamePad are rendered as separate GPU targets from the same 1280×720 logical scene.
- Character animation frames are uploaded as GX2 RGBA textures and drawn as textured quads instead of thousands of `OSScreenPutPixelEx` calls.
- Point filtering preserves crisp pixel-art edges.
- Transparent animation pixels are discarded by the pixel shader.
- Rendering is synchronized to the display swap interval.
- The renderer is isolated in `renderer.cpp/.h`, giving Utopia a proper rendering layer for later tile maps, backgrounds, objects, effects, camera work, and 2.5D features.
- The old OSScreen CPU renderer has been removed from the exported runtime.

The current development renderer uses **CafeGLSL** to compile Utopia's small built-in vertex and pixel shaders on the Wii U. Place `glslcompiler.rpl` in `wiiu/libs/` on the SD card. The renderer reports initialization failure rather than silently falling back to the old CPU renderer.

## Tile maps and room editor

Version 0.9 adds the first editable RPG environment:

- A **Room / Tiles** tab for a single 1280×720 room.
- 32×32 PNG tile import with up to 255 tile definitions.
- Paint, erase, and flood-fill tools on a 40×23 tile grid.
- Per-tile **Solid collision** metadata.
- Test Run now draws the room and prevents the player from entering solid tiles.
- Wii U export writes the tile textures, room map, and collision table into the native project.
- The GX2 renderer caches tile and sprite textures so repeated room tiles are uploaded once and reused.
- Export folders are versioned as `utopia_wiiu_export_v0_9`.

The final tile row extends slightly below the 720-pixel viewport and is clipped naturally; gameplay remains bounded to 1280×720. Multiple rooms, transitions, scrolling, and camera support are intentionally deferred until the fixed-room system is validated.

## Test Run

Version 0.75 adds **Test Run** to the main toolbar. It opens a resizable desktop preview that uses the current project and Blueprint movement setup without requiring a Wii U export.

- Test enabled movement directions with the arrow keys or WASD.
- Test the Run Modifier with either Shift or its mapped keyboard button: Wii U A=`Z`, B=`X`, X=`C`, and Y=`V`.
- Walking speed, running speed, diagonal normalization, screen boundaries, facing direction, and directional idle/walk animations are simulated.
- Press Escape or close the window to stop testing.

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

The animated-character tools include named animations, multiple PNG frames, ordering, FPS, looping, preview playback, transparency, directional state assignments, and native TV/GamePad animation.

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
5. In the devkitPro MSYS2 terminal, enter the versioned exported `utopia_wiiu_export_v0_95_02` directory and run `make`.
6. Copy `game.wuhb` to `wiiu/apps/utopia_test/game.wuhb` on the Aroma SD card.

## Version 0.95.02 test

Create a variable such as `WalkSpeed = 100`, assign it as the speed source for the four Move Character nodes, then connect a GamePad button to **Set Variable** or **Change Variable**. In Test Run, confirm the button changes movement speed immediately. Also test a **Compare Variable** between an input and a movement/action node to confirm the action is allowed only when the comparison is true. Then connect one GamePad input to two different Move Character directions and confirm both execute together. Also confirm Start executes once, Update executes continuously, variable actions fire from their connected paths, Compare Variable gates downstream nodes, and **Delete Link** removes only the selected connection. Export `utopia_wiiu_export_v0_95_02` and repeat the runtime test in Cemu or on Wii U hardware when available.

Utopia Game Studio is not affiliated with or endorsed by Nintendo, Epic Games, or YoYo Games.
