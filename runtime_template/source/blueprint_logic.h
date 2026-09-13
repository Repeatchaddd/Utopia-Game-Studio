#pragma once
#include <stdint.h>
#define BP_VAR_COUNT 0
static int bp_vars[1] = {0};
static inline int bp_compare_value(int left,int op,int right){switch(op){case 0:return left==right;case 1:return left!=right;case 2:return left<right;case 3:return left<=right;case 4:return left>right;case 5:return left>=right;default:return 1;}}
static inline int bp_gate(int idx,int op,int value){return idx<0?1:bp_compare_value(bp_vars[idx],op,value);}
static inline int bp_speed_percent(int idx,int fallback,int lo,int hi){int value=idx>=0?bp_vars[idx]:fallback;if(value<lo)value=lo;if(value>hi)value=hi;return value;}
static inline void BPApplyFrameActions(uint32_t trigger,int first_frame){(void)trigger;(void)first_frame;}
static inline void BPCollectMovement(uint32_t hold,int first_frame,int *move_x100,int *move_y100,int *run_percent){(void)hold;(void)first_frame;*move_x100=0;*move_y100=0;*run_percent=100;}
