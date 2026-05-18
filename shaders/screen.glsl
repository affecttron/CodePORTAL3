#version 330 core

// final present pass — samples scene framebuffer onto the default fbo

uniform sampler2D u_texture;

in vec2 v_uv;
out vec4 fragColor;

void main() {
    // flip V — fbo is right-side-up; quad UVs assume upload-flipped layout
    fragColor = texture(u_texture, vec2(v_uv.x, 1.0 - v_uv.y));
}
