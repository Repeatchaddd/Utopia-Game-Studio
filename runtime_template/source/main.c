#include <vpad/input.h>
#include <whb/proc.h>
#include "game_config.h"
#include "animation_frames.h"
#include "blueprint_logic.h"
#include "renderer.h"
#include "room_data.h"

static int room_blocked(int x, int y) {
    const int points[4][2] = {{x,y},{x+PLAYER_W-1,y},{x,y+PLAYER_H-1},{x+PLAYER_W-1,y+PLAYER_H-1}};
    for (int i=0;i<4;++i) {
        int cx=points[i][0]/TILE_SIZE, cy=points[i][1]/TILE_SIZE;
        if (cx>=0 && cx<ROOM_COLS && cy>=0 && cy<ROOM_ROWS) {
            uint8_t t=ROOM_MAP[cy*ROOM_COLS+cx];
            if (t!=255 && t<TILE_COUNT && ROOM_SOLID[t]) return 1;
        }
    }
    return 0;
}

static void draw_room(void) {
    for (int gy=0; gy<ROOM_ROWS; ++gy)
        for (int gx=0; gx<ROOM_COLS; ++gx) {
            uint8_t t=ROOM_MAP[gy*ROOM_COLS+gx];
            if (t!=255 && t<TILE_COUNT)
                UtopiaRendererDrawSprite(gx*TILE_SIZE, gy*TILE_SIZE, TILE_SIZE, TILE_SIZE, ROOM_TILES[t], TILE_SIZE, TILE_SIZE);
        }
}

int main(int argc, char **argv)
{
    (void)argc; (void)argv;
    WHBProcInit();
    if (!UtopiaRendererInit()) {
        WHBProcShutdown();
        return 1;
    }

    int x = START_X, y = START_Y;
    VPADStatus input;
    VPADReadError error;
    unsigned int animation_tick = 0;
    unsigned int animation_frame = 0;
    int facing = 0; /* down, left, right, up */
    const UtopiaAnimation *previous_animation = 0;
    int bp_first_frame = 1;
    while (WHBProcIsRunning()) {
        int move_x100 = 0, move_y100 = 0, run_percent = 100;
        uint32_t hold = 0, trigger = 0;
        VPADRead(VPAD_CHAN_0, &input, 1, &error);
        if (error == VPAD_READ_SUCCESS) {
            hold = input.hold; trigger = input.trigger;
            BPApplyFrameActions(trigger, bp_first_frame);
            BPCollectMovement(hold, bp_first_frame, &move_x100, &move_y100, &run_percent);
            if (input.trigger & VPAD_BUTTON_PLUS) break;
        }
        bp_first_frame = 0;
        int delta_x = PLAYER_SPEED * move_x100 / 100;
        int delta_y = PLAYER_SPEED * move_y100 / 100;
        if (run_percent != 100) { delta_x = delta_x * run_percent / 100; delta_y = delta_y * run_percent / 100; }
        /* 181/256 is approximately 1/sqrt(2), keeping diagonals from moving faster. */
        if (delta_x && delta_y) { delta_x = delta_x * 181 / 256; delta_y = delta_y * 181 / 256; }
        int next_x = x + delta_x;
        int next_y = y + delta_y;
        if (!room_blocked(next_x, y)) x = next_x;
        if (!room_blocked(x, next_y)) y = next_y;
        if (delta_y > 0) facing = 0;
        else if (delta_x < 0) facing = 1;
        else if (delta_x > 0) facing = 2;
        else if (delta_y < 0) facing = 3;
        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x > 1280 - PLAYER_W) x = 1280 - PLAYER_W;
        if (y > 720 - PLAYER_H) y = 720 - PLAYER_H;

        UtopiaRendererBegin(BACKGROUND_COLOR);
        draw_room();
#if HAS_ANIMATION
        const UtopiaAnimation *idle[] = {&ANIM_IDLE_DOWN, &ANIM_IDLE_LEFT, &ANIM_IDLE_RIGHT, &ANIM_IDLE_UP};
        const UtopiaAnimation *walk[] = {&ANIM_WALK_DOWN, &ANIM_WALK_LEFT, &ANIM_WALK_RIGHT, &ANIM_WALK_UP};
        const UtopiaAnimation *animation = (delta_x || delta_y) ? walk[facing] : idle[facing];
        if (!animation->count) animation = (delta_x || delta_y) ? idle[facing] : walk[facing];
        if (animation != previous_animation) { animation_frame = 0; animation_tick = 0; previous_animation = animation; }
        if (animation->count) {
            UtopiaRendererDrawSprite(x, y, PLAYER_W, PLAYER_H, animation->frames[animation_frame], animation->width, animation->height);
        } else {
            UtopiaRendererDrawSolid(x, y, PLAYER_W, PLAYER_H, PLAYER_COLOR);
        }
        if (animation->count && ++animation_tick >= animation->delay) {
            animation_tick = 0;
            if (animation_frame + 1 < animation->count) ++animation_frame;
            else if (animation->loop) animation_frame = 0;
        }
#else
        UtopiaRendererDrawSolid(x, y, PLAYER_W, PLAYER_H, PLAYER_COLOR);
#endif
        UtopiaRendererEnd();
    }

    UtopiaRendererShutdown();
    WHBProcShutdown();
    return 0;
}
