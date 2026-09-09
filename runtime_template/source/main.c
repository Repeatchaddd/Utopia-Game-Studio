#include <coreinit/memdefaultheap.h>
#include <coreinit/screen.h>
#include <vpad/input.h>
#include <whb/proc.h>
#include "game_config.h"

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
    while (WHBProcIsRunning()) {
        VPADRead(VPAD_CHAN_0, &input, 1, &error);
        if (error == VPAD_READ_SUCCESS) {
            if (input.hold & VPAD_BUTTON_LEFT)  x -= PLAYER_SPEED;
            if (input.hold & VPAD_BUTTON_RIGHT) x += PLAYER_SPEED;
            if (input.hold & VPAD_BUTTON_UP)    y -= PLAYER_SPEED;
            if (input.hold & VPAD_BUTTON_DOWN)  y += PLAYER_SPEED;
            if (input.trigger & VPAD_BUTTON_PLUS) break;
        }
        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x > 1280 - PLAYER_W) x = 1280 - PLAYER_W;
        if (y > 720 - PLAYER_H) y = 720 - PLAYER_H;

        OSScreenClearBufferEx(SCREEN_TV, BACKGROUND_COLOR);
        OSScreenClearBufferEx(SCREEN_DRC, BACKGROUND_COLOR);
        fill_rect(SCREEN_TV, x, y, PLAYER_W, PLAYER_H, PLAYER_COLOR, 1280, 720);
        fill_rect(SCREEN_DRC, x, y, PLAYER_W, PLAYER_H, PLAYER_COLOR, 1280, 720);
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
