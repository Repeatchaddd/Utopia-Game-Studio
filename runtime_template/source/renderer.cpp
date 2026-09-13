#include "renderer.h"
#include "CafeGLSLCompiler.h"

#include <coreinit/memdefaultheap.h>
#include <gx2/draw.h>
#include <gx2/mem.h>
#include <gx2/registers.h>
#include <gx2/shaders.h>
#include <gx2/surface.h>
#include <gx2r/buffer.h>
#include <gx2r/draw.h>
#include <whb/gfx.h>
#include <whb/log.h>
#include <string.h>

static const char *VERTEX_SHADER = R"(
#version 450
layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aTexCoord;
layout(location = 0) out vec2 TexCoord;
void main() {
    TexCoord = aTexCoord;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
)";

static const char *PIXEL_SHADER = R"(
#version 450
#extension GL_ARB_shading_language_420pack: enable
layout(location = 0) in vec2 TexCoord;
layout(location = 0) out vec4 FragColor;
layout(binding = 0) uniform sampler2D spriteTexture;
void main() {
    vec4 c = texture(spriteTexture, TexCoord);
    if (c.a <= 0.001) discard;
    FragColor = c;
}
)";

static WHBGfxShaderGroup shaderGroup = {};
static GX2RBuffer positionBuffer = {};
static GX2RBuffer texCoordBuffer = {};
static GX2Sampler sampler = {};
typedef struct {
    GX2Texture texture;
    const uint32_t *pixels;
    unsigned int width, height;
    bool ready;
} TextureSlot;
static TextureSlot textureCache[256] = {};
static uint32_t frameBackground = 0;
typedef struct { int x,y,w,h; const uint32_t *pixels; unsigned int tw,th; } DrawCommand;
static DrawCommand commands[1024];
static unsigned int commandCount = 0;

static const float texCoords[8] = {
    0.0f, 1.0f,
    1.0f, 1.0f,
    1.0f, 0.0f,
    0.0f, 0.0f
};

static void destroyTextures(void) {
    for (unsigned int i = 0; i < 256; ++i) {
        if (textureCache[i].ready && textureCache[i].texture.surface.image)
            MEMFreeToDefaultHeap(textureCache[i].texture.surface.image);
        memset(&textureCache[i], 0, sizeof(textureCache[i]));
    }
}

static GX2Texture *getTexture(const uint32_t *pixels, unsigned int width, unsigned int height) {
    if (!pixels || !width || !height) return nullptr;
    for (unsigned int i = 0; i < 256; ++i)
        if (textureCache[i].ready && textureCache[i].pixels == pixels &&
            textureCache[i].width == width && textureCache[i].height == height)
            return &textureCache[i].texture;

    TextureSlot *slot = nullptr;
    for (unsigned int i = 0; i < 256; ++i)
        if (!textureCache[i].ready) { slot = &textureCache[i]; break; }
    if (!slot) return nullptr;

    GX2Texture *texture = &slot->texture;
    memset(texture, 0, sizeof(*texture));
    texture->surface.dim = GX2_SURFACE_DIM_TEXTURE_2D;
    texture->surface.width = width;
    texture->surface.height = height;
    texture->surface.depth = 1;
    texture->surface.mipLevels = 1;
    texture->surface.format = GX2_SURFACE_FORMAT_UNORM_R8_G8_B8_A8;
    texture->surface.aa = GX2_AA_MODE1X;
    texture->surface.use = GX2_SURFACE_USE_TEXTURE;
    texture->surface.tileMode = GX2_TILE_MODE_LINEAR_ALIGNED;
    texture->viewNumSlices = 1;
    texture->compMap = 0x00010203;
    GX2CalcSurfaceSizeAndAlignment(&texture->surface);
    GX2InitTextureRegs(texture);
    texture->surface.image = MEMAllocFromDefaultHeapEx(texture->surface.imageSize, texture->surface.alignment);
    if (!texture->surface.image) return nullptr;

    uint32_t *dst = (uint32_t*)texture->surface.image;
    for (unsigned int y = 0; y < height; ++y)
        memcpy(dst + y * texture->surface.pitch, pixels + y * width, width * sizeof(uint32_t));
    GX2Invalidate(GX2_INVALIDATE_MODE_CPU_TEXTURE, texture->surface.image, texture->surface.imageSize);

    slot->pixels = pixels;
    slot->width = width;
    slot->height = height;
    slot->ready = true;
    return texture;
}

