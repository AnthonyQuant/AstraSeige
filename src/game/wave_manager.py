"""src/game/wave_manager.py

Coordinated enemy fleet formation controller handling classic grids,
inverted-V multicolored crab clusters, twin saucer wings, Mothership boss waves,
kill-based frenzy acceleration, and Bonus UFO spawning for AstraSeige.
"""

import random
from typing import Dict, List, Optional, Tuple

from config import (
    DEFAULT_DIFFICULTY,
    DEFENSE_LINE_Y,
    DIFFICULTY_SETTINGS,
    ENEMY_BULLET_SPEED,
    FORMATION_COLS,
    FORMATION_DROP_DISTANCE,
    FORMATION_START_Y,
    FORMATION_X_SPACING,
    FORMATION_Y_SPACING,
    LEFT_BOUNDARY,
    MAX_WAVES,
    RIGHT_BOUNDARY,
    UFO_SPAWN_CHANCE_PER_TICK,
)
from src.entities.bullet import Bullet
from src.entities.enemy import Enemy
from src.entities.enemy_types import (
    ArmouredInvader,
    BasicInvader,
    BonusUFO,
    ClusterInvader,
    EliteInvader,
    MothershipBoss,
)

WAVE_TITLES: Dict[int, str] = {
    1: "SCOUT VANGUARD",
    2: "CRIMSON PYRAMID",
    3: "SAUCER FLANK",
    4: "PRISM ARMADA",
    5: "MOTHERSHIP ASSAULT",
    6: "DREADNOUGHT WING",
    7: "VORTEX CLUSTER",
    8: "SHOCK ARMADA",
    9: "IMPERIAL GUARD",
    10: "FINAL ARMADA",
}

PYRAMID_ROW_TIERS: Tuple[str, ...] = (
    "red",
    "orange",
    "cyan",
    "pink",
    "yellow",
    "red",
    "orange",
    "cyan",
)


