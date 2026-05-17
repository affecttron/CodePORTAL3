#version 330 core

// menu post-FX: Voronoi neon rain, FBM drift, slice tears, scanlines, neon grade

uniform sampler2D u_texture;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_intensity;
uniform float u_glitch;

in vec2 v_uv;
out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

vec2 hash22(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

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

// 2D voronoi — returns distance to nearest cell point
float voronoi(vec2 p) {
    vec2 n = floor(p);
    vec2 f = fract(p);
    float d = 8.0;
    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            vec2 g = vec2(float(i), float(j));
            vec2 o = hash22(n + g);
            vec2 r = g + o - f;
            d = min(d, dot(r, r));
        }
    }
    return sqrt(d);
}

void main() {
    float fx = clamp(u_intensity, 0.0, 1.0);
    vec2 uv = v_uv;

    // rare periodic glitch pulse
    float pulseSeed = floor(u_time * 0.5);
    float pulse     = step(0.92, hash21(vec2(pulseSeed, 11.0))) *
                      smoothstep(0.0, 0.05, fract(u_time * 0.5)) *
                      (1.0 - smoothstep(0.05, 0.18, fract(u_time * 0.5)));
    float burst     = max(u_glitch, pulse);

    // slice tear on burst
    if (burst > 0.01) {
        float slice     = floor(uv.y * 120.0);
        float sliceRand = hash21(vec2(slice, floor(u_time * 8.0)));
        float tearGate  = step(0.90, sliceRand) * burst;
        uv.x += (sliceRand - 0.5) * 0.04 * tearGate;
    }

    // heat shimmer
    uv.x += sin(uv.y * 24.0 + u_time * 1.4) * 0.0009 * fx;

    // CA — subtle, boosted by burst
    float ca = (0.0007 + 0.004 * burst) * fx;
    float r = texture(u_texture, uv - vec2(ca, 0.0)).r;
    float g = texture(u_texture, uv).g;
    float b = texture(u_texture, uv + vec2(ca, 0.0)).b;
    vec3 col = vec3(r, g, b);

    // scanlines
    float scan = 0.94 + 0.06 * sin(v_uv.y * u_resolution.y * 1.2);
    col *= mix(1.0, scan, fx);

    // neon glow
    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    col += col * smoothstep(0.55, 0.95, lum) * 0.22 * fx;

    // magenta/cyan grade
    col.r += 0.012 * fx;
    col.b += 0.020 * fx;

    // Voronoi neon rain — drifting cells, cyan highlights at boundaries
    vec2 rainUV = vec2(v_uv.x * 32.0, v_uv.y * 50.0 - u_time * 1.8);
    float vor = voronoi(rainUV);
    float rain = smoothstep(0.40, 0.05, vor);
    col += vec3(0.10, 0.55, 0.90) * rain * 0.05 * fx;

    // FBM atmospheric drift
    float drift = fbm(v_uv * vec2(5.0, 3.0) + vec2(u_time * 0.04, u_time * 0.10));
    col += vec3(0.03, 0.01, 0.06) * drift * fx * 0.45;

    // vignette
    vec2 c = v_uv - 0.5;
    float vig = smoothstep(1.15, 0.45, length(c));
    col *= mix(1.0, vig, fx * 0.35);

    // grain
    col += (hash21(v_uv * u_resolution + u_time * 80.0) - 0.5) * 0.022 * fx;

    // flash on burst
    col += burst * 0.04 * vec3(1.0, 0.3, 0.9) * fx;

    fragColor = vec4(col, 1.0);
}
