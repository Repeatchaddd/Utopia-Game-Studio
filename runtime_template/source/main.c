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
    while (WHBProcIsRunning()) {
        int move_x = 0, move_y = 0, running = 0;
        int speed_x = PLAYER_SPEED, speed_y = PLAYER_SPEED;
        VPADRead(VPAD_CHAN_0, &input, 1, &error);
        if (error == VPAD_READ_SUCCESS) {
#if BP_MOVE_LEFT
            if (input.hold & VPAD_BUTTON_LEFT)  { move_x -= 1; speed_x = PLAYER_SPEED * BP_MOVE_LEFT_SPEED / 100; }
#endif
#if BP_MOVE_RIGHT
            if (input.hold & VPAD_BUTTON_RIGHT) { move_x += 1; speed_x = PLAYER_SPEED * BP_MOVE_RIGHT_SPEED / 100; }
#endif
#if BP_MOVE_UP
            if (input.hold & VPAD_BUTTON_UP)    { move_y -= 1; speed_y = PLAYER_SPEED * BP_MOVE_UP_SPEED / 100; }
#endif
#if BP_MOVE_DOWN
            if (input.hold & VPAD_BUTTON_DOWN)  { move_y += 1; speed_y = PLAYER_SPEED * BP_MOVE_DOWN_SPEED / 100; }
#endif
#if BP_RUN_ENABLED
            if (input.hold & BP_RUN_BUTTON) running = 1;
#endif
            if (input.trigger & VPAD_BUTTON_PLUS) break;
        }
        /* 181/256 is approximately 1/sqrt(2), keeping diagonals from moving faster. */
        if (running) { speed_x = speed_x * BP_RUN_SPEED / 100; speed_y = speed_y * BP_RUN_SPEED / 100; }
        if (move_x && move_y) { speed_x = speed_x * 181 / 256; speed_y = speed_y * 181 / 256; }
        if (speed_x < 1) speed_x = 1;
        if (speed_y < 1) speed_y = 1;
        int next_x = x + move_x * speed_x;
        int next_y = y + move_y * speed_y;
        if (!room_blocked(next_x, y)) x = next_x;
        if (!room_blocked(x, next_y)) y = next_y;
        if (move_y > 0) facing = 0;
        else if (move_x < 0) facing = 1;
        else if (move_x > 0) facing = 2;
        else if (move_y < 0) facing = 3;
        if (x < 0) x = 0;
        if (y < 0) y = 0;
        if (x > 1280 - PLAYER_W) x = 1280 - PLAYER_W;
        if (y > 720 - PLAYER_H) y = 720 - PLAYER_H;

        UtopiaRendererBegin(BACKGROUND_COLOR);
        draw_room();
#if HAS_ANIMATION
        const UtopiaAnimation *idle[] = {&ANIM_IDLE_DOWN, &ANIM_IDLE_LEFT, &ANIM_IDLE_RIGHT, &ANIM_IDLE_UP};
        const UtopiaAnimation *walk[] = {&ANIM_WALK_DOWN, &ANIM_WALK_LEFT, &ANIM_WALK_RIGHT, &ANIM_WALK_UP};
        const UtopiaAnimation *animation = (move_x || move_y) ? walk[facing] : idle[facing];
        if (!animation->count) animation = (move_x || move_y) ? idle[facing] : walk[facing];
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
