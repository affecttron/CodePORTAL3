#version 330 core

// fullscreen quad in clip space

in vec2 vert;
in vec2 tex_coord;

out vec2 v_uv;

void main() {
    v_uv = tex_coord;
    gl_Position = vec4(vert, 0.0, 1.0);
}
