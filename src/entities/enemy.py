"""src/entities/enemy.py

Base Enemy parent class encapsulating common invader attributes, movement,
damage handling, firing, and lifecycle cleanup for AstraSeige.
"""

import turtle
from typing import List, Optional, Sequence

from src.entities.bullet import Bullet


class Enemy(turtle.Turtle):
    """Base class for all alien invaders, saucers, and bosses."""

    def __init__(
        self,
        x: float,
        y: float,
        health: int = 1,
        points: int = 10,
        base_speed: float = 2.0,
        color: str = "#4ADE80",
        shape_name: str = "square",
        stretch_wid: float = 1.1,
        stretch_len: float = 1.5,
        width: int = 32,
        height: int = 22,
        fire_weight: float = 1.0,
        damage_colors: Optional[Sequence[str]] = None,
        row: int = 0,
        col: int = 0,
    ) -> None:
        super().__init__(visible=False)
        self.penup()
        self.speed(0)
        self.shape(shape_name)
        self.shapesize(stretch_wid=stretch_wid, stretch_len=stretch_len)
        self.color(color)

        # Formation grid coordinates
        self.row: int = row
        self.col: int = col

        # Combat & scoring attributes
        self.max_health: int = max(1, int(health))
        self.health: int = self.max_health
        self.points: int = max(0, int(points))
        self.base_speed: float = float(base_speed)
        self.fire_weight: float = float(fire_weight)
        self.alive: bool = True
        self.hit_flash_frames: int = 0

        # Hitbox dimensions (in pixels) used by CollisionManager
        self.width: int = width
        self.height: int = height

        # Optional color gradient indexed by remaining HP (1 HP -> index 0, etc.)
        self.damage_colors: List[str] = list(damage_colors) if damage_colors else []

        self.goto(x, y)
        self.showturtle()

    # ------------------------------------------------------------------
    # Movement & Combat Behaviour
    # ------------------------------------------------------------------
    def move_by(self, dx: float, dy: float = 0.0) -> None:
        """Translates the invader by (dx, dy) during coordinated formation marches."""
        if not self.alive:
            return
        self.goto(self.xcor() + dx, self.ycor() + dy)

    def update(self) -> None:
        """Per-frame hook overridden by independent-movement enemies (UFO, Mothership)."""
        if self.hit_flash_frames > 0:
            self.hit_flash_frames -= 1

    def take_damage(self, damage: int = 1) -> bool:
        """Applies damage to the invader. Returns True if destroyed, False if still alive."""
        if not self.alive:
            return False

        self.health -= max(1, int(damage))
        if self.health <= 0:
            self.destroy()
            return True

        self.hit_flash_frames = 4
        self.on_damaged()
        return False

    def on_damaged(self) -> None:
        """Updates visual appearance when a multi-HP invader survives a hit."""
        if self.damage_colors and self.health > 0:
            color_index = min(self.health - 1, len(self.damage_colors) - 1)
            self.color(self.damage_colors[color_index])

    def shoot(self, bullet_speed: Optional[float] = None) -> Optional[Bullet]:
        """Spawns a downward enemy projectile beneath this invader."""
        if not self.alive:
            return None

        muzzle_y = self.ycor() - (self.height * 0.65)
        return Bullet(
            x=self.xcor(),
            y=muzzle_y,
            owner="enemy",
            speed=bullet_speed,
        )

    def destroy(self) -> None:
        """Marks the invader destroyed, hides its sprite, and moves it off-screen."""
        if not self.alive:
            return
        self.alive = False
        self.hideturtle()
        self.goto(0, 1200)