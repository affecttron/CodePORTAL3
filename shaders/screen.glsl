#version 330 core

// final present pass — samples scene framebuffer onto the default fbo

uniform sampler2D u_texture;
uniform vec2 u_resolution;

in vec2 v_uv;
out vec4 fragColor;

void main() {
    // flip V — fbo is right-side-up; quad UVs assume upload-flipped layout
    vec2 uv    = vec2(v_uv.x, 1.0 - v_uv.y);
    vec2 texel = 1.0 / u_resolution;

    vec3 center = texture(u_texture, uv).rgb;

    // 3×3 neighbourhood blur for unsharp mask — lifts detail lost in upscaling
    vec3 blur = vec3(0.0);
    blur += texture(u_texture, uv + texel * vec2(-1.0, -1.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2( 0.0, -1.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2( 1.0, -1.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2(-1.0,  0.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2( 1.0,  0.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2(-1.0,  1.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2( 0.0,  1.0)).rgb;
    blur += texture(u_texture, uv + texel * vec2( 1.0,  1.0)).rgb;
    blur /= 8.0;

    vec3 sharpened = center + (center - blur) * 0.35;

    fragColor = vec4(clamp(sharpened, 0.0, 1.0), 1.0);
}
