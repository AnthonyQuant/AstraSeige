"""src/entities/player.py

Player delta starfighter entity handling bounded horizontal movement,
stackable energy shield charges, 3-tier Vulcan fanning spread shots,
and post-hit invulnerability frames for AstraSeige.
"""

import time
import turtle
from typing import Dict, List, Optional, Union

from config import (
    INVULNERABILITY_SEC,
    LEFT_BOUNDARY,
    MAX_ACTIVE_PLAYER_BULLETS,
    MAX_SHIELD_CHARGES,
    PLAYER_COOLDOWN_SEC,
    PLAYER_SPEED,
    PLAYER_START_Y,
    RAPID_FIRE_COOLDOWN_SEC,
    RAPID_FIRE_DURATION_SEC,
    RIGHT_BOUNDARY,
    SHIELD_PICKUP_CHARGES,
    STARTING_SHIELD_CHARGES,
    VULCAN_MAX_LEVEL,
    VULCAN_SPREAD_ANGLES,
)
from src.entities.bullet import Bullet
from src.entities.powerup import PowerUpType
from src.ui.pixel_sprites import resolve_pixel_sprite


class Player(turtle.Turtle):
    """Represents the player-controlled purple-silver delta starfighter."""

    def __init__(self) -> None:
        super().__init__(visible=False)
        self.penup()
        self.speed(0)

        ship_shape = resolve_pixel_sprite("player_viper", "triangle")
        self.shape(ship_shape)
        self.setheading(90)
        if ship_shape == "player_viper":
            self.shapesize(stretch_wid=1.0, stretch_len=1.0)
        else:
            self.shapesize(stretch_wid=1.4, stretch_len=1.8)
        self.color("#A855F7")

        # Hitbox dimensions (in pixels) for collision checks
        self.width: int = 36
        self.height: int = 32

        # Movement state
        self.move_speed: float = PLAYER_SPEED
        self.moving_left: bool = False
        self.moving_right: bool = False

        # Weapon cooldown, Vulcan tier & projectile cap state
        self.fire_cooldown: float = PLAYER_COOLDOWN_SEC
        self.max_active_bullets: int = MAX_ACTIVE_PLAYER_BULLETS
        self._last_shot_time: float = -self.fire_cooldown
        self.vulcan_level: int = 1

        # Stackable shield charges & timed power-up state
        self.shield_charges: int = STARTING_SHIELD_CHARGES
        self._invulnerable_until: float = 0.0
        self._shield_until: float = 0.0
        self._rapid_fire_until: float = 0.0

        # Cached render states to prevent redundant Tkinter canvas reconfigurations
        self._last_color: str = "#A855F7"
        self._last_visible: bool = False
        self._shield_visible: bool = False

        # Dedicated Turtle ring for the energy shield halo
        self._shield_ring = turtle.Turtle(visible=False)
        self._shield_ring.penup()
        self._shield_ring.speed(0)
        self._shield_ring.shape("circle")
        self._shield_ring.shapesize(stretch_wid=2.4, stretch_len=2.4)
        self._shield_ring.color("#38BDF8", "")
        self._shield_ring.pensize(2)

        self.goto(0, PLAYER_START_Y)

    # ------------------------------------------------------------------
    # Directional Input Handlers
    # ------------------------------------------------------------------
    def start_move_left(self) -> None:
        self.moving_left = True

    def stop_move_left(self) -> None:
        self.moving_left = False

    def start_move_right(self) -> None:
        self.moving_right = True

    def stop_move_right(self) -> None:
        self.moving_right = False

    # ------------------------------------------------------------------
    # Stackable Shield & Vulcan Power-Up Management
    # ------------------------------------------------------------------
    @property
    def has_shield(self) -> bool:
        return self.shield_charges > 0 or time.monotonic() < self._shield_until

    @property
    def has_rapid_fire(self) -> bool:
        return self.vulcan_level > 1 or time.monotonic() < self._rapid_fire_until

    def add_shield_charge(self, amount: int = SHIELD_PICKUP_CHARGES) -> int:
        self.shield_charges = min(
            MAX_SHIELD_CHARGES,
            max(0, self.shield_charges + max(1, int(amount))),
        )
        return self.shield_charges

    def consume_shield_charge(self) -> bool:
        if self.shield_charges > 0:
            self.shield_charges -= 1
            return True
        if time.monotonic() < self._shield_until:
            self._shield_until = 0.0
            return True
        return False

    def upgrade_vulcan(self) -> int:
        self.vulcan_level = min(VULCAN_MAX_LEVEL, self.vulcan_level + 1)
        now = time.monotonic()
        self._rapid_fire_until = max(self._rapid_fire_until, now) + RAPID_FIRE_DURATION_SEC
        return self.vulcan_level

    def activate_powerup(
        self,
        powerup_type: PowerUpType,
        duration: Optional[float] = None,
    ) -> None:
        now = time.monotonic()
        vulcan_enum = getattr(PowerUpType, "VULCAN", None)

        if powerup_type == PowerUpType.SHIELD:
            self.add_shield_charge(SHIELD_PICKUP_CHARGES)
            if duration is not None and duration > 0:
                self._shield_until = max(self._shield_until, now) + duration
        elif powerup_type == PowerUpType.RAPID_FIRE or (
            vulcan_enum is not None and powerup_type == vulcan_enum
        ):
            self.upgrade_vulcan()
            if duration is not None:
                self._rapid_fire_until = now + max(0.0, duration)

    def get_active_buffs(self) -> Dict[str, float]:
        now = time.monotonic()
        active: Dict[str, float] = {}
        if self.shield_charges > 0:
            active[f"SHIELD x{self.shield_charges}"] = float(self.shield_charges)
        elif self._shield_until > now:
            active["SHIELD"] = round(self._shield_until - now, 1)

        if self.vulcan_level > 1:
            active[f"VULCAN LV{self.vulcan_level}"] = float(self.vulcan_level)
        if self._rapid_fire_until > now:
            active["RAPID FIRE"] = round(self._rapid_fire_until - now, 1)
        return active

    # ------------------------------------------------------------------
    # Weapon Firing (Linear & Fanning Vulcan Spread)
    # ------------------------------------------------------------------
    def _current_cooldown(self) -> float:
        if self.has_rapid_fire:
            return RAPID_FIRE_COOLDOWN_SEC
        return self.fire_cooldown

    def can_fire(self, active_bullet_count: int) -> bool:
        angles = VULCAN_SPREAD_ANGLES.get(self.vulcan_level, (0.0,))
        if active_bullet_count + len(angles) > self.max_active_bullets:
            return False
        return (time.monotonic() - self._last_shot_time) >= self._current_cooldown()

    def shoot_volley(self, active_bullet_count: int) -> List[Bullet]:
        if not self.can_fire(active_bullet_count):
            return []

        self._last_shot_time = time.monotonic()
        muzzle_y = self.ycor() + (self.height * 0.55)
        angles = VULCAN_SPREAD_ANGLES.get(self.vulcan_level, (0.0,))
        is_vulcan = self.vulcan_level > 1

        return [
            Bullet(
                x=self.xcor(),
                y=muzzle_y,
                owner="player",
                angle_deg=angle,
                is_vulcan=is_vulcan,
            )
            for angle in angles
        ]

    def shoot(self, active_bullet_count: int) -> Optional[Union[Bullet, List[Bullet]]]:
        volley = self.shoot_volley(active_bullet_count)
        if not volley:
            return None
        if len(volley) == 1:
            return volley[0]
        return volley

    # ------------------------------------------------------------------
    # Damage, Invulnerability & Visual Status Sync
    # ------------------------------------------------------------------
    @property
    def is_invulnerable(self) -> bool:
        return time.monotonic() < self._invulnerable_until

    def trigger_invulnerability(self, duration: float = INVULNERABILITY_SEC) -> None:
        self._invulnerable_until = time.monotonic() + max(0.0, float(duration))

    def _update_visual_effects(self) -> None:
        now = time.monotonic()

        if self.is_invulnerable:
            should_show = (int(now * 10) % 2) == 0
        else:
            should_show = True
            target_color = "#FACC15" if self.vulcan_level > 1 else "#A855F7"
            if target_color != self._last_color:
                self.color(target_color)
                self._last_color = target_color

        if should_show != self._last_visible:
            if should_show:
                self.showturtle()
            else:
                self.hideturtle()
            self._last_visible = should_show

        show_shield = self.has_shield and should_show
        if show_shield:
            self._shield_ring.goto(self.xcor(), self.ycor())
        if show_shield != self._shield_visible:
            if show_shield:
                self._shield_ring.showturtle()
            else:
                self._shield_ring.hideturtle()
            self._shield_visible = show_shield

    # ------------------------------------------------------------------
    # Per-Frame Update & Boundary Clamping
    # ------------------------------------------------------------------
    def update(self, dt: float = 1.0) -> None:
        """Updates horizontal position scaled by `dt`, boundary clamping, and buff visuals."""
        direction = 0
        if self.moving_left:
            direction -= 1
        if self.moving_right:
            direction += 1

        if direction != 0:
            new_x = self.xcor() + (direction * self.move_speed * dt)
            clamped_x = max(LEFT_BOUNDARY, min(RIGHT_BOUNDARY, new_x))
            self.setx(clamped_x)

        self._update_visual_effects()

    def reset(self) -> None:
        self.moving_left = False
        self.moving_right = False
        self.fire_cooldown = PLAYER_COOLDOWN_SEC
        self._last_shot_time = -self.fire_cooldown
        self.vulcan_level = 1
        self.shield_charges = STARTING_SHIELD_CHARGES
        self._invulnerable_until = 0.0
        self._shield_until = 0.0
        self._rapid_fire_until = 0.0
        self._last_color = "#A855F7"
        self._last_visible = True
        self._shield_visible = False
        self.color("#A855F7")
        self.goto(0, PLAYER_START_Y)
        self.showturtle()
        self._shield_ring.goto(0, PLAYER_START_Y)
        self._shield_ring.hideturtle()

    def hide_ship(self) -> None:
        self.moving_left = False
        self.moving_right = False
        self._invulnerable_until = 0.0
        self._shield_until = 0.0
        self._rapid_fire_until = 0.0
        self._last_visible = False
        self._shield_visible = False
        self._shield_ring.hideturtle()
        self.hideturtle()