class WaveManager:
    """Controls enemy formation layouts, group movement, boss patrols, and wave progression."""

    def __init__(self, difficulty: str = DEFAULT_DIFFICULTY) -> None:
        self.difficulty: str = (
            difficulty if difficulty in DIFFICULTY_SETTINGS else DEFAULT_DIFFICULTY
        )
        self.wave: int = 1
        self.direction: int = 1
        self.base_speed: float = 1.6

        self.enemies: List[Enemy] = []
        self.initial_enemy_count: int = 0
        self.bonus_ufo: Optional[BonusUFO] = None
        self.mothership: Optional[MothershipBoss] = None

    def set_difficulty(self, difficulty: str) -> None:
        if difficulty in DIFFICULTY_SETTINGS:
            self.difficulty = difficulty

    # ------------------------------------------------------------------
    # Formation Spawning & Progressive Layouts
    # ------------------------------------------------------------------
    @staticmethod
    def get_wave_title(wave: int) -> str:
        return WAVE_TITLES.get(wave, f"SECTOR {wave}")

    @staticmethod
    def is_final_wave(wave: int) -> bool:
        return wave >= MAX_WAVES

    def _rows_for_wave(self, wave: int) -> int:
        if wave == 1:
            return 3
        if wave <= 4:
            return 4
        return 5

    def _cols_for_wave(self, wave: int) -> int:
        if wave == 1:
            return max(6, FORMATION_COLS - 1)
        if wave <= 6:
            return FORMATION_COLS
        return FORMATION_COLS + 1

    def _create_enemy_for_cell(
        self, wave: int, row: int, col: int, x: float, y: float
    ) -> Enemy:
        if row == 0:
            return EliteInvader(x=x, y=y, row=row, col=col)
        if row == 1 and wave >= 6:
            return ArmouredInvader(x=x, y=y, row=row, col=col)
        if row == 2 and wave >= 9:
            return ArmouredInvader(x=x, y=y, row=row, col=col)
        return BasicInvader(x=x, y=y, row=row, col=col)

    def _spawn_standard_grid(self, wave: int) -> None:
        rows = self._rows_for_wave(wave)
        cols = self._cols_for_wave(wave)
        x_spacing = 62 if cols > FORMATION_COLS else FORMATION_X_SPACING
        total_grid_width = (cols - 1) * x_spacing
        start_x = -total_grid_width / 2.0

        for row in range(rows):
            y = FORMATION_START_Y - (row * FORMATION_Y_SPACING)
            for col in range(cols):
                x = start_x + (col * x_spacing)
                enemy = self._create_enemy_for_cell(
                    wave=wave, row=row, col=col, x=x, y=y
                )
                self.enemies.append(enemy)

    def _spawn_inverted_pyramid_cluster(self) -> None:
        max_cols = len(PYRAMID_ROW_TIERS)
        x_spacing = 52.0
        y_spacing = 26.0
        top_y = 232.0

        for row_idx, tier in enumerate(PYRAMID_ROW_TIERS):
            count = max_cols - row_idx
            row_width = (count - 1) * x_spacing
            start_x = -row_width / 2.0
            y = top_y - (row_idx * y_spacing)

            for idx in range(count):
                x = start_x + (idx * x_spacing)
                self.enemies.append(
                    ClusterInvader(
                        x=x,
                        y=y,
                        tier=tier,
                        row=row_idx,
                        col=row_idx * 10 + idx,
                    )
                )

    def _spawn_saucer_flank_wave(self, wave: int) -> None:
        left_offsets = (-285.0, -235.0, -185.0)
        right_offsets = (185.0, 235.0, 285.0)

        for row_idx, y in enumerate((215.0, 172.0, 129.0)):
            for col_idx, x in enumerate(left_offsets):
                self.enemies.append(
                    ArmouredInvader(x=x, y=y, row=row_idx, col=col_idx)
                )
            for col_idx, x in enumerate(right_offsets):
                self.enemies.append(
                    ArmouredInvader(x=x, y=y, row=row_idx, col=col_idx + 10)
                )

        for row_idx, y in enumerate((215.0, 172.0)):
            for col_idx, x in enumerate((-45.0, 45.0)):
                self.enemies.append(
                    EliteInvader(x=x, y=y, row=row_idx, col=col_idx + 5)
                )

    def _spawn_mothership_boss_wave(self, wave: int) -> None:
        left_positions = (
            (-305.0, 212.0), (-260.0, 212.0), (-215.0, 212.0), (-170.0, 212.0),
            (-238.0, 182.0),
            (-295.0, 152.0), (-248.0, 152.0), (-200.0, 152.0),
            (-268.0, 122.0), (-215.0, 122.0),
        )
        for idx, (x, y) in enumerate(left_positions):
            self.enemies.append(
                ArmouredInvader(x=x, y=y, row=idx // 4, col=idx)
            )

        right_positions = (
            (215.0, 222.0), (262.0, 222.0),
            (175.0, 192.0), (220.0, 192.0), (265.0, 192.0), (310.0, 192.0),
            (215.0, 162.0), (262.0, 162.0),
            (175.0, 132.0), (220.0, 132.0), (265.0, 132.0), (310.0, 132.0),
        )
        for idx, (x, y) in enumerate(right_positions):
            self.enemies.append(
                ArmouredInvader(x=x, y=y, row=idx // 4, col=20 + idx)
            )

        boss = MothershipBoss(x=0.0, y=138.0, wave_number=wave)
        self.mothership = boss
        self.enemies.append(boss)

    def spawn_wave(self, wave: int) -> List[Enemy]:
        self.clear_all()
        self.wave = max(1, min(MAX_WAVES, int(wave)))
        self.direction = 1

        if self.wave in (2, 4, 7):
            self._spawn_inverted_pyramid_cluster()
        elif self.wave in (3, 8):
            self._spawn_saucer_flank_wave(self.wave)
        elif self.wave in (5, 10):
            self._spawn_mothership_boss_wave(self.wave)
        else:
            self._spawn_standard_grid(self.wave)

        self.initial_enemy_count = len(self.enemies)
        return self.enemies

    def clear_all(self) -> None:
        """Hides and cleans up all active enemies, bosses, and bonus UFOs."""
        for enemy in self.enemies:
            try:
                enemy.hideturtle()
                enemy.clear()
            except Exception:
                pass
            enemy.destroy()
        self.enemies.clear()
        self.mothership = None

        if self.bonus_ufo is not None:
            try:
                self.bonus_ufo.hideturtle()
                self.bonus_ufo.clear()
            except Exception:
                pass
            self.bonus_ufo.destroy()
            self.bonus_ufo = None

    # ------------------------------------------------------------------
    # Fleet Telemetry & Kinematics
    # ------------------------------------------------------------------
    @property
    def alive_enemies(self) -> List[Enemy]:
        return [enemy for enemy in self.enemies if enemy.alive]

    @property
    def is_wave_cleared(self) -> bool:
        return self.initial_enemy_count > 0 and len(self.alive_enemies) == 0

    def get_frontline_enemies(self) -> List[Enemy]:
        lowest_by_col: Dict[int, Enemy] = {}
        for enemy in self.alive_enemies:
            if isinstance(enemy, MothershipBoss):
                continue
            current = lowest_by_col.get(enemy.col)
            if current is None or enemy.ycor() < current.ycor():
                lowest_by_col[enemy.col] = enemy
        return list(lowest_by_col.values())

    def get_current_speed(self) -> float:
        alive_count = len(self.alive_enemies)
        if alive_count == 0 or self.initial_enemy_count == 0:
            return 0.0

        preset = DIFFICULTY_SETTINGS[self.difficulty]
        diff_mult = preset["enemy_speed_mult"]
        wave_mult = 1.0 + ((self.wave - 1) * preset["wave_speed_step"])

        eliminated_ratio = (
            self.initial_enemy_count - alive_count
        ) / self.initial_enemy_count
        frenzy_mult = 1.0 + (1.35 * (eliminated_ratio ** 1.35))

        return self.base_speed * diff_mult * wave_mult * frenzy_mult

    # ------------------------------------------------------------------
    # Randomised Attacks & Bonus UFO Spawning
    # ------------------------------------------------------------------
    def try_spawn_enemy_bullet(
        self,
        active_enemy_bullets: int,
        dt: float = 1.0,
    ) -> Optional[Bullet]:
        preset = DIFFICULTY_SETTINGS[self.difficulty]
        wave_bullet_cap = preset["max_enemy_bullets"] + ((self.wave - 1) // 3)
        if active_enemy_bullets >= wave_bullet_cap:
            return None

        frontline = self.get_frontline_enemies()
        if not frontline:
            return None

        wave_fire_mult = 1.0 + ((self.wave - 1) * 0.09)
        fire_chance = preset["enemy_fire_prob"] * wave_fire_mult * min(dt, 3.0)
        if random.random() >= fire_chance:
            return None

        weights = [max(0.1, enemy.fire_weight) for enemy in frontline]
        shooter = random.choices(frontline, weights=weights, k=1)[0]
        bullet_speed = ENEMY_BULLET_SPEED * (1.0 + ((self.wave - 1) * 0.04))
        return shooter.shoot(bullet_speed=bullet_speed)

    def _update_bonus_ufo(self, dt: float = 1.0) -> None:
        if self.bonus_ufo is not None:
            if self.bonus_ufo.alive:
                self.bonus_ufo.update(dt=dt)
            if not self.bonus_ufo.alive:
                self.bonus_ufo = None
            return

        if self.mothership is not None and self.mothership.alive:
            return

        spawn_prob = UFO_SPAWN_CHANCE_PER_TICK * min(dt, 3.0)
        if self.alive_enemies and random.random() < spawn_prob:
            self.bonus_ufo = BonusUFO()

    def update(self, dt: float = 1.0) -> None:
        """Advances the formation horizontally scaled by `dt`, updates boss & UFOs."""
        alive = self.alive_enemies
        if not alive:
            self.mothership = None
            self._update_bonus_ufo(dt=dt)
            return

        if self.mothership is not None:
            if self.mothership.alive:
                self.mothership.update(dt=dt)
            else:
                self.mothership = None

        marching_enemies = [e for e in alive if not isinstance(e, MothershipBoss)]
        if marching_enemies:
            step_x = self.direction * self.get_current_speed() * dt
            min_left_edge = min(e.xcor() - (e.width / 2.0) for e in marching_enemies)
            max_right_edge = max(e.xcor() + (e.width / 2.0) for e in marching_enemies)

            hit_right = (
                self.direction > 0 and (max_right_edge + step_x) >= RIGHT_BOUNDARY
            )
            hit_left = (
                self.direction < 0 and (min_left_edge + step_x) <= LEFT_BOUNDARY
            )

            if hit_right or hit_left:
                if hit_right:
                    clamp_dx = RIGHT_BOUNDARY - max_right_edge
                else:
                    clamp_dx = LEFT_BOUNDARY - min_left_edge

                for enemy in marching_enemies:
                    enemy.move_by(clamp_dx, -FORMATION_DROP_DISTANCE)
                self.direction *= -1
            else:
                for enemy in marching_enemies:
                    enemy.move_by(step_x, 0.0)

        self._update_bonus_ufo(dt=dt)

    def has_breached_defense_line(self) -> bool:
        for enemy in self.alive_enemies:
            if isinstance(enemy, MothershipBoss):
                continue
            bottom_edge = enemy.ycor() - (enemy.height / 2.0)
            if bottom_edge <= DEFENSE_LINE_Y:
                return True
        return False