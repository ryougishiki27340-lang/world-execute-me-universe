"""Facts: every formula, constant, universe stage and code snippet in ONE place.

All numbers here are verified textbook values; each entry carries its source.
The film reads only from this module - no numbers are typed into scene code.
Verified: 2026-10-11. Sources: standard references (CODATA 2022, standard texts).
"""

# --- constants ----------------------------------------------------------
C = 299792458.0                  # m/s, speed of light (CODATA 2022)
HBAR = 1.054571817e-34           # J·s, reduced Planck constant (CODATA 2022)
G = 6.67430e-11                  # m^3 kg^-1 s^-2, Newton constant (CODATA 2022)
KB = 1.380649e-23                # J/K, Boltzmann (CODATA 2022)

# --- geometry (S03) ------------------------------------------------------
UNIT_CIRCLE = "x = cos t, y = sin t, t in [0, 2π)"
SINE = "y = sin x"
TANGENT_LINE = "y - sin a = cos a (x - a)"   # tangent to y=sin x at x=a
# 4D hypercube rotation (4x4 double rotation in xw/yz planes)
HYPERCUBE_ROT = ((1, 2), (3, 4))             # plane indices for the double rotation

# --- electromagnetism (S04) ---------------------------------------------
AC_WAVE = "V(t) = V0 sin(2π f t)"            # alternating current
DC_WAVE = "V(t) = V0"                        # direct current

# --- simulation (S05) ----------------------------------------------------
LORENZ = dict(sigma=10.0, rho=28.0, beta=8.0 / 3.0,
              eq="dx/dt=σ(y-x), dy/dt=x(ρ-z)-y, dz/dt=xy-βz")   # Lorenz 1963
DOUBLE_PENDULUM = dict(g=9.80665, l1=1.0, l2=1.0, m1=1.0, m2=1.0,
                        eq="Lagrangian double pendulum, Euler integration")

# --- resonance (S08): Fourier epicycles ----------------------------------
# Coefficients of the square wave (odd harmonics only): 4/π * (1/n) for odd n
SQUARE_WAVE_TERMS = 8

# --- collapse (S11) ------------------------------------------------------
FREE_PARTICLE_GAUSSIAN = "ψ(x,t)=∫ dk A(k) exp(i(kx - ħk²t/2m)), A(k)=exp(-k² σ²/2)"
MANDELBROT = "z_{n+1} = z_n^2 + c, z_0 = 0"
JULIA = "z_{n+1} = z_n^2 + c, fixed c"

# --- love algebra (S14) --------------------------------------------------
LOVE_EXPANSION = "(you + me)² = you² + 2·you·me + me²"
HEART_IMPLICIT = "(x² + y² − 1)³ − x² y³ = 0"   # algebraic heart curve

# --- universe history (S12), in ORDER ------------------------------------
# each stage: (name, marker temperature or energy scale, one-line fact)
UNIVERSE_STAGES = [
    ("big_bang",          "t = 0",            "singularity; the clock starts"),
    ("inflation",         "E ~ 10^16 GeV",    "exponential expansion, 10^-32 s"),
    ("quark_gluon",       "T > 10^12 K",      "quark-gluon plasma"),
    ("nucleosynthesis",   "T ~ 10^9 K",       "first nuclei: H, He, Li"),
    ("recombination",     "T ~ 3000 K",       "atoms form; photons decouple"),
    ("first_light",       "t ~ 380 kyr",      "CMB released (2.7255 K today)"),
    ("stars",             "t ~ 100 Myr",      "first stars ignite"),
    ("supernova",         "Fe core collapse", "heavy elements forged"),
    ("neutron_star",      "ρ ~ 10^17 kg/m³",  "degenerate neutron matter"),
    ("black_hole",        "R = 2GM/c²",       "event horizon"),
    ("dark_energy",       "ρ ~ constant",     "accelerating expansion"),
    ("heat_death",        "t → ∞",            "maximum entropy, silence"),
]

# --- original multilingual code snippets (used by components/code.py) -----
# Snippets are original; syntax-highlighted by the renderer, never executed.
CODE_SNIPPETS = {
    "python":   ["def love(me, you):", "    return solve(me, you)"],
    "c":        ["int main(void) {", "    return love(&you, &me);", "}"],
    "glsl":     ["vec4 love(vec2 uv) {", "    return vec4(heart(uv), 1.0);", "}"],
    "rust":     ["fn love(me: &Self, you: &Other) -> World {", "    World::execute(me, you)", "}"],
    "asm":      ["mov rax, you", "call execute", "ret"],
    "sql":      ["SELECT * FROM world", "WHERE you = 'online';"],
    "haskell":  ["love :: Me -> You -> World", "love me you = execute me you"],
}

# --- the love loop (S12) --------------------------------------------------
LOVE_LOOP = [
    "while (you.presence != \"online\") {",
    "    love = solve(me, you);",
    "    send(love, you);",
    "    wait(you.reply);",
    "    run++;",
    "}",
    "say(love);",            # unreachable
]
LOVE_LOOP_ERRS = {
    1: "ERR_UNRESOLVED_LOVE",
    2: "ERR_WINDOW_EDGE",
    3: "ERR_REPLY_OVERDUE",
}
LOVE_OVERFLOW = "ERR_LOVE_OVERFLOW"