static void setQuad(int x, int y, int w, int h) {
    const float l = ((float)x / 640.0f) - 1.0f;
    const float r = ((float)(x + w) / 640.0f) - 1.0f;
    const float t = 1.0f - ((float)y / 360.0f);
    const float b = 1.0f - ((float)(y + h) / 360.0f);
    const float pos[8] = { l,b, r,b, r,t, l,t };
    void *buffer = GX2RLockBufferEx(&positionBuffer, GX2R_RESOURCE_BIND_NONE);
    memcpy(buffer, pos, sizeof(pos));
    GX2RUnlockBufferEx(&positionBuffer, GX2R_RESOURCE_BIND_NONE);
}

static void bindAndDraw(GX2Texture *texture) {
    GX2SetFetchShader(&shaderGroup.fetchShader);
    GX2SetVertexShader(shaderGroup.vertexShader);
    GX2SetPixelShader(shaderGroup.pixelShader);
    GX2SetShaderMode(GX2_SHADER_MODE_UNIFORM_BLOCK);
    GX2RSetAttributeBuffer(&positionBuffer, 0, positionBuffer.elemSize, 0);
    GX2RSetAttributeBuffer(&texCoordBuffer, 1, texCoordBuffer.elemSize, 0);
    GX2SetPixelTexture(texture, shaderGroup.pixelShader->samplerVars[0].location);
    GX2SetPixelSampler(&sampler, shaderGroup.pixelShader->samplerVars[0].location);
    GX2DrawEx(GX2_PRIMITIVE_MODE_QUADS, 4, 0, 1);
}

bool UtopiaRendererInit(void) {
    WHBGfxInit();
    if (!GLSL_Init()) { WHBGfxShutdown(); return false; }

    char log[1024] = {};
    shaderGroup.vertexShader = GLSL_CompileVertexShader(VERTEX_SHADER, log, sizeof(log), GLSL_COMPILER_FLAG_NONE);
    if (!shaderGroup.vertexShader) { WHBLogPrintf("Utopia vertex shader: %s", log); return false; }
    memset(log, 0, sizeof(log));
    shaderGroup.pixelShader = GLSL_CompilePixelShader(PIXEL_SHADER, log, sizeof(log), GLSL_COMPILER_FLAG_NONE);
    if (!shaderGroup.pixelShader) { WHBLogPrintf("Utopia pixel shader: %s", log); return false; }

    GX2Invalidate(GX2_INVALIDATE_MODE_CPU_SHADER, shaderGroup.vertexShader->program, shaderGroup.vertexShader->size);
    GX2Invalidate(GX2_INVALIDATE_MODE_CPU_SHADER, shaderGroup.pixelShader->program, shaderGroup.pixelShader->size);
    WHBGfxInitShaderAttribute(&shaderGroup, "aPos", 0, 0, GX2_ATTRIB_FORMAT_FLOAT_32_32);
    WHBGfxInitShaderAttribute(&shaderGroup, "aTexCoord", 1, 0, GX2_ATTRIB_FORMAT_FLOAT_32_32);
    WHBGfxInitFetchShader(&shaderGroup);

    positionBuffer.flags = GX2R_RESOURCE_BIND_VERTEX_BUFFER | GX2R_RESOURCE_USAGE_CPU_WRITE | GX2R_RESOURCE_USAGE_GPU_READ;
    positionBuffer.elemSize = 2 * sizeof(float);
    positionBuffer.elemCount = 4;
    GX2RCreateBuffer(&positionBuffer);

    texCoordBuffer.flags = GX2R_RESOURCE_BIND_VERTEX_BUFFER | GX2R_RESOURCE_USAGE_CPU_WRITE | GX2R_RESOURCE_USAGE_GPU_READ;
    texCoordBuffer.elemSize = 2 * sizeof(float);
    texCoordBuffer.elemCount = 4;
    GX2RCreateBuffer(&texCoordBuffer);
    void *uv = GX2RLockBufferEx(&texCoordBuffer, GX2R_RESOURCE_BIND_NONE);
    memcpy(uv, texCoords, sizeof(texCoords));
    GX2RUnlockBufferEx(&texCoordBuffer, GX2R_RESOURCE_BIND_NONE);

    GX2InitSampler(&sampler, GX2_TEX_CLAMP_MODE_CLAMP, GX2_TEX_XY_FILTER_MODE_POINT);
    GX2SetSwapInterval(1);
    return true;
}

