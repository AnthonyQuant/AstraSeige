"""tests/test_game_systems.py

Automated unit and integration test suite for AstraSeige.
Patches Turtle graphics primitives with lightweight stateful stubs so all tests
execute rapidly and deterministically without opening a GUI window.
"""

import csv
import inspect
from pathlib import Path
import shutil
import sys
import tempfile
import turtle
import unittest
from unittest.mock import patch

# Ensure the SpaceInvaders project root is importable regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (  # noqa: E402
    DEFENSE_LINE_Y,
    DIFFICULTY_SETTINGS,
    LEFT_BOUNDARY,
    MAX_WAVES,
    PLAYER_START_Y,
    RIGHT_BOUNDARY,
    STARTING_SHIELD_CHARGES,
)
from src.audio.sound_manager import SoundManager  # noqa: E402
from src.entities.bullet import Bullet  # noqa: E402
from src.entities.enemy_types import (  # noqa: E402
    ArmouredInvader,
    BasicInvader,
    ClusterInvader,
    EliteInvader,
    MothershipBoss,
)
from src.entities.player import Player  # noqa: E402
from src.entities.powerup import PowerUp, PowerUpType  # noqa: E402
from src.game.collision_manager import CollisionManager  # noqa: E402
from src.game.game_state import GameSession, GameState  # noqa: E402
from src.game.wave_manager import WaveManager  # noqa: E402
from src.storage.score_manager import ScoreManager  # noqa: E402


# ----------------------------------------------------------------------
# Headless Turtle Stubs
# ----------------------------------------------------------------------
def _stub_turtle_init(
    self: turtle.Turtle,
    shape: str = "classic",
    undobuffersize: int = 1000,
    visible: bool = True,
) -> None:
    self._stub_x = 0.0
    self._stub_y = 0.0
    self._stub_visible = bool(visible)
    self._stub_shape = shape
    self._stub_color = "#FFFFFF"
    self._stub_heading = 0.0


def _stub_goto(self: turtle.Turtle, x: float, y: float = None) -> None:  # type: ignore[assignment]
    if y is None and isinstance(x, (tuple, list)):
        self._stub_x = float(x[0])
        self._stub_y = float(x[1])
    else:
        self._stub_x = float(x)
        self._stub_y = float(y)


def _stub_setx(self: turtle.Turtle, x: float) -> None:
    self._stub_x = float(x)


def _stub_sety(self: turtle.Turtle, y: float) -> None:
    self._stub_y = float(y)


def _stub_xcor(self: turtle.Turtle) -> float:
    return getattr(self, "_stub_x", 0.0)


def _stub_ycor(self: turtle.Turtle) -> float:
    return getattr(self, "_stub_y", 0.0)


def _stub_showturtle(self: turtle.Turtle) -> None:
    self._stub_visible = True


def _stub_hideturtle(self: turtle.Turtle) -> None:
    self._stub_visible = False


def _stub_isvisible(self: turtle.Turtle) -> bool:
    return getattr(self, "_stub_visible", True)


def _stub_shape(self: turtle.Turtle, name: str = None) -> str:  # type: ignore[assignment]
    if name is not None:
        self._stub_shape = name
    return getattr(self, "_stub_shape", "classic")


def _stub_color(self: turtle.Turtle, *args: str) -> tuple:
    if args:
        self._stub_color = args[0]
    c = getattr(self, "_stub_color", "#FFFFFF")
    return (c, c)


def _stub_setheading(self: turtle.Turtle, to_angle: float) -> None:
    self._stub_heading = float(to_angle)


