# Utopia Game Studio 0.75

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
5. In the devkitPro MSYS2 terminal, enter the exported `utopia_wiiu_export` directory and run `make`.
6. Copy `game.wuhb` to `wiiu/apps/utopia_test/game.wuhb` on the Aroma SD card.

## Version 0.75 test

Choose **Test Run**, move with both WASD and the arrow keys, and hold Shift or the mapped run key to compare walking and running speeds. Confirm disabled Blueprint directions do not move, diagonal movement is normalized, directional animations change correctly, and the character stays inside the scene.

Utopia Game Studio is not affiliated with or endorsed by Nintendo, Epic Games, or YoYo Games.
