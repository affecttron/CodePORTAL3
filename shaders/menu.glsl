#version 330 core

// menu post-FX — atmospheric. The centerpiece is a domain-warped FBM "smoke"
// field drifting horizontally in the background. Technique inspired by
// LuckeyDuckey/Forbidden's GetWindPattern (iterated FBM, each layer warps
// the next). A luminance bg mask keeps the rendered UI clean.

uniform sampler2D u_texture;
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_intensity;
uniform float u_glitch;

in vec2 v_uv;
out vec4 fragColor;

// grim monochrome smoke palette
const vec3 SMOKE_DARK = vec3(0.030, 0.030, 0.034);  // near-black
const vec3 SMOKE_MID  = vec3(0.130, 0.130, 0.140);  // dark grey
const vec3 SMOKE_LIT  = vec3(0.340, 0.340, 0.360);  // cool grey wisp highlight

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float valueNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = smoothstep(0.0, 1.0, f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// 4-octave FBM
float fbm(vec2 p) {
    float total = 0.0;
    float maxV  = 0.0;
    float amp   = 0.5;
    float freq  = 1.0;
    for (int i = 0; i < 4; i++) {
        total += valueNoise(p * freq) * amp;
        maxV  += amp;
        amp   *= 0.5;
        freq  *= 2.0;
    }
    return total / maxV;
}

// iteratively domain-warped FBM — each layer perturbs the next.
// produces flowing, smoke-like fields rather than static noise.
float smokeField(vec2 p) {
    vec2 slow = vec2(u_time * 0.06, u_time * 0.018);
    vec2 fast = vec2(u_time * 0.11, 0.0);
    float n1 = fbm(p - fast);
    float n2 = fbm(p + 2.0 * vec2(n1));
    float n3 = fbm(p + vec2(n2));
    float n4 = fbm(p + slow + vec2(n3));
    return n4;
}

void main() {
    float fx = clamp(u_intensity, 0.0, 1.0);
    vec2  uv = v_uv;
    vec2  aspect = vec2(u_resolution.x / u_resolution.y, 1.0);

    // rare periodic glitch pulse (kept subtle)
    float pulseSeed = floor(u_time * 0.5);
    float pulse = step(0.94, hash21(vec2(pulseSeed, 11.0))) *
                  smoothstep(0.0, 0.05, fract(u_time * 0.5)) *
                  (1.0 - smoothstep(0.05, 0.18, fract(u_time * 0.5)));
    float burst = max(u_glitch, pulse);

    // slice tear only on burst
    if (burst > 0.01) {
        float slice     = floor(uv.y * 120.0);
        float sliceRand = hash21(vec2(slice, floor(u_time * 8.0)));
        float tearGate  = step(0.92, sliceRand) * burst;
        uv.x += (sliceRand - 0.5) * 0.035 * tearGate;
    }

    // radial chromatic aberration — R disperses outward from center, B inward
    vec2  centered = uv - 0.5;
    float dist     = length(centered);
    vec2  caDir    = dist > 0.001 ? normalize(centered) : vec2(1.0, 0.0);
    float caAmt    = (0.0007 + 0.003 * burst) * fx;
    float r = texture(u_texture, uv + caDir * caAmt).r;
    float g = texture(u_texture, uv).g;
    float b = texture(u_texture, uv - caDir * caAmt).b;
    vec3 col = vec3(r, g, b);

    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    // bg mask — 1 on dark background, 0 on rendered UI
    float bg  = 1.0 - smoothstep(0.10, 0.32, lum);

    // ── primary drifting smoke field ──
    vec2  sp    = (v_uv - 0.5) * aspect * 2.2;
    float smoke = smokeField(sp);
    float wisp  = smoothstep(0.32, 0.85, smoke);
    vec3  smCol = mix(SMOKE_DARK, SMOKE_MID, smoke);
    smCol       = mix(smCol, SMOKE_LIT, wisp * 0.65);
    col += smCol * fx * bg * 0.70;

    // ── secondary fine smoke drifting opposite (parallax depth) ──
    vec2  sp2    = (v_uv - 0.5) * aspect * 4.5 + vec2(-u_time * 0.012, u_time * 0.005);
    float smoke2 = fbm(sp2);
    col += vec3(0.05, 0.05, 0.055) * smoke2 * fx * bg * 0.55;

    // ── gentle CRT scanlines ──
    float scan = 0.97 + 0.03 * sin(v_uv.y * u_resolution.y * 1.0);
    col *= mix(1.0, scan, fx);

    // ── multi-tap bloom — 8-sample cross+diagonal for real spread on bright UI ──
    {
        vec2  texel = 1.0 / u_resolution;
        float br    = 3.0;
        float bd    = br * 0.7071;
        vec3  acc   = vec3(0.0);
        acc += texture(u_texture, uv + texel * vec2( br,  0.0)).rgb;
        acc += texture(u_texture, uv + texel * vec2(-br,  0.0)).rgb;
        acc += texture(u_texture, uv + texel * vec2( 0.0,  br)).rgb;
        acc += texture(u_texture, uv + texel * vec2( 0.0, -br)).rgb;
        acc += texture(u_texture, uv + texel * vec2( bd,  bd)).rgb;
        acc += texture(u_texture, uv + texel * vec2(-bd,  bd)).rgb;
        acc += texture(u_texture, uv + texel * vec2( bd, -bd)).rgb;
        acc += texture(u_texture, uv + texel * vec2(-bd, -bd)).rgb;
        acc /= 8.0;
        float bloomLum = dot(acc, vec3(0.299, 0.587, 0.114));
        col += acc * smoothstep(0.40, 0.88, bloomLum) * 0.45 * fx;
    }

    // desaturation pull — kills any residual color cast for the grim look
    {
        float gl = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(col, vec3(gl), 0.20 * fx);
    }

    // vignette (heavier — grim atmosphere needs darker edges)
    {
        vec2  c   = v_uv - 0.5;
        float vig = smoothstep(1.15, 0.45, length(c));
        col *= mix(1.0, vig, fx * 0.50);
    }

    // light grain
    col += (hash21(v_uv * u_resolution + u_time * 80.0) - 0.5) * 0.020 * fx;

    // mild burst flash (cool white)
    col += burst * 0.03 * vec3(0.95, 0.95, 1.00) * fx;

    fragColor = vec4(col, 1.0);
}
