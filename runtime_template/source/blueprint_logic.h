#pragma once
#include <stdint.h>
#define BP_VAR_COUNT 0
static int bp_vars[1] = {0};
static inline int bp_compare_value(int left,int op,int right){switch(op){case 0:return left==right;case 1:return left!=right;case 2:return left<right;case 3:return left<=right;case 4:return left>right;case 5:return left>=right;default:return 1;}}
static inline int bp_gate(int idx,int op,int value){return idx<0?1:bp_compare_value(bp_vars[idx],op,value);}
#define BP_MOVE_LEFT 1
#define BP_MOVE_LEFT_SPEED 100
#define BP_MOVE_LEFT_SPEED_VAR -1
#define BP_MOVE_LEFT_GATE_VAR -1
#define BP_MOVE_LEFT_GATE_OP 0
#define BP_MOVE_LEFT_GATE_VALUE 0
#define BP_MOVE_RIGHT 1
#define BP_MOVE_RIGHT_SPEED 100
#define BP_MOVE_RIGHT_SPEED_VAR -1
#define BP_MOVE_RIGHT_GATE_VAR -1
#define BP_MOVE_RIGHT_GATE_OP 0
#define BP_MOVE_RIGHT_GATE_VALUE 0
#define BP_MOVE_UP 1
#define BP_MOVE_UP_SPEED 100
#define BP_MOVE_UP_SPEED_VAR -1
#define BP_MOVE_UP_GATE_VAR -1
#define BP_MOVE_UP_GATE_OP 0
#define BP_MOVE_UP_GATE_VALUE 0
#define BP_MOVE_DOWN 1
#define BP_MOVE_DOWN_SPEED 100
#define BP_MOVE_DOWN_SPEED_VAR -1
#define BP_MOVE_DOWN_GATE_VAR -1
#define BP_MOVE_DOWN_GATE_OP 0
#define BP_MOVE_DOWN_GATE_VALUE 0
#define BP_RUN_ENABLED 1
#define BP_RUN_BUTTON VPAD_BUTTON_B
#define BP_RUN_SPEED 175
#define BP_RUN_SPEED_VAR -1
#define BP_RUN_GATE_VAR -1
#define BP_RUN_GATE_OP 0
#define BP_RUN_GATE_VALUE 0
static inline void BPApplyTriggered(uint32_t trigger){(void)trigger;}
