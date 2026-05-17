#version 330 core

// menu post-FX: glitch pulse, slice tears, shimmer, scanlines, neon grade

uniform sampler2D u_texture;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_intensity;
uniform float u_glitch;

in vec2 v_uv;
out vec4 fragColor;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    float fx = clamp(u_intensity, 0.0, 1.0);
    vec2 uv = v_uv;

    // rare periodic glitch pulse
    float pulseSeed = floor(u_time * 0.5);
    float pulse     = step(0.92, hash(vec2(pulseSeed, 11.0))) *
                      smoothstep(0.0, 0.05, fract(u_time * 0.5)) *
                      (1.0 - smoothstep(0.05, 0.18, fract(u_time * 0.5)));
    float burst     = max(u_glitch, pulse);

    // slice tear on burst
    if (burst > 0.01) {
        float slice     = floor(uv.y * 120.0);
        float sliceRand = hash(vec2(slice, floor(u_time * 8.0)));
        float tearGate  = step(0.90, sliceRand) * burst;
        uv.x += (sliceRand - 0.5) * 0.04 * tearGate;
    }

    // heat shimmer
    uv.x += sin(uv.y * 24.0 + u_time * 1.4) * 0.0009 * fx;

    // CA — subtle, boosted by burst
    float ca = (0.0010 + 0.006 * burst) * fx;
    float r = texture(u_texture, uv - vec2(ca, 0.0)).r;
    float g = texture(u_texture, uv).g;
    float b = texture(u_texture, uv + vec2(ca, 0.0)).b;
    vec3 col = vec3(r, g, b);

    // scanlines
    float scan = 0.92 + 0.08 * sin(v_uv.y * u_resolution.y * 1.2);
    col *= mix(1.0, scan, fx);

    // neon glow
    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    col += col * smoothstep(0.55, 0.95, lum) * 0.30 * fx;

    // magenta/cyan grade
    col.r += 0.015 * fx;
    col.b += 0.025 * fx;

    // vignette
    vec2 c = v_uv - 0.5;
    float vig = smoothstep(1.10, 0.40, length(c));
    col *= mix(1.0, vig, fx * 0.45);

    // grain
    col += (hash(v_uv * u_resolution + u_time * 80.0) - 0.5) * 0.03 * fx;

    // flash on burst
    col += burst * 0.05 * vec3(1.0, 0.3, 0.9) * fx;

    fragColor = vec4(col, 1.0);
}
