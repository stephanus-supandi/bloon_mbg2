"""Trait definitions and the benchmark gorilla target (reference only)."""

TRAIT_NAMES = [
    "body_size", "torso_width", "arm_length", "forearm_ratio", "leg_length",
    "shoulder_width", "muscle_mass", "jaw_size", "skull_ratio", "posture",
    "fur_density",
]

# Benchmark objective (spec §15). The renderer NEVER consults this vector.
GORILLA_TARGET = {
    "body_size": 0.95, "torso_width": 0.90, "arm_length": 0.85,
    "forearm_ratio": 0.55, "leg_length": 0.35, "shoulder_width": 0.95,
    "muscle_mass": 0.92, "jaw_size": 0.80, "skull_ratio": 0.45,
    "posture": 0.35, "fur_density": 0.70,
}

def clamp01(x):
    return max(0.0, min(1.0, float(x)))