def _stub_noop(self: turtle.Turtle, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
    return None


class _DummyScreen:
    """Minimal headless Screen stub for resolve_shape() lookups."""

    def getshapes(self) -> list:
        return ["classic", "triangle", "square", "circle"]


class HeadlessTurtleTestCase(unittest.TestCase):
    """Base TestCase that isolates all Turtle calls from Tkinter."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._turtle_patcher = patch.multiple(
            turtle.Turtle,
            __init__=_stub_turtle_init,
            goto=_stub_goto,
            setx=_stub_setx,
            sety=_stub_sety,
            xcor=_stub_xcor,
            ycor=_stub_ycor,
            showturtle=_stub_showturtle,
            hideturtle=_stub_hideturtle,
            isvisible=_stub_isvisible,
            shape=_stub_shape,
            color=_stub_color,
            setheading=_stub_setheading,
            shapesize=_stub_noop,
            speed=_stub_noop,
            penup=_stub_noop,
            pendown=_stub_noop,
            pensize=_stub_noop,
            clear=_stub_noop,
            write=_stub_noop,
            stamp=_stub_noop,
            clearstamps=_stub_noop,
            begin_fill=_stub_noop,
            end_fill=_stub_noop,
            dot=_stub_noop,
            circle=_stub_noop,
        )
        cls._screen_patcher = patch.object(
            turtle, "Screen", return_value=_DummyScreen()
        )
        cls._turtle_patcher.start()
        cls._screen_patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._screen_patcher.stop()
        cls._turtle_patcher.stop()
        super().tearDownClass()


# ----------------------------------------------------------------------
# 1. Session Telemetry & Difficulty Preset Tests
# ----------------------------------------------------------------------
class TestGameSession(unittest.TestCase):
    """Verifies GameSession state transitions, accuracy math, and difficulty presets."""

    def test_difficulty_presets_sync_lives(self) -> None:
        session = GameSession(difficulty="Easy", high_score=500)
        self.assertEqual(session.state, GameState.MENU)
        self.assertEqual(session.lives, DIFFICULTY_SETTINGS["Easy"]["starting_lives"])

        session.set_difficulty("Hard")
        self.assertEqual(session.lives, DIFFICULTY_SETTINGS["Hard"]["starting_lives"])

    def test_kills_accuracy_and_high_score_tracking(self) -> None:
        session = GameSession(player_name="AcePilot", difficulty="Normal", high_score=25)
        session.record_shot()
        session.record_shot()
        session.record_shot()
        session.record_shot()

        session.record_hit()
        session.record_kill(10)
        self.assertFalse(session.is_new_high_score)
        self.assertEqual(session.high_score, 25)

        session.record_hit()
        session.record_kill(30)
        self.assertTrue(session.is_new_high_score)
        self.assertEqual(session.score, 40)
        self.assertEqual(session.high_score, 40)
        self.assertEqual(session.enemies_destroyed, 2)
        self.assertEqual(session.accuracy, 50.0)

    def test_reset_clears_run_metrics_but_preserves_high_score(self) -> None:
        session = GameSession(player_name="Nova", difficulty="Normal", high_score=100)
        session.record_shot()
        session.record_hit()
        session.record_kill(150)
        session.advance_wave()

        session.reset()
        self.assertEqual(session.score, 0)
        self.assertEqual(session.wave, 1)
        self.assertEqual(session.shots_fired, 0)
        self.assertEqual(session.hits, 0)
        self.assertEqual(session.high_score, 150)
        self.assertEqual(session.player_name, "Nova")


# ----------------------------------------------------------------------
# 2. Player, Vulcan Spread, Stackable Shield & Invader Entity Tests
# ----------------------------------------------------------------------
class TestEntitiesAndPowerUps(HeadlessTurtleTestCase):
    """Verifies movement clamping, Vulcan spread volleys, stacked shields, and bosses."""

    def test_player_horizontal_movement_clamped_to_boundaries(self) -> None:
        player = Player()
        player.reset()
        self.assertEqual(player.ycor(), PLAYER_START_Y)

        player.start_move_left()
        for _ in range(200):
            player.update()
        self.assertEqual(player.xcor(), LEFT_BOUNDARY)
        player.stop_move_left()

        player.start_move_right()
        for _ in range(400):
            player.update()
        self.assertEqual(player.xcor(), RIGHT_BOUNDARY)

    def test_player_firing_and_vulcan_spread_levels(self) -> None:
        player = Player()
        player.reset()

        first_volley = player.shoot(active_bullet_count=0)
        self.assertTrue(bool(first_volley))
        # Immediate second shot blocked by standard cooldown
        self.assertFalse(bool(player.shoot(active_bullet_count=1)))

        # Upgrading Vulcan Core unlocks 3-way and 5-way fanning spread volleys
        player.activate_powerup(PowerUpType.VULCAN, duration=8.0)
        self.assertEqual(player.vulcan_level, 2)
        self.assertTrue(player.has_rapid_fire)
        player._last_shot_time = 0.0
        spread_3 = player.shoot(active_bullet_count=0)
        self.assertIsInstance(spread_3, list)
        self.assertEqual(len(spread_3), 3)

        player.activate_powerup(PowerUpType.VULCAN, duration=8.0)
        self.assertEqual(player.vulcan_level, 3)
        player._last_shot_time = 0.0
        spread_5 = player.shoot(active_bullet_count=0)
        self.assertIsInstance(spread_5, list)
        self.assertEqual(len(spread_5), 5)

    def test_stackable_shield_charges(self) -> None:
        player = Player()
        player.reset()
        self.assertEqual(player.shield_charges, STARTING_SHIELD_CHARGES)

        player.shield_charges = 0
        player.activate_powerup(PowerUpType.SHIELD)
        player.activate_powerup(PowerUpType.SHIELD)
        self.assertEqual(player.shield_charges, 2)
        self.assertIn("SHIELD x2", player.get_active_buffs())

        self.assertTrue(player.consume_shield_charge())
        self.assertEqual(player.shield_charges, 1)
        self.assertTrue(player.consume_shield_charge())
        self.assertEqual(player.shield_charges, 0)
        self.assertFalse(player.consume_shield_charge())

    def test_multi_hp_invader_and_boss_degradation(self) -> None:
        armoured = ArmouredInvader(x=0, y=100)
        self.assertEqual(armoured.health, 3)
        self.assertFalse(armoured.take_damage(1))
        self.assertFalse(armoured.take_damage(1))
        self.assertTrue(armoured.take_damage(1))
        self.assertFalse(armoured.alive)

        elite = EliteInvader(x=40, y=100)
        self.assertEqual(elite.health, 4)
        for _ in range(3):
            self.assertFalse(elite.take_damage(1))
        self.assertTrue(elite.take_damage(1))
        self.assertFalse(elite.alive)

        crab = ClusterInvader(x=-40, y=100, tier="red")
        self.assertEqual(crab.points, 35)
        self.assertFalse(crab.take_damage(1))
        self.assertTrue(crab.take_damage(1))

        boss = MothershipBoss(x=0, y=140, wave_number=5)
        self.assertEqual(boss.points, 500)
        self.assertGreater(boss.health, 10)


# ----------------------------------------------------------------------
# 3. Wave Formations & Collision Resolution Tests
# ----------------------------------------------------------------------
class TestWaveAndCollisionSystems(HeadlessTurtleTestCase):
    """Verifies curated wave formations, shield absorption, crystals, and boss beams."""

    def test_wave_manager_curated_formations_and_final_wave(self) -> None:
        wm = WaveManager(difficulty="Normal")

        wm.spawn_wave(1)
        self.assertGreater(len(wm.alive_enemies), 0)
        self.assertIsNone(wm.mothership)

        wm.spawn_wave(2)
        self.assertEqual(len(wm.alive_enemies), 36)
        self.assertTrue(all(isinstance(e, ClusterInvader) for e in wm.alive_enemies))

        wm.spawn_wave(5)
        self.assertIsNotNone(wm.mothership)
        self.assertTrue(wm.mothership.alive)

        self.assertFalse(wm.is_final_wave(1))
        self.assertTrue(wm.is_final_wave(MAX_WAVES))

        wm.clear_all()
        self.assertTrue(wm.is_wave_cleared)

    def test_player_bullet_destroys_basic_invader(self) -> None:
        player = Player()
        player.reset()
        wm = WaveManager(difficulty="Normal")
        cm = CollisionManager()

        invader = BasicInvader(x=50, y=120)
        wm.enemies = [invader]
        bullet = Bullet(x=50, y=120, owner="player")

        report = cm.process_collisions(
            player=player,
            player_bullets=[bullet],
            enemy_bullets=[],
            wave_manager=wm,
            powerups=[],
        )

        self.assertEqual(report.hits_landed, 1)
        self.assertEqual(report.enemies_killed, 1)
        self.assertEqual(report.points_earned, 10)
        self.assertFalse(invader.alive)
        self.assertFalse(bullet.active)

    def test_shield_consumes_one_charge_per_hit(self) -> None:
        player = Player()
        player.reset()
        player.shield_charges = 0
        player.activate_powerup(PowerUpType.SHIELD)
        player.activate_powerup(PowerUpType.SHIELD)
        self.assertEqual(player.shield_charges, 2)

        wm = WaveManager(difficulty="Normal")
        cm = CollisionManager()
        enemy_bolt = Bullet(x=player.xcor(), y=player.ycor(), owner="enemy")

        report = cm.process_collisions(
            player=player,
            player_bullets=[],
            enemy_bullets=[enemy_bolt],
            wave_manager=wm,
            powerups=[],
        )

        self.assertTrue(report.shield_absorbed)
        self.assertFalse(report.player_hit)
        self.assertEqual(player.shield_charges, 1)
        self.assertFalse(enemy_bolt.active)

    def test_crystal_pickup_and_direct_hit(self) -> None:
        player = Player()
        player.reset()
        player.shield_charges = 0
        wm = WaveManager(difficulty="Normal")
        cm = CollisionManager()

        crystal = PowerUp(
            x=player.xcor(),
            y=player.ycor(),
            powerup_type=PowerUpType.CRYSTAL,
        )
        enemy_bolt = Bullet(x=player.xcor(), y=player.ycor(), owner="enemy")

        report = cm.process_collisions(
            player=player,
            player_bullets=[],
            enemy_bullets=[enemy_bolt],
            wave_manager=wm,
            powerups=[crystal],
        )

        self.assertIn(PowerUpType.CRYSTAL, report.collected_powerups)
        self.assertEqual(report.crystal_points, 10)
        self.assertEqual(report.crystals_collected, 1)
        self.assertTrue(report.player_hit)
        self.assertFalse(crystal.active)
        self.assertFalse(enemy_bolt.active)

    def test_mothership_plasma_beam_hits_player(self) -> None:
        player = Player()
        player.reset()
        player.shield_charges = 0
        wm = WaveManager(difficulty="Normal")
        cm = CollisionManager()

        boss = MothershipBoss(x=0, y=140, wave_number=5)
        boss.beam_active = True
        boss.beam_angle_deg = 0.0
        wm.mothership = boss
        wm.enemies = [boss]

        report = cm.process_collisions(
            player=player,
            player_bullets=[],
            enemy_bullets=[],
            wave_manager=wm,
            powerups=[],
        )
        self.assertTrue(report.player_hit)

    def test_defense_line_breach_detection(self) -> None:
        player = Player()
        player.reset()
        wm = WaveManager(difficulty="Normal")
        cm = CollisionManager()

        breaching_invader = BasicInvader(x=0, y=DEFENSE_LINE_Y - 5)
        wm.enemies = [breaching_invader]

        report = cm.process_collisions(
            player=player,
            player_bullets=[],
            enemy_bullets=[],
            wave_manager=wm,
            powerups=[],
        )
        self.assertTrue(report.defense_breached)


# ----------------------------------------------------------------------
# 4. Persistent High-Score & CSV Telemetry Tests
# ----------------------------------------------------------------------
class TestScoreManagerPersistence(unittest.TestCase):
    """Verifies JSON Top-10 leaderboard ranking and CSV match history logging."""

    def setUp(self) -> None:
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="astraseige_test_"))
        json_path = self._tmp_dir / "high_scores.json"
        csv_path = self._tmp_dir / "game_history.csv"

        params = list(inspect.signature(ScoreManager.__init__).parameters.keys())[1:]
        if len(params) >= 2:
            self.manager = ScoreManager(**{params[0]: json_path, params[1]: csv_path})
        else:
            self.manager = ScoreManager()
        self.json_path = json_path
        self.csv_path = csv_path

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_leaderboard_sorting_top_10_cap_and_csv_logging(self) -> None:
        for idx in range(12):
            session = GameSession(player_name=f"Pilot{idx}", difficulty="Normal")
            session.score = (idx + 1) * 100
            session.wave = (idx % 10) + 1
            session.enemies_destroyed = idx + 3
            session.shots_fired = 20
            session.hits = 10
            qualified, rank = self.manager.record_session(session, outcome="GAME_OVER")
            self.assertTrue(qualified)
            self.assertEqual(rank, 1)

        leaderboard = self.manager.load_high_scores()
        self.assertEqual(len(leaderboard), 10)
        self.assertEqual(self.manager.get_top_score(), 1200)
        self.assertEqual(leaderboard[0]["player_name"], "Pilot11")

        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(len(rows), 13)


# ----------------------------------------------------------------------
# 5. Sound Manager Thread & Mute Tests
# ----------------------------------------------------------------------
class TestSoundManager(unittest.TestCase):
    """Verifies non-blocking sound queueing, mute toggling, and clean shutdown."""

    def test_mute_toggle_and_shutdown(self) -> None:
        sound = SoundManager(enabled=True)
        self.assertTrue(sound.enabled)

        new_state = sound.toggle_mute()
        self.assertFalse(new_state)
        self.assertFalse(sound.enabled)

        sound.play_laser()
        sound.shutdown()


if __name__ == "__main__":
    unittest.main(verbosity=2)