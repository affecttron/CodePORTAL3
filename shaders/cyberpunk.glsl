#version 330 core

// in-game post-FX: CA, scanlines, neon grade, vignette, FBM atmosphere, glitch

uniform sampler2D u_texture;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_intensity;   // 0 = off, 1 = full
uniform float u_glitch;      // 0..1, decays per frame

in vec2 v_uv;
out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

// value noise
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// fractional brownian motion — layered noise
float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p *= 2.3;
        a *= 0.5;
    }
    return v;
}

void main() {
    float fx = clamp(u_intensity, 0.0, 1.0);
    vec2  uv = v_uv;

    // tears on burst only
    float burst = u_glitch;
    if (burst > 0.01) {
        float band     = floor(uv.y * 110.0 + u_time * 0.5);
        float bandRand = hash21(vec2(band, 17.0));
        float tearGate = step(0.85, bandRand) * burst;
        uv.x += (bandRand - 0.5) * 0.03 * tearGate;
    }

    // subtle CA, slight at edges
    vec2  centered = uv - 0.5;
    float dist     = length(centered);
    float ca       = (0.0004 + 0.0012 * dist) * fx + burst * 0.003;

    float r = texture(u_texture, uv - vec2(ca, 0.0)).r;
    float g = texture(u_texture, uv).g;
    float b = texture(u_texture, uv + vec2(ca, 0.0)).b;
    vec3 col = vec3(r, g, b);

    // soft scanlines
    float scan = 0.5 + 0.5 * sin(v_uv.y * u_resolution.y * 1.0);
    col *= mix(1.0, 0.95 + 0.05 * scan, fx);

    // neon glow on bright pixels
    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    col += col * smoothstep(0.65, 1.0, lum) * 0.13 * fx;

    // magenta shadows / cyan highlights
    vec3 tintShadow = vec3(0.018, 0.000, 0.030);
    vec3 tintHi     = vec3(0.000, 0.015, 0.025);
    col += mix(tintShadow, tintHi, lum) * fx;

    // FBM atmospheric drift — slow cyan/magenta haze
    float drift = fbm(v_uv * vec2(6.0, 3.0) + vec2(u_time * 0.05, u_time * 0.08));
    col += mix(vec3(0.02, 0.00, 0.04), vec3(0.00, 0.03, 0.05), drift) * drift * fx * 0.30;

    // vignette
    float vig = smoothstep(1.15, 0.60, dist);
    col *= mix(1.0, vig, fx * 0.25);

    // grain
    float grain = (hash21(v_uv * u_resolution + u_time * 60.0) - 0.5) * 0.018 * fx;
    col += grain;

    // flash on burst
    col += burst * 0.06 * vec3(1.0, 0.2, 0.8) * fx;

    fragColor = vec4(col, 1.0);
}
