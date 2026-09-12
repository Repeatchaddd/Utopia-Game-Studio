# Utopia Game Studio 0.2

Utopia Game Studio is an independent visual creator for native Wii U homebrew games. It focuses exclusively on **2D and 2.5D games** and shares no code, project format, or versioning with Next64.

## Version 0.2

- Creates, opens, and saves `.ugs` projects.
- Imports PNG frames up to 128×128 pixels.
- Groups frames into named animations such as `idle`, `walk`, and `jump`.
- Reorders and deletes frames.
- Sets animation speed from 1–60 FPS and enables or disables looping.
- Plays animation previews inside the editor.
- Assigns one active animation to the character.
- Exports the active animation as native C pixel data.
- Animates the character on both TV and GamePad.
- Moves the character with the GamePad D-pad; Plus exits.
- Opens and upgrades Version 0.1 `.wugc` projects.

The structure is inspired by the approachable sprite/animation workflow of GameMaker Studio 2, but the implementation and source are original.

## Run on Windows

1. Install Python 3 from https://www.python.org/ and enable **Add Python to PATH**.
2. Double-click `run_editor.bat`.
3. Create or select an animation under **Animated Character**.
4. Import equally sized PNG frames in playback order.
5. Choose the animation under **Scene → Active animation**.
6. Save the project and select **Export Wii U Project**.

PNG files are stored inside the `.ugs` project, making the project portable. Transparent PNG pixels remain transparent in the Wii U export.

## Build for Aroma

1. Install devkitPro for Windows: https://devkitpro.org/wiki/Getting_Started
2. Open the devkitPro MSYS2 terminal.
3. Run `pacman -Syu --needed wiiu-dev`.
4. Change to the generated `utopia_wiiu_export` directory.
5. Run `make` to create `game.wuhb`.
6. Copy it to `wiiu/apps/utopia_test/game.wuhb` on the Aroma SD card.

## Version 0.2 test order

1. Test the editor with two small, equally sized PNG frames.
2. Verify Play and Stop, FPS, looping, reordering, save, and reopen.
3. Export and compile.
4. Verify animation and D-pad movement on both the TV and GamePad.

The native renderer is intentionally simple. Keep initial test frames around 16×16 or 32×32 pixels and display sizes modest while we establish reliable real-hardware behavior.

Utopia Game Studio is an independent homebrew project and is not affiliated with or endorsed by Nintendo.
