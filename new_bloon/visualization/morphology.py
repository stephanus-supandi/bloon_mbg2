"""Procedural morphology generator: phenotype -> morphology parameters.
Pure function dari phenotype vector. Tidak menerima genome, fitness,
generation, atau target.
"""


def morphology_from_phenotype(p):
    return {
        "torso_rx": 2.0 + 3.0 * p["torso_width"] + 1.5 * p["muscle_mass"],
        "torso_ry": 2.0 + 3.0 * p["body_size"],
        "head_rx": 1.2 + 1.6 * p["skull_ratio"],
        "head_ry": 1.0 + 1.4 * p["skull_ratio"],
        "jaw_rx": 0.6 + 1.8 * p["jaw_size"],
        "arm_ry": 1.5 + 4.0 * p["arm_length"],
        "arm_rx": 0.6 + 0.9 * p["muscle_mass"],
        "leg_ry": 0.8 + 2.6 * p["leg_length"],
        "leg_rx": 0.5 + 0.7 * p["muscle_mass"],
        "lean": (1.0 - p["posture"]) * 3.0,
    }