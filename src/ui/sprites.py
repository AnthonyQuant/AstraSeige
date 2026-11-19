"""src/ui/sprites.py

Custom vector polygon sprite definitions and Turtle shape registration for
Space Invaders: Galactic Assault.
"""

import turtle
from typing import Dict, Optional, Tuple

Polygon = Tuple[Tuple[float, float], ...]

# Note: Player uses setheading(90), which rotates shape (x, y) by 90 deg CCW
# into screen (-y, x). Defining the nose along +x orients the ship upright.
PLAYER_SHIP_SHAPE: Polygon = (
    (15.0, 0.0),    # Nose tip
    (6.0, 4.0),     # Upper fuselage left
    (3.0, 10.0),    # Inner wing left
    (6.0, 12.0),    # Wingtip cannon left
    (-6.0, 18.0),   # Outer wingtip left
    (-13.0, 16.0),  # Rear wing left
    (-10.0, 6.0),   # Thruster housing left
    (-14.0, 3.0),   # Engine nozzle left
    (-11.0, 0.0),   # Center tail notch
    (-14.0, -3.0),  # Engine nozzle right
    (-10.0, -6.0),  # Thruster housing right
    (-13.0, -16.0), # Rear wing right
    (-6.0, -18.0),  # Outer wingtip right
    (6.0, -12.0),   # Wingtip cannon right
    (3.0, -10.0),   # Inner wing right
    (6.0, -4.0),    # Upper fuselage right
)

# Invader shapes use default heading 0, where (x, y) maps 1:1 to screen (x, y).
SCOUT_INVADER_SHAPE: Polygon = (
    (-6.0, 11.0),
    (6.0, 11.0),
    (11.0, 6.0),
    (15.0, 1.0),
    (15.0, -5.0),
    (10.0, -5.0),
    (10.0, -11.0),
    (5.0, -11.0),
    (5.0, -6.0),
    (-5.0, -6.0),
    (-5.0, -11.0),
    (-10.0, -11.0),
    (-10.0, -5.0),
    (-15.0, -5.0),
    (-15.0, 1.0),
    (-11.0, 6.0),
)

ARMOURED_INVADER_SHAPE: Polygon = (
    (-9.0, 12.0),
    (9.0, 12.0),
    (15.0, 7.0),
    (17.0, 0.0),
    (14.0, -7.0),
    (9.0, -12.0),
    (4.0, -12.0),
    (4.0, -7.0),
    (-4.0, -7.0),
    (-4.0, -12.0),
    (-9.0, -12.0),
    (-14.0, -7.0),
    (-17.0, 0.0),
    (-15.0, 7.0),
)

ELITE_INVADER_SHAPE: Polygon = (
    (0.0, 13.0),
    (7.0, 9.0),
    (18.0, 11.0),
    (16.0, 2.0),
    (11.0, -4.0),
    (14.0, -12.0),
    (6.0, -9.0),
    (0.0, -13.0),
    (-6.0, -9.0),
    (-14.0, -12.0),
    (-11.0, -4.0),
    (-16.0, 2.0),
    (-18.0, 11.0),
    (-7.0, 9.0),
)

BONUS_UFO_SHAPE: Polygon = (
    (-7.0, 10.0),
    (7.0, 10.0),
    (11.0, 5.0),
    (21.0, 1.0),
    (17.0, -5.0),
    (9.0, -9.0),
    (-9.0, -9.0),
    (-17.0, -5.0),
    (-21.0, 1.0),
    (-11.0, 5.0),
)

CUSTOM_SHAPES: Dict[str, Polygon] = {
    "player_ship": PLAYER_SHIP_SHAPE,
    "scout_invader": SCOUT_INVADER_SHAPE,
    "armoured_invader": ARMOURED_INVADER_SHAPE,
    "elite_invader": ELITE_INVADER_SHAPE,
    "bonus_ufo": BONUS_UFO_SHAPE,
}


def register_all_shapes(screen: Optional[turtle._Screen] = None) -> None:
    """Registers all custom polygon sprites onto the active Turtle screen."""
    target_screen = screen if screen is not None else turtle.Screen()
    existing = set(target_screen.getshapes())

    for shape_name, vertices in CUSTOM_SHAPES.items():
        if shape_name not in existing:
            target_screen.register_shape(shape_name, vertices)


def resolve_shape(
    preferred_shape: str,
    fallback_shape: str,
    screen: Optional[turtle._Screen] = None,
) -> str:
    """Returns `preferred_shape` if registered on the Turtle screen, else `fallback_shape`."""
    try:
        target_screen = screen if screen is not None else turtle.Screen()
        if preferred_shape in target_screen.getshapes():
            return preferred_shape
    except Exception:
        pass
    return fallback_shape