void UtopiaRendererShutdown(void) {
    destroyTextures();
    GX2RDestroyBufferEx(&positionBuffer, GX2R_RESOURCE_BIND_NONE);
    GX2RDestroyBufferEx(&texCoordBuffer, GX2R_RESOURCE_BIND_NONE);
    if (shaderGroup.vertexShader && GLSL_FreeVertexShader) GLSL_FreeVertexShader(shaderGroup.vertexShader);
    if (shaderGroup.pixelShader && GLSL_FreePixelShader) GLSL_FreePixelShader(shaderGroup.pixelShader);
    /* CafeGLSL RPL unloading is intentionally left to title shutdown on Wii U. */
    WHBGfxShutdown();
}

static void colorFloats(uint32_t c, float *r, float *g, float *b, float *a) {
    *r = ((c >> 24) & 255) / 255.0f;
    *g = ((c >> 16) & 255) / 255.0f;
    *b = ((c >> 8) & 255) / 255.0f;
    *a = (c & 255) / 255.0f;
}

void UtopiaRendererBegin(uint32_t background_rgba) {
    float r,g,b,a;
    colorFloats(background_rgba,&r,&g,&b,&a);
    frameBackground = background_rgba;
    commandCount = 0;
    WHBGfxBeginRender();
    WHBGfxBeginRenderTV();
    WHBGfxClearColor(r,g,b,a);
}

void UtopiaRendererDrawSprite(int x, int y, int w, int h, const uint32_t *pixels,
                              unsigned int texture_width, unsigned int texture_height) {
    if (commandCount < 1024) commands[commandCount++] = (DrawCommand){x,y,w,h,pixels,texture_width,texture_height};
    GX2Texture *texture = getTexture(pixels, texture_width, texture_height);
    if (!texture) return;
    setQuad(x,y,w,h);
    bindAndDraw(texture);
}

void UtopiaRendererDrawSolid(int x, int y, int w, int h, uint32_t rgba) {
    static uint32_t solid;
    solid = rgba;
    UtopiaRendererDrawSprite(x,y,w,h,&solid,1,1);
}

void UtopiaRendererEnd(void) {
    WHBGfxFinishRenderTV();

    float r,g,b,a;
    colorFloats(frameBackground,&r,&g,&b,&a);
    WHBGfxBeginRenderDRC();
    WHBGfxClearColor(r,g,b,a);
    for (unsigned int i = 0; i < commandCount; ++i) {
        DrawCommand *cmd = &commands[i];
        GX2Texture *texture = getTexture(cmd->pixels, cmd->tw, cmd->th);
        if (!texture) continue;
        setQuad(cmd->x,cmd->y,cmd->w,cmd->h);
        bindAndDraw(texture);
    }
    WHBGfxFinishRenderDRC();
    WHBGfxFinishRender();
}
