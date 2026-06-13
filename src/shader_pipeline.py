import os
import time
from array import array
from typing import Any

import pygame

moderngl: Any = None
try:
    import moderngl
    _MODERNGL_AVAILABLE = True
except Exception:
    _MODERNGL_AVAILABLE = False


SHADER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shaders")


class ShaderPipeline:

    @classmethod
    def create(cls, size, fullscreen=False, shader="cyberpunk", render_scale=1.0,
               display_size=None):
        if not _MODERNGL_AVAILABLE:
            print("[shader] moderngl not installed — running without post-FX.")
            return _PassthroughPipeline(size, fullscreen, display_size=display_size)
        try:
            return cls(size, fullscreen, shader, render_scale, display_size)
        except Exception as exc:
            print(f"[shader] disabled ({exc.__class__.__name__}: {exc}) — falling back.")
            return _PassthroughPipeline(size, fullscreen, display_size=display_size)

    @classmethod
    def create_passthrough(cls, size, fullscreen=False, display_size=None):
        return _PassthroughPipeline(size, fullscreen, display_size=display_size)

    def __init__(self, size, fullscreen, shader_name, render_scale, display_size=None):
        rw = max(1, int(size[0] * render_scale))
        rh = max(1, int(size[1] * render_scale))
        self._render_size = (rw, rh)
        if display_size is None:
            self._screen_size = (int(size[0]), int(size[1]))
        else:
            self._screen_size = (int(display_size[0]), int(display_size[1]))
        self._shader_name = shader_name

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
        pygame.display.set_mode(self._screen_size, flags)

        self._ctx = moderngl.create_context()
        self._ctx.enable(moderngl.BLEND)

        self._build_quad()

        self._scene_program = self._compile_program(shader_name)
        self._scene_vao = self._make_vao(self._scene_program)

        self._screen_program = self._compile_program("screen")
        self._screen_vao = self._make_vao(self._screen_program)

        self._upload_tex = self._ctx.texture(self._render_size, 4)
        self._upload_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._upload_tex.repeat_x = False
        self._upload_tex.repeat_y = False
        self._upload_tex.swizzle = "BGRA"

        self._scene_tex = self._ctx.texture(self._render_size, 4)
        self._scene_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._scene_tex.repeat_x = False
        self._scene_tex.repeat_y = False
        self._scene_fbo = self._ctx.framebuffer(color_attachments=[self._scene_tex])

        self._start_time = time.perf_counter()
        self._enabled = True
        self._glitch = 0.0
        self._glitch_decay = 0.85

        self._surface = pygame.Surface(
            self._render_size, 0, 32,
            (0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000),
        )

    def _build_quad(self):
        verts = array("f", [
            -1.0,  1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
        ])
        self._vbo = self._ctx.buffer(verts.tobytes())

    def _compile_program(self, name):
        with open(os.path.join(SHADER_DIR, "vertex.glsl"), "r", encoding="utf-8") as f:
            vert_src = f.read()
        with open(os.path.join(SHADER_DIR, f"{name}.glsl"), "r", encoding="utf-8") as f:
            frag_src = f.read()
        return self._ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)

    def _make_vao(self, program):
        return self._ctx.vertex_array(
            program, [(self._vbo, "2f 2f", "vert", "tex_coord")]
        )

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
        self._scene_program.release()
        self._scene_vao.release()
        self._scene_program = new_program
        self._scene_vao = self._make_vao(self._scene_program)
        self._shader_name = name

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)

    def toggle(self):
        self._enabled = not self._enabled
        return self._enabled

    def pulse_glitch(self, amount=1.0):
        self._glitch = max(self._glitch, float(amount))

    def scale_mouse_pos(self, pos):
        sw, sh = self._screen_size
        rw, rh = self._render_size
        if sw == rw and sh == rh:
            return (int(pos[0]), int(pos[1]))
        return (int(pos[0] * rw / sw), int(pos[1] * rh / sh))

    def present(self):
        self._upload_tex.write(self._surface.get_buffer())

        self._scene_fbo.use()
        self._ctx.viewport = (0, 0, self._render_size[0], self._render_size[1])
        self._upload_tex.use(0)
        self._set_uniform(self._scene_program, "u_texture", 0)
        self._set_uniform(self._scene_program, "u_time", time.perf_counter() - self._start_time)
        self._set_uniform(self._scene_program, "u_resolution", self._render_size)
        self._set_uniform(self._scene_program, "u_intensity", 1.0 if self._enabled else 0.0)
        self._set_uniform(self._scene_program, "u_glitch", self._glitch)
        self._scene_vao.render(mode=moderngl.TRIANGLE_STRIP)

        self._ctx.screen.use()
        self._ctx.viewport = (0, 0, self._screen_size[0], self._screen_size[1])
        self._scene_tex.use(0)
        self._set_uniform(self._screen_program, "u_texture", 0)
        self._set_uniform(self._screen_program, "u_time", time.perf_counter() - self._start_time)
        self._set_uniform(self._screen_program, "u_resolution", self._screen_size)
        self._screen_vao.render(mode=moderngl.TRIANGLE_STRIP)

        pygame.display.flip()

        self._glitch *= self._glitch_decay
        if self._glitch < 0.01:
            self._glitch = 0.0

    def shutdown(self):
        try:
            self._scene_fbo.release()
            self._scene_tex.release()
            self._upload_tex.release()
            self._scene_vao.release()
            self._screen_vao.release()
            self._scene_program.release()
            self._screen_program.release()
            self._vbo.release()
            self._ctx.release()
        except Exception:
            pass

    def _set_uniform(self, program, name, value):
        try:
            program[name].value = value
        except KeyError:
            pass


class _PassthroughPipeline:

    def __init__(self, size, fullscreen, display_size=None):
        self._render_size = (int(size[0]), int(size[1]))
        if display_size is None:
            self._display_size = self._render_size
        else:
            self._display_size = (int(display_size[0]), int(display_size[1]))
        flags = pygame.FULLSCREEN if fullscreen else 0
        self._display = pygame.display.set_mode(self._display_size, flags)
        self._display_size = self._display.get_size()
        self._surface = pygame.Surface(self._render_size).convert()
        self._needs_scale = self._render_size != self._display_size

    @property
    def surface(self):
        return self._surface

    def set_shader(self, _=None):
        pass

    def set_enabled(self, _=None):
        pass

    def toggle(self):
        return False

    def pulse_glitch(self, _=1.0):
        pass

    def scale_mouse_pos(self, pos):
        sw, sh = self._display_size
        rw, rh = self._render_size
        if sw == rw and sh == rh:
            return (int(pos[0]), int(pos[1]))
        return (int(pos[0] * rw / sw), int(pos[1] * rh / sh))

    def present(self):
        if self._needs_scale:
            pygame.transform.smoothscale(self._surface, self._display_size, self._display)
        else:
            self._display.blit(self._surface, (0, 0))
        pygame.display.flip()

    def shutdown(self):
        pass
