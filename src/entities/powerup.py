"""src/entities/powerup.py

Collectible falling power-up capsules (Shield, Vulcan Spread, and +10Pt Bonus Crystal)
spawned upon enemy eliminations for AstraSeige.
"""

from enum import Enum
import random
import turtle
from typing import Optional, Tuple

from config import (
    BOTTOM_BOUNDARY,
    CRYSTAL_BONUS_POINTS,
    POWERUP_DROP_CHANCE,
    POWERUP_FALL_SPEED,
    RAPID_FIRE_DURATION_SEC,
    SHIELD_DURATION_SEC,
    SHIELD_PICKUP_CHARGES,
)
from src.ui.pixel_sprites import resolve_pixel_sprite


class PowerUpType(str, Enum):
    """Supported collectible power-up and bonus crystal types."""

    SHIELD = "SHIELD"
    VULCAN = "VULCAN"
    CRYSTAL = "CRYSTAL"
    RAPID_FIRE = "RAPID_FIRE"


SPAWNABLE_POWERUP_TYPES: Tuple[PowerUpType, ...] = (
    PowerUpType.SHIELD,
    PowerUpType.VULCAN,
    PowerUpType.CRYSTAL,
)


class PowerUp(turtle.Turtle):
    """Represents a collectible bonus item drifting down the playfield."""

    def __init__(
        self,
        x: float,
        y: float,
        powerup_type: Optional[PowerUpType] = None,
        fall_speed: float = POWERUP_FALL_SPEED,
    ) -> None:
        super().__init__(visible=False)
        self.penup()
        self.speed(0)

        self.powerup_type: PowerUpType = (
            powerup_type
            if powerup_type is not None
            else random.choice(SPAWNABLE_POWERUP_TYPES)
        )
        self.fall_speed: float = float(fall_speed)
        self.active: bool = True

        self.width: int = 26
        self.height: int = 26

        self.duration: float = 0.0
        self.bonus_points: int = 0
        self.shield_charges: int = 0
        self._uses_fallback_shape: bool = False

        if self.powerup_type == PowerUpType.SHIELD:
            self.duration = SHIELD_DURATION_SEC
            self.shield_charges = SHIELD_PICKUP_CHARGES
            chosen_shape = resolve_pixel_sprite("powerup_shield", "circle")
            self.shape(chosen_shape)
            self.color("#38BDF8")
            self._uses_fallback_shape = chosen_shape == "circle"
            if self._uses_fallback_shape:
                self.shapesize(stretch_wid=1.05, stretch_len=1.05)

        elif self.powerup_type == PowerUpType.CRYSTAL:
            self.bonus_points = CRYSTAL_BONUS_POINTS
            chosen_shape = resolve_pixel_sprite("powerup_crystal", "triangle")
            self.shape(chosen_shape)
            self.color("#C084FC")
            self._uses_fallback_shape = chosen_shape == "triangle"
            if self._uses_fallback_shape:
                self.shapesize(stretch_wid=1.05, stretch_len=1.05)

        else:
            self.duration = RAPID_FIRE_DURATION_SEC
            chosen_shape = resolve_pixel_sprite("powerup_vulcan", "square")
            self.shape(chosen_shape)
            self.color("#FACC15")
            self._uses_fallback_shape = chosen_shape == "square"
            if self._uses_fallback_shape:
                self.setheading(45)
                self.shapesize(stretch_wid=0.95, stretch_len=0.95)

        self.goto(x, y)
        self.showturtle()

    @classmethod
    def maybe_spawn(
        cls,
        x: float,
        y: float,
        drop_chance: float = POWERUP_DROP_CHANCE,
    ) -> Optional["PowerUp"]:
        if random.random() < drop_chance:
            chosen_type = random.choices(
                population=list(SPAWNABLE_POWERUP_TYPES),
                weights=[0.35, 0.30, 0.35],
                k=1,
            )[0]
            return cls(x=x, y=y, powerup_type=chosen_type)
        return None

    def update(self, dt: float = 1.0) -> None:
        """Moves the pickup downward scaled by `dt` and deactivates off-screen items."""
        if not self.active:
            return

        new_y = self.ycor() - (self.fall_speed * dt)
        self.sety(new_y)

        if self._uses_fallback_shape:
            self.setheading((self.heading() + (4.0 * dt)) % 360)

        if new_y < (BOTTOM_BOUNDARY - 20):
            self.deactivate()

    def deactivate(self) -> None:
        if not self.active:
            return
        self.active = False
        self.hideturtle()
        self.goto(0, 1100)