"""src/game/collision_manager.py

Axis-Aligned Bounding Box (AABB) and beam-segment collision detection engine
handling Vulcan spread impacts, Bonus UFO hits, mid-air bullet interception,
stackable Shield absorption, +10Pt Crystal pickups, Mothership plasma beams,
and defense-line breaches for AstraSeige.
"""

from dataclasses import dataclass, field
import math
from typing import List, Optional, Protocol, Tuple

from src.entities.bullet import Bullet
from src.entities.player import Player
from src.entities.powerup import PowerUp, PowerUpType
from src.game.wave_manager import WaveManager


class Collidable(Protocol):
    """Structural protocol for any Turtle entity with center coordinates and hitbox size."""

    width: int
    height: int

    def xcor(self) -> float: ...
    def ycor(self) -> float: ...


@dataclass
class CollisionReport:
    """Structured summary of all collision events resolved during a single frame."""

    hits_landed: int = 0
    enemies_killed: int = 0
    points_earned: int = 0
    crystal_points: int = 0
    crystals_collected: int = 0
    destroyed_positions: List[Tuple[float, float]] = field(default_factory=list)
    collected_powerups: List[PowerUpType] = field(default_factory=list)
    shield_absorbed: bool = False
    player_hit: bool = False
    defense_breached: bool = False


class CollisionManager:
    """Evaluates spatial intersections between projectiles, invaders, beams, power-ups, and the player."""

    @staticmethod
    def check_aabb(entity_a: Collidable, entity_b: Collidable) -> bool:
        """Returns True if the rectangular hitboxes of two entities overlap."""
        half_w = (entity_a.width + entity_b.width) * 0.5
        half_h = (entity_a.height + entity_b.height) * 0.5

        dx = abs(entity_a.xcor() - entity_b.xcor())
        dy = abs(entity_a.ycor() - entity_b.ycor())

        return dx < half_w and dy < half_h

    @staticmethod
    def _point_to_segment_distance(
        px: float,
        py: float,
        ax: float,
        ay: float,
        bx: float,
        by: float,
    ) -> float:
        """Computes shortest Euclidean distance from point (px, py) to segment AB."""
        abx = bx - ax
        aby = by - ay
        len_sq = (abx * abx) + (aby * aby)
        if len_sq <= 1e-9:
            return math.hypot(px - ax, py - ay)

        t = ((px - ax) * abx + (py - ay) * aby) / len_sq
        t = max(0.0, min(1.0, t))
        closest_x = ax + (t * abx)
        closest_y = ay + (t * aby)
        return math.hypot(px - closest_x, py - closest_y)

    def _resolve_player_bullets(
        self,
        player_bullets: List[Bullet],
        wave_manager: WaveManager,
        report: CollisionReport,
    ) -> None:
        """Checks active player lasers and Vulcan bolts against UFOs, bosses, and invaders."""
        alive_enemies = wave_manager.alive_enemies

        for bullet in player_bullets:
            if not bullet.active:
                continue

            # 1. Check Bonus UFO first (high-priority bonus target)
            ufo = wave_manager.bonus_ufo
            if ufo is not None and ufo.alive and self.check_aabb(bullet, ufo):
                ufo_x, ufo_y = ufo.xcor(), ufo.ycor()
                bullet.deactivate()
                report.hits_landed += 1

                if ufo.take_damage(1):
                    report.enemies_killed += 1
                    report.points_earned += ufo.points
                    report.destroyed_positions.append((ufo_x, ufo_y))
                    wave_manager.bonus_ufo = None
                continue

            # 2. Check formation invaders and Mothership Boss
            for enemy in alive_enemies:
                if not enemy.alive:
                    continue

                if self.check_aabb(bullet, enemy):
                    enemy_x, enemy_y = enemy.xcor(), enemy.ycor()
                    bullet.deactivate()
                    report.hits_landed += 1

                    if enemy.take_damage(1):
                        report.enemies_killed += 1
                        report.points_earned += enemy.points
                        report.destroyed_positions.append((enemy_x, enemy_y))
                    break

    def _resolve_bullet_clashes(
        self,
        player_bullets: List[Bullet],
        enemy_bullets: List[Bullet],
    ) -> None:
        """Allows player lasers to shoot down incoming enemy bolts in mid-air."""
        for p_bullet in player_bullets:
            if not p_bullet.active:
                continue

            for e_bullet in enemy_bullets:
                if not e_bullet.active:
                    continue

                if self.check_aabb(p_bullet, e_bullet):
                    p_bullet.deactivate()
                    e_bullet.deactivate()
                    break

    def _resolve_enemy_bullets(
        self,
        enemy_bullets: List[Bullet],
        player: Player,
        report: CollisionReport,
    ) -> None:
        """Checks incoming enemy bolts against the player starfighter and stackable Shield."""
        for bullet in enemy_bullets:
            if not bullet.active:
                continue

            if self.check_aabb(bullet, player):
                bullet.deactivate()
                if player.consume_shield_charge():
                    report.shield_absorbed = True
                    player.trigger_invulnerability(0.45)
                elif not player.is_invulnerable:
                    report.player_hit = True
                    break

    def _resolve_mothership_beam(
        self,
        wave_manager: WaveManager,
        player: Player,
        report: CollisionReport,
    ) -> None:
        """Checks if the Dreadnought Mothership's active plasma beam strikes the player."""
        if report.player_hit or report.shield_absorbed or player.is_invulnerable:
            return

        boss = wave_manager.mothership
        if boss is None or not boss.alive or not boss.beam_active:
            return

        sx, sy = boss.beam_start
        ex, ey = boss.beam_end
        dist = self._point_to_segment_distance(
            px=player.xcor(),
            py=player.ycor(),
            ax=sx,
            ay=sy,
            bx=ex,
            by=ey,
        )

        # Beam core radius (~14 px) + player starfighter radius (~16 px)
        if dist <= 30.0:
            if player.consume_shield_charge():
                report.shield_absorbed = True
                player.trigger_invulnerability(0.65)
            else:
                report.player_hit = True

    def _resolve_powerups(
        self,
        powerups: List[PowerUp],
        player: Player,
        report: CollisionReport,
    ) -> None:
        """Checks falling Shield, Vulcan, and +10Pt Crystal pickups against the player."""
        for capsule in powerups:
            if not capsule.active:
                continue

            if self.check_aabb(capsule, player):
                if capsule.powerup_type == PowerUpType.CRYSTAL:
                    report.crystal_points += capsule.bonus_points
                    report.crystals_collected += 1
                else:
                    player.activate_powerup(
                        capsule.powerup_type,
                        duration=capsule.duration,
                    )

                report.collected_powerups.append(capsule.powerup_type)
                capsule.deactivate()

    def process_collisions(
        self,
        player: Player,
        player_bullets: List[Bullet],
        enemy_bullets: List[Bullet],
        wave_manager: WaveManager,
        powerups: Optional[List[PowerUp]] = None,
    ) -> CollisionReport:
        """Runs all collision passes for the current tick and returns a CollisionReport."""
        report = CollisionReport()

        self._resolve_player_bullets(player_bullets, wave_manager, report)
        self._resolve_bullet_clashes(player_bullets, enemy_bullets)
        self._resolve_enemy_bullets(enemy_bullets, player, report)
        self._resolve_mothership_beam(wave_manager, player, report)
        if powerups:
            self._resolve_powerups(powerups, player, report)
        report.defense_breached = wave_manager.has_breached_defense_line()

        return report