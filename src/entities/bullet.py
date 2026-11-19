"""src/entities/bullet.py

Projectile entity representing upward player lasers, angled Vulcan spread bolts,
and downward enemy plasma bolts for AstraSeige.
"""

import math
import turtle
from typing import Optional

from config import (
    BOTTOM_BOUNDARY,
    ENEMY_BULLET_SPEED,
    LEFT_BOUNDARY,
    PLAYER_BULLET_SPEED,
    RIGHT_BOUNDARY,
    TOP_BOUNDARY,
)


class Bullet(turtle.Turtle):
    """Represents a single active projectile fired by the player or an alien vessel."""

    def __init__(
        self,
        x: float,
        y: float,
        owner: str = "player",
        speed: Optional[float] = None,
        angle_deg: float = 0.0,
        is_vulcan: bool = False,
    ) -> None:
        super().__init__(visible=False)
        self.penup()
        self.speed(0)

        self.owner: str = owner.lower()
        self.active: bool = True
        self.angle_deg: float = float(angle_deg)
        self.is_vulcan: bool = bool(is_vulcan)

        self.width: int = 8 if self.is_vulcan else 6
        self.height: int = 16

        if self.owner == "player":
            self.direction: int = 1
            self.move_speed: float = (
                speed if speed is not None else PLAYER_BULLET_SPEED
            )
            self.shape("triangle" if not self.is_vulcan else "square")
            self.setheading(90 - self.angle_deg)
            if self.is_vulcan:
                self.color("#FBBF24")
                self.shapesize(stretch_wid=0.35, stretch_len=0.85)
            else:
                self.color("#38BDF8")
                self.shapesize(stretch_wid=0.45, stretch_len=0.65)
        else:
            self.direction = -1
            self.move_speed = (
                speed if speed is not None else ENEMY_BULLET_SPEED
            )
            self.shape("square")
            self.setheading(270 + self.angle_deg)
            self.color("#FB7185")
            self.shapesize(stretch_wid=0.30, stretch_len=0.75)

        rad = math.radians(self.angle_deg)
        self.vx: float = math.sin(rad) * self.move_speed
        self.vy: float = math.cos(rad) * self.move_speed * self.direction

        self.goto(x, y)
        self.showturtle()

    @property
    def is_player_bullet(self) -> bool:
        return self.owner == "player"

    def update(self, dt: float = 1.0) -> None:
        """Advances the projectile along its trajectory scaled by `dt`."""
        if not self.active:
            return

        new_x = self.xcor() + (self.vx * dt)
        new_y = self.ycor() + (self.vy * dt)
        self.goto(new_x, new_y)

        if new_x < (LEFT_BOUNDARY - 30) or new_x > (RIGHT_BOUNDARY + 30):
            self.deactivate()
        elif self.direction > 0 and new_y > (TOP_BOUNDARY + 20):
            self.deactivate()
        elif self.direction < 0 and new_y < (BOTTOM_BOUNDARY - 20):
            self.deactivate()

    def deactivate(self) -> None:
        if not self.active:
            return
        self.active = False
        self.hideturtle()
        self.goto(0, 1000)