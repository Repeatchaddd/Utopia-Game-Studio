#pragma once
#include <stdint.h>
#include <gx2/shaders.h>
#include <coreinit/dynload.h>
#include <coreinit/debug.h>

enum GLSL_COMPILER_FLAG {
    GLSL_COMPILER_FLAG_NONE = 0,
    GLSL_COMPILER_FLAG_GENERATE_DISASSEMBLY = 1 << 0
};

static OSDynLoad_Module utopia_glsl_module = nullptr;
static GX2VertexShader* (*GLSL_CompileVertexShader)(const char*, char*, int, GLSL_COMPILER_FLAG) = nullptr;
static GX2PixelShader* (*GLSL_CompilePixelShader)(const char*, char*, int, GLSL_COMPILER_FLAG) = nullptr;
static void (*GLSL_FreeVertexShader)(GX2VertexShader*) = nullptr;
static void (*GLSL_FreePixelShader)(GX2PixelShader*) = nullptr;
static void (*GLSL_DestroyCompiler)(void) = nullptr;

static inline bool GLSL_Init(void) {
    if (utopia_glsl_module != nullptr) return true;
    OSDynLoad_Error r = OSDynLoad_Acquire("glslcompiler", &utopia_glsl_module);
    if (r != OS_DYNLOAD_OK)
        r = OSDynLoad_Acquire("~/wiiu/libs/glslcompiler.rpl", &utopia_glsl_module);
    if (r != OS_DYNLOAD_OK) {
        OSReport("Utopia: glslcompiler.rpl not found\n");
        utopia_glsl_module = nullptr;
        return false;
    }
    void (*initCompiler)(void) = nullptr;
    OSDynLoad_FindExport(utopia_glsl_module, OS_DYNLOAD_EXPORT_FUNC, "InitGLSLCompiler", (void**)&initCompiler);
    OSDynLoad_FindExport(utopia_glsl_module, OS_DYNLOAD_EXPORT_FUNC, "CompileVertexShader", (void**)&GLSL_CompileVertexShader);
    OSDynLoad_FindExport(utopia_glsl_module, OS_DYNLOAD_EXPORT_FUNC, "CompilePixelShader", (void**)&GLSL_CompilePixelShader);
    OSDynLoad_FindExport(utopia_glsl_module, OS_DYNLOAD_EXPORT_FUNC, "FreeVertexShader", (void**)&GLSL_FreeVertexShader);
    OSDynLoad_FindExport(utopia_glsl_module, OS_DYNLOAD_EXPORT_FUNC, "FreePixelShader", (void**)&GLSL_FreePixelShader);
    OSDynLoad_FindExport(utopia_glsl_module, OS_DYNLOAD_EXPORT_FUNC, "DestroyGLSLCompiler", (void**)&GLSL_DestroyCompiler);
    if (!initCompiler || !GLSL_CompileVertexShader || !GLSL_CompilePixelShader) return false;
    initCompiler();
    return true;
}

static inline void GLSL_Shutdown(void) {
    if (utopia_glsl_module == nullptr) return;
    if (GLSL_DestroyCompiler) GLSL_DestroyCompiler();
    OSDynLoad_Release(utopia_glsl_module);
    utopia_glsl_module = nullptr;
}
