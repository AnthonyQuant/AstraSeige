"""src/entities/enemy_types.py

Specialized pixel-art invader subclasses for AstraSeige:
- BasicInvader (Neon Green Antenna Invader)
- ClusterInvader (5-Color Pyramid Cluster Crabs)
- ArmouredInvader (Red-Domed Green Saucer)
- EliteInvader (Purple Horned Commander)
- BonusUFO (High-speed top-lane mystery saucer)
- MothershipBoss (Central Dreadnought UFO with blazing plasma beam)
"""

import math
import random
import time
from typing import Dict, Optional, Tuple

from config import (
    LEFT_BOUNDARY,
    MOTHERSHIP_BASE_HP,
    MOTHERSHIP_BEAM_COOLDOWN_SEC,
    MOTHERSHIP_BEAM_DURATION_SEC,
    MOTHERSHIP_BEAM_LENGTH,
    MOTHERSHIP_POINTS,
    MOTHERSHIP_SPEED,
    RIGHT_BOUNDARY,
    TOP_BOUNDARY,
    UFO_POINTS_OPTIONS,
    UFO_SPEED,
)
from src.entities.bullet import Bullet
from src.entities.enemy import Enemy
from src.ui.pixel_sprites import resolve_pixel_sprite


CLUSTER_TIERS: Dict[str, Tuple[str, str, int, int]] = {
    "red": ("crab_red", "#F43F5E", 2, 35),
    "orange": ("crab_orange", "#FB923C", 2, 30),
    "cyan": ("crab_cyan", "#38BDF8", 1, 25),
    "pink": ("crab_pink", "#EC4899", 1, 20),
    "yellow": ("crab_yellow", "#FACC15", 1, 15),
}


class BasicInvader(Enemy):
    """Neon green antenna invader: 1 HP, 10 points."""

    def __init__(self, x: float, y: float, row: int = 0, col: int = 0) -> None:
        sprite = resolve_pixel_sprite("green_invader", "square")
        stretch_wid, stretch_len = (1.0, 1.0) if sprite == "green_invader" else (1.05, 1.45)

        super().__init__(
            x=x,
            y=y,
            health=1,
            points=10,
            base_speed=2.0,
            color="#22C55E",
            shape_name=sprite,
            stretch_wid=stretch_wid,
            stretch_len=stretch_len,
            width=32,
            height=26,
            fire_weight=1.0,
            row=row,
            col=col,
        )


class ClusterInvader(Enemy):
    """Color-coded pixel crab used in the inverted-V cluster formations."""

    def __init__(
        self,
        x: float,
        y: float,
        tier: str = "cyan",
        row: int = 0,
        col: int = 0,
    ) -> None:
        shape_key, hex_color, hp, pts = CLUSTER_TIERS.get(
            tier.lower(),
            CLUSTER_TIERS["cyan"],
        )
        sprite = resolve_pixel_sprite(shape_key, "square")
        stretch_wid, stretch_len = (1.0, 1.0) if sprite == shape_key else (1.05, 1.40)

        super().__init__(
            x=x,
            y=y,
            health=hp,
            points=pts,
            base_speed=2.05,
            color=hex_color,
            shape_name=sprite,
            stretch_wid=stretch_wid,
            stretch_len=stretch_len,
            width=30,
            height=22,
            fire_weight=1.1,
            row=row,
            col=col,
        )
        self.tier: str = tier.lower()


class ArmouredInvader(Enemy):
    """Red-domed green saucer craft: 3 HP, 30 points."""

    def __init__(self, x: float, y: float, row: int = 0, col: int = 0) -> None:
        sprite = resolve_pixel_sprite("saucer_enemy", "square")
        stretch_wid, stretch_len = (
            (1.0, 1.0) if sprite == "saucer_enemy" else (1.2, 1.65)
        )

        super().__init__(
            x=x,
            y=y,
            health=3,
            points=30,
            base_speed=1.9,
            color="#22C55E",
            shape_name=sprite,
            stretch_wid=stretch_wid,
            stretch_len=stretch_len,
            width=36,
            height=22,
            fire_weight=1.35,
            damage_colors=("#FACC15", "#FB923C", "#22C55E"),
            row=row,
            col=col,
        )


class EliteInvader(Enemy):
    """Purple horned alien commander: 4 HP, aggressive fire, 60 points."""

    def __init__(self, x: float, y: float, row: int = 0, col: int = 0) -> None:
        sprite = resolve_pixel_sprite("purple_invader", "square")
        stretch_wid, stretch_len = (1.0, 1.0) if sprite == "purple_invader" else (1.25, 1.75)

        super().__init__(
            x=x,
            y=y,
            health=4,
            points=60,
            base_speed=2.2,
            color="#9333EA",
            shape_name=sprite,
            stretch_wid=stretch_wid,
            stretch_len=stretch_len,
            width=36,
            height=30,
            fire_weight=1.85,
            damage_colors=("#F472B6", "#E879F9", "#C084FC", "#9333EA"),
            row=row,
            col=col,
        )


