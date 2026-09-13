#pragma once
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

bool UtopiaRendererInit(void);
void UtopiaRendererShutdown(void);
void UtopiaRendererBegin(uint32_t background_rgba);
void UtopiaRendererDrawSprite(int x, int y, int w, int h,
                              const uint32_t *pixels,
                              unsigned int texture_width,
                              unsigned int texture_height);
void UtopiaRendererDrawSolid(int x, int y, int w, int h, uint32_t rgba);
void UtopiaRendererEnd(void);

#ifdef __cplusplus
}
#endif
