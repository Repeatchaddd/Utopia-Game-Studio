#include <coreinit/memdefaultheap.h>
#include <coreinit/screen.h>
#include <vpad/input.h>
#include <whb/proc.h>
#include "game_config.h"
#include "animation_frames.h"
#include "blueprint_logic.h"

static void fill_rect(OSScreenID screen, int x, int y, int w, int h, uint32_t color,
                      int logical_w, int logical_h)
{
    int sx = screen == SCREEN_TV ? 1 : 0;
    int out_w = screen == SCREEN_TV ? 1280 : 854;
    int out_h = screen == SCREEN_TV ? 720 : 480;
    int left = x * out_w / logical_w;
    int top = y * out_h / logical_h;
    int right = (x + w) * out_w / logical_w;
    int bottom = (y + h) * out_h / logical_h;
    (void)sx;
    for (int py = top; py < bottom; ++py)
        for (int px = left; px < right; ++px)
            OSScreenPutPixelEx(screen, px, py, color);
}

#if HAS_ANIMATION
static void draw_frame(OSScreenID screen, int x, int y, int w, int h, const uint32_t *pixels)
{
    int out_w = screen == SCREEN_TV ? 1280 : 854;
    int out_h = screen == SCREEN_TV ? 720 : 480;
    int left = x * out_w / 1280;
    int top = y * out_h / 720;
    int draw_w = w * out_w / 1280;
    int draw_h = h * out_h / 720;
    for (int dy = 0; dy < draw_h; ++dy) {
        int source_y = dy * FRAME_HEIGHT / draw_h;
        for (int dx = 0; dx < draw_w; ++dx) {
            int source_x = dx * FRAME_WIDTH / draw_w;
            uint32_t color = pixels[source_y * FRAME_WIDTH + source_x];
            if (color != 0) OSScreenPutPixelEx(screen, left + dx, top + dy, color);
        }
    }
}
#endif

int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    WHBProcInit();
    OSScreenInit();

    uint32_t tv_size = OSScreenGetBufferSizeEx(SCREEN_TV);
    uint32_t drc_size = OSScreenGetBufferSizeEx(SCREEN_DRC);
    void *tv = MEMAllocFromDefaultHeapEx(tv_size, 0x100);
    void *drc = MEMAllocFromDefaultHeapEx(drc_size, 0x100);
    if (!tv || !drc) {
        if (tv) MEMFreeToDefaultHeap(tv);
        if (drc) MEMFreeToDefaultHeap(drc);
        WHBProcShutdown();
        return 1;
    }
    OSScreenSetBufferEx(SCREEN_TV, tv);
    OSScreenSetBufferEx(SCREEN_DRC, drc);
    OSScreenEnableEx(SCREEN_TV, true);
    OSScreenEnableEx(SCREEN_DRC, true);

    int x = START_X, y = START_Y;
    VPADStatus input;
    VPADReadError error;
    unsigned int animation_tick = 0;
    unsigned int animation_frame = 0;
    while (WHBProcIsRunning()) {
        VPADRead(VPAD_CHAN_0, &input, 1, &error);
        if (error == VPAD_READ_SUCCESS) {
#if BP_MOVE_LEFT
            if (input.hold & VPAD_BUTTON_LEFT)  x -= PLAYER_SPEED;
#endif
#if BP_MOVE_RIGHT
            if (input.hold & VPAD_BUTTON_RIGHT) x += PLAYER_SPEED;
#endif
#if BP_MOVE_UP
            if (input.hold & VPAD_BUTTON_UP)    y -= PLAYER_SPEED;
#endif
#if BP_MOVE_DOWN
            if (input.hold & VPAD_BUTTON_DOWN)  y += PLAYER_SPEED;
#endif
            if (input.trigger & VPAD_BUTTON_PLUS) break;
        }
        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x > 1280 - PLAYER_W) x = 1280 - PLAYER_W;
        if (y > 720 - PLAYER_H) y = 720 - PLAYER_H;

        OSScreenClearBufferEx(SCREEN_TV, BACKGROUND_COLOR);
        OSScreenClearBufferEx(SCREEN_DRC, BACKGROUND_COLOR);
#if HAS_ANIMATION
        draw_frame(SCREEN_TV, x, y, PLAYER_W, PLAYER_H, animation_frames[animation_frame]);
        draw_frame(SCREEN_DRC, x, y, PLAYER_W, PLAYER_H, animation_frames[animation_frame]);
        if (++animation_tick >= FRAME_DELAY) {
            animation_tick = 0;
            if (animation_frame + 1 < FRAME_COUNT) ++animation_frame;
            else if (ANIMATION_LOOP) animation_frame = 0;
        }
#else
        fill_rect(SCREEN_TV, x, y, PLAYER_W, PLAYER_H, PLAYER_COLOR, 1280, 720);
        fill_rect(SCREEN_DRC, x, y, PLAYER_W, PLAYER_H, PLAYER_COLOR, 1280, 720);
#endif
        OSScreenFlipBuffersEx(SCREEN_TV);
        OSScreenFlipBuffersEx(SCREEN_DRC);
    }

    OSScreenEnableEx(SCREEN_TV, false);
    OSScreenEnableEx(SCREEN_DRC, false);
    MEMFreeToDefaultHeap(tv);
    MEMFreeToDefaultHeap(drc);
    WHBProcShutdown();
    return 0;
}
