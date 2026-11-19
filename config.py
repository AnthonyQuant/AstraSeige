"""config.py

Centralized configuration, screen geometry, entity metrics, power-up tiers,
and difficulty presets for AstraSeige.
"""

from pathlib import Path

# Project Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HIGH_SCORES_FILE = DATA_DIR / "high_scores.json"
GAME_HISTORY_FILE = DATA_DIR / "game_history.csv"
DATABASE_FILE = DATA_DIR / "astraseige.db"

# Screen & Loop Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 650
WINDOW_TITLE = "ASTRASEIGE"
BACKGROUND_COLOR = "#070913"
TARGET_FPS = 60.0
FRAME_DELAY_MS = 16  # ~60 FPS target frame budget
MAX_DELTA_SEC = 0.10  # Caps dt spike at 6x step so bullets never tunnel through enemies

# Playfield Boundaries
LEFT_BOUNDARY = -360
RIGHT_BOUNDARY = 360
TOP_BOUNDARY = 270
BOTTOM_BOUNDARY = -280
PLAYER_START_Y = -255
DEFENSE_LINE_Y = -225

# Player & Stackable Shield Settings
PLAYER_SPEED = 8.0
PLAYER_COOLDOWN_SEC = 0.36
RAPID_FIRE_COOLDOWN_SEC = 0.22
MAX_ACTIVE_PLAYER_BULLETS = 15  # Supports up to 3 simultaneous 5-way Vulcan volleys
INVULNERABILITY_SEC = 1.5
STARTING_SHIELD_CHARGES = 1
SHIELD_PICKUP_CHARGES = 1
MAX_SHIELD_CHARGES = 5

# Vulcan Fanning Spread-Shot Tiers
VULCAN_MAX_LEVEL = 3
VULCAN_SPREAD_ANGLES = {
    1: (0.0,),
    2: (-10.0, 0.0, 10.0),
    3: (-18.0, -9.0, 0.0, 9.0, 18.0),
}

# Projectile Settings
PLAYER_BULLET_SPEED = 14.0
ENEMY_BULLET_SPEED = 6.5

# Wave & Formation Settings
MAX_WAVES = 10
FORMATION_COLS = 8
FORMATION_START_Y = 210
FORMATION_X_SPACING = 66
FORMATION_Y_SPACING = 42
FORMATION_DROP_DISTANCE = 18
WAVE_CLEAR_BONUS_BASE = 100
WAVE_TRANSITION_DELAY_SEC = 1.4

# Power-Up & Crystal Settings
POWERUP_FALL_SPEED = 3.2
POWERUP_DROP_CHANCE = 0.28
SHIELD_DURATION_SEC = 7.0
RAPID_FIRE_DURATION_SEC = 6.0
CRYSTAL_BONUS_POINTS = 10

# Bonus UFO & Mothership Boss Settings
UFO_SPEED = 4.2
UFO_SPAWN_CHANCE_PER_TICK = 0.0022
UFO_POINTS_OPTIONS = (100, 150, 200, 250)

MOTHERSHIP_BASE_HP = 24
MOTHERSHIP_POINTS = 500
MOTHERSHIP_SPEED = 2.0
MOTHERSHIP_BEAM_COOLDOWN_SEC = 4.2
MOTHERSHIP_BEAM_DURATION_SEC = 1.35
MOTHERSHIP_BEAM_LENGTH = 360.0

# Difficulty Presets
DIFFICULTY_SETTINGS = {
    "Easy": {
        "starting_lives": 4,
        "enemy_speed_mult": 0.80,
        "enemy_fire_prob": 0.008,
        "wave_speed_step": 0.10,
        "max_enemy_bullets": 4,
    },
    "Normal": {
        "starting_lives": 3,
        "enemy_speed_mult": 1.00,
        "enemy_fire_prob": 0.014,
        "wave_speed_step": 0.14,
        "max_enemy_bullets": 6,
    },
    "Hard": {
        "starting_lives": 2,
        "enemy_speed_mult": 1.25,
        "enemy_fire_prob": 0.022,
        "wave_speed_step": 0.18,
        "max_enemy_bullets": 8,
    },
}

DEFAULT_DIFFICULTY = "Normal"
DEFAULT_PLAYER_NAME = "Pilot"