"""Shared settings for KlærSøm: sample sizes, input limits and drafting constants.

All lengths are in centimetres. Sample sizes are illustrative, not a sizing standard.
"""

PRESETS = {
    "small":  {"bust": 84,  "waist": 68, "hip": 90,  "front_length": 38, "shoulder_width": 36, "dress_length": 90,  "upper_arm": 27},
    "medium": {"bust": 92,  "waist": 76, "hip": 98,  "front_length": 40, "shoulder_width": 38, "dress_length": 100, "upper_arm": 29.5},
    "large":  {"bust": 104, "waist": 88, "hip": 110, "front_length": 43, "shoulder_width": 41, "dress_length": 110, "upper_arm": 33},
}

# (minimum, maximum) accepted for every numeric input.
RANGES = {
    "bust": (50, 180), "waist": (40, 170), "hip": (50, 190),
    "front_length": (20, 80), "shoulder_width": (20, 70), "dress_length": (35, 180),
    "upper_arm": (15, 60), "seam_allowance": (0, 5),
    "skirt_fullness": (1.0, 2.5), "puff_fullness": (1.0, 2.0),
}

NECKLINES = {"square": "Wide square neckline", "shallow": "Shallow round neckline"}
SKIRTS = {"gathered_a_line": "Full gathered A-line (approx.)", "straight": "Straight"}

DEFAULT_OPTIONS = {
    "seam_allowance": 1.5, "neckline": "square", "skirt_style": "gathered_a_line",
    "skirt_fullness": 1.8, "puff_fullness": 1.5,
}

HEM_ALLOWANCE = 3.0   # skirt hem turn-up; never less than the seam allowance