class BonusUFO(Enemy):
    """High-speed mystery saucer sweeping across the top lane for randomized bonus points."""

    def __init__(
        self,
        direction: Optional[int] = None,
        y: Optional[float] = None,
    ) -> None:
        self.direction: int = (
            direction if direction in (-1, 1) else random.choice((-1, 1))
        )
        spawn_x = (
            LEFT_BOUNDARY - 50 if self.direction == 1 else RIGHT_BOUNDARY + 50
        )
        spawn_y = y if y is not None else (TOP_BOUNDARY - 24)
        bonus_points = random.choice(UFO_POINTS_OPTIONS)

        sprite = resolve_pixel_sprite("saucer_enemy", "circle")
        stretch_wid, stretch_len = (1.0, 1.0) if sprite == "saucer_enemy" else (0.95, 2.1)

        super().__init__(
            x=spawn_x,
            y=spawn_y,
            health=1,
            points=bonus_points,
            base_speed=UFO_SPEED,
            color="#F43F5E",
            shape_name=sprite,
            stretch_wid=stretch_wid,
            stretch_len=stretch_len,
            width=40,
            height=22,
            fire_weight=0.0,
        )

    def update(self, dt: float = 1.0) -> None:
        """Moves the UFO horizontally across the upper screen scaled by `dt`."""
        if not self.alive:
            return

        new_x = self.xcor() + (self.direction * self.base_speed * dt)
        self.setx(new_x)

        if self.direction == 1 and new_x > (RIGHT_BOUNDARY + 60):
            self.destroy()
        elif self.direction == -1 and new_x < (LEFT_BOUNDARY - 60):
            self.destroy()

    def shoot(self, bullet_speed: Optional[float] = None) -> Optional[Bullet]:
        return None


class MothershipBoss(Enemy):
    """Dreadnought UFO Boss with sweeping motion and blazing plasma beam."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 115.0,
        wave_number: int = 5,
    ) -> None:
        sprite = resolve_pixel_sprite("mothership_boss", "circle")
        stretch_wid, stretch_len = (1.0, 1.0) if sprite == "mothership_boss" else (2.2, 4.5)
        scaled_hp = MOTHERSHIP_BASE_HP + max(0, wave_number - 5) * 6

        super().__init__(
            x=x,
            y=y,
            health=scaled_hp,
            points=MOTHERSHIP_POINTS,
            base_speed=MOTHERSHIP_SPEED,
            color="#F43F5E",
            shape_name=sprite,
            stretch_wid=stretch_wid,
            stretch_len=stretch_len,
            width=88,
            height=42,
            fire_weight=2.5,
        )
        self.direction: int = 1
        self._last_beam_time: float = time.monotonic() - 1.5
        self._beam_until: float = 0.0
        self.beam_angle_deg: float = 22.0
        self.beam_length: float = MOTHERSHIP_BEAM_LENGTH

    @property
    def beam_active(self) -> bool:
        return self.alive and time.monotonic() < self._beam_until

    @beam_active.setter
    def beam_active(self, active: bool) -> None:
        if active and self.alive:
            now = time.monotonic()
            self._last_beam_time = now
            self._beam_until = now + MOTHERSHIP_BEAM_DURATION_SEC
        else:
            self._beam_until = 0.0

    @property
    def beam_start(self) -> Tuple[float, float]:
        return (self.xcor(), self.ycor() - (self.height * 0.5))

    @property
    def beam_end(self) -> Tuple[float, float]:
        sx, sy = self.beam_start
        rad = math.radians(self.beam_angle_deg)
        ex = sx + math.sin(rad) * self.beam_length
        ey = sy - math.cos(rad) * self.beam_length
        return (ex, ey)

    def update(self, dt: float = 1.0) -> None:
        """Patrols horizontally scaled by `dt` and cycles its plasma beam."""
        super().update()
        if not self.alive:
            return

        now = time.monotonic()
        new_x = self.xcor() + (self.direction * self.base_speed * dt)
        if new_x >= 130:
            new_x = 130
            self.direction = -1
        elif new_x <= -130:
            new_x = -130
            self.direction = 1
        self.setx(new_x)

        if not self.beam_active and (now - self._last_beam_time) >= MOTHERSHIP_BEAM_COOLDOWN_SEC:
            self._last_beam_time = now
            self._beam_until = now + MOTHERSHIP_BEAM_DURATION_SEC
            self.beam_angle_deg = random.choice((-24.0, -14.0, 0.0, 14.0, 24.0))

    def move_by(self, dx: float, dy: float = 0.0) -> None:
        return

    def destroy(self) -> None:
        self._beam_until = 0.0
        super().destroy()