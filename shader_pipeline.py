"""GLSL post-FX pipeline — pygame surface → GL texture → fullscreen quad."""

import os
import time
from array import array

import pygame


try:
    import moderngl
    _MODERNGL_AVAILABLE = True
except Exception:
    _MODERNGL_AVAILABLE = False


SHADER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shaders")


class ShaderPipeline:

    @classmethod
    def create(cls, size, fullscreen=False, shader="cyberpunk"):
        # falls back to plain blitting if moderngl is missing/broken
        if not _MODERNGL_AVAILABLE:
            print("[shader] moderngl not installed — running without post-FX.")
            return _PassthroughPipeline(size, fullscreen)
        try:
            return cls(size, fullscreen, shader)
        except Exception as exc:
            print(f"[shader] disabled ({exc.__class__.__name__}: {exc}) — falling back.")
            return _PassthroughPipeline(size, fullscreen)

    def __init__(self, size, fullscreen, shader_name):
        self._size = (int(size[0]), int(size[1]))
        self._shader_name = shader_name

        # request GL 3.3 core to match `#version 330 core` shaders
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
        pygame.display.set_mode(self._size, flags)

        self._ctx = moderngl.create_context()
        self._ctx.enable(moderngl.BLEND)

        self._build_quad()
        self._program = self._compile_program(shader_name)
        self._vao = self._make_vao(self._program)
        self._build_texture()

        self._start_time = time.perf_counter()
        self._enabled = True
        self._glitch = 0.0
        self._glitch_decay = 0.85

        # explicit BGRA layout — raw buffer uploads with no conversion
        self._surface = pygame.Surface(
            self._size, 0, 32,
            (0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000),
        )

    def _build_quad(self):
        # x, y, u, v
        verts = array("f", [
            -1.0,  1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
        ])
        self._vbo = self._ctx.buffer(verts.tobytes())

    def _compile_program(self, name):
        with open(os.path.join(SHADER_DIR, "passthrough.vert"), "r", encoding="utf-8") as f:
            vert_src = f.read()
        with open(os.path.join(SHADER_DIR, f"{name}.frag"), "r", encoding="utf-8") as f:
            frag_src = f.read()
        return self._ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)

    def _make_vao(self, program):
        return self._ctx.vertex_array(
            program, [(self._vbo, "2f 2f", "vert", "tex_coord")]
        )

    def _build_texture(self):
        self._tex = self._ctx.texture(self._size, 4)
        self._tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._tex.repeat_x = False
        self._tex.repeat_y = False
        # surface bytes are BGRA — remap so shader's .rgba is correct
        self._tex.swizzle = "BGRA"

    @property
    def surface(self):
        return self._surface

    def set_shader(self, name):
        if name == self._shader_name:
            return
        try:
            new_program = self._compile_program(name)
        except Exception as exc:
            print(f"[shader] failed to swap to '{name}': {exc}")
            return
        self._program.release()
        self._vao.release()
        self._program = new_program
        self._vao = self._make_vao(self._program)
        self._shader_name = name

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)

    def toggle(self):
        self._enabled = not self._enabled
        return self._enabled

    def pulse_glitch(self, amount=1.0):
        self._glitch = max(self._glitch, float(amount))

    def present(self):
        # zero-copy upload via buffer protocol
        self._tex.write(self._surface.get_buffer())
        self._tex.use(0)

        self._set_uniform("u_texture", 0)
        self._set_uniform("u_time", time.perf_counter() - self._start_time)
        self._set_uniform("u_resolution", self._size)
        self._set_uniform("u_intensity", 1.0 if self._enabled else 0.0)
        self._set_uniform("u_glitch", self._glitch)

        self._ctx.clear(0.0, 0.0, 0.0, 1.0)
        self._vao.render(mode=moderngl.TRIANGLE_STRIP)
        pygame.display.flip()

        self._glitch *= self._glitch_decay
        if self._glitch < 0.01:
            self._glitch = 0.0

    def shutdown(self):
        try:
            self._tex.release()
            self._vao.release()
            self._program.release()
            self._vbo.release()
            self._ctx.release()
        except Exception:
            pass

    def _set_uniform(self, name, value):
        # silently skip uniforms the shader doesn't declare
        try:
            self._program[name].value = value
        except KeyError:
            pass


class _PassthroughPipeline:
    """Fallback when ModernGL is unavailable."""

    def __init__(self, size, fullscreen):
        self._size = (int(size[0]), int(size[1]))
        flags = pygame.FULLSCREEN if fullscreen else 0
        self._display = pygame.display.set_mode(self._size, flags)
        self._surface = pygame.Surface(self._size).convert()

    @property
    def surface(self):
        return self._surface

    def set_shader(self, _name):
        pass

    def set_enabled(self, _e):
        pass

    def toggle(self):
        return False

    def pulse_glitch(self, _a=1.0):
        pass

    def present(self):
        self._display.blit(self._surface, (0, 0))
        pygame.display.flip()

    def shutdown(self):
        pass
