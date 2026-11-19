"""src/game/game_manager.py

Central game coordinator managing the Turtle screen, delta-time ontimer() loop,
keyboard & mouse event listeners, pre-play New Pilot / Existing Account chooser,
Vulcan spread combat, Mothership plasma beams, stackable power-up lifecycle,
multi-wave progression, persistent SQLite/JSON/CSV score recording, retro sound
effects, visual effects, and full UI transitions.
"""

import time
import turtle
from typing import Any, Dict, List, Optional, Tuple

from config import (
    BACKGROUND_COLOR,
    FRAME_DELAY_MS,
    LEFT_BOUNDARY,
    MAX_DELTA_SEC,
    RIGHT_BOUNDARY,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TARGET_FPS,
    WAVE_CLEAR_BONUS_BASE,
    WAVE_TRANSITION_DELAY_SEC,
    WINDOW_TITLE,
)
from src.audio.sound_manager import SoundManager
from src.entities.bullet import Bullet
from src.entities.player import Player
from src.entities.powerup import PowerUp, PowerUpType
from src.game.collision_manager import CollisionManager
from src.game.game_state import GameSession, GameState
from src.game.wave_manager import WaveManager
from src.storage.score_manager import ScoreManager
from src.ui.effects import Effects
from src.ui.hud import HOME_BUTTON_RECT, HUD, QUIT_BUTTON_RECT
from src.ui.menu import Menu
from src.ui.pixel_sprites import register_pixel_sprites
from src.ui.screens import Screens
from src.ui.sprites import register_all_shapes


class GameManager:
    """Coordinates the arcade window, delta-time loop scheduling, UI views, and gameplay."""

    def __init__(self) -> None:
        self.score_manager = ScoreManager()
        self.session = GameSession(high_score=self.score_manager.get_top_score())
        self.sound = SoundManager()
        self.is_running: bool = True
        self._is_fullscreen: bool = False
        self._wave_transition_until: float = 0.0
        self._session_recorded: bool = False
        self._pilot_selected: bool = False
        self._last_frame_time: float = time.monotonic()
        self.crystals_collected: int = 0

        self.screen = turtle.Screen()
        self._setup_screen()
        register_all_shapes(self.screen)
        register_pixel_sprites(self.screen)

        self.effects = Effects()

        self.player = Player()
        self.wave_manager = WaveManager(difficulty=self.session.difficulty)
        self.collision_manager = CollisionManager()
        self.player_bullets: List[Bullet] = []
        self.enemy_bullets: List[Bullet] = []
        self.powerups: List[PowerUp] = []

        self.hud = HUD()
        self.menu = Menu()
        self.screens = Screens()

        self._bind_controls()
        self._render_menu()

    def _setup_screen(self) -> None:
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.bgcolor(BACKGROUND_COLOR)
        self.screen.title(WINDOW_TITLE)
        self.screen.tracer(0)

        try:
            root_window = self.screen.cv._rootwindow
            root_window.protocol("WM_DELETE_WINDOW", self.quit_game)
        except Exception:
            pass

    def _bind_controls(self) -> None:
        self.screen.listen()

        for left_key in ("Left", "a", "A"):
            self.screen.onkeypress(self._on_left_press, left_key)
            self.screen.onkeyrelease(self._on_left_release, left_key)

        for right_key in ("Right", "d", "D"):
            self.screen.onkeypress(self._on_right_press, right_key)
            self.screen.onkeyrelease(self._on_right_release, right_key)

        self.screen.onkeypress(self._on_fire_press, "space")

        self.screen.onkeypress(self._on_mute_press, "s")
        self.screen.onkeypress(self._on_mute_press, "S")
        self.screen.onkeypress(self._on_fullscreen_press, "f")
        self.screen.onkeypress(self._on_fullscreen_press, "F")

        for digit in range(1, 10):
            self.screen.onkeypress(
                lambda d=digit: self._on_digit_press(d),
                str(digit),
            )

        self.screen.onkeypress(self._on_create_pilot_press, "c")
        self.screen.onkeypress(self._on_create_pilot_press, "C")
        self.screen.onkeypress(self._on_name_press, "n")
        self.screen.onkeypress(self._on_name_press, "N")
        self.screen.onkeypress(self._on_leaderboard_press, "h")
        self.screen.onkeypress(self._on_leaderboard_press, "H")
        self.screen.onkeypress(self._on_profiles_press, "u")
        self.screen.onkeypress(self._on_profiles_press, "U")
        self.screen.onkeypress(self._on_help_press, "question")
        self.screen.onkeypress(self._on_help_press, "slash")
        self.screen.onkeypress(self._on_back_press, "BackSpace")

        self.screen.onkeypress(self._on_menu_press, "m")
        self.screen.onkeypress(self._on_menu_press, "M")

        self.screen.onkeypress(self._on_start_press, "Return")
        self.screen.onkeypress(self._on_pause_press, "p")
        self.screen.onkeypress(self._on_pause_press, "P")
        self.screen.onkeypress(self._on_restart_press, "r")
        self.screen.onkeypress(self._on_restart_press, "R")
        self.screen.onkeypress(self._on_quit_press, "q")
        self.screen.onkeypress(self._on_quit_press, "Q")
        self.screen.onkeypress(self._on_escape_press, "Escape")

        try:
            self.screen.onclick(self._on_screen_click)
        except Exception:
            pass

    @staticmethod
    def _point_in_rect(
        x: float,
        y: float,
        rect: Tuple[float, float, float, float],
    ) -> bool:
        cx, cy, width, height = rect
        return abs(x - cx) <= (width / 2.0) and abs(y - cy) <= (height / 2.0)

    def _get_boss_hp_ratio(self) -> Optional[float]:
        boss = self.wave_manager.mothership
        if boss is not None and boss.alive:
            return boss.hp_ratio
        return None

    def _refresh_hud(self, force: bool = False) -> None:
        if self.session.state not in (GameState.PLAYING, GameState.PAUSED):
            return
        self.hud.update(
            self.session,
            active_buffs=self.player.get_active_buffs(),
            sound_enabled=self.sound.enabled,
            shield_charges=self.player.shield_charges,
            vulcan_level=self.player.vulcan_level,
            crystals_collected=self.crystals_collected,
            boss_hp_ratio=self._get_boss_hp_ratio(),
            force=force,
        )

    def _current_pilot_profile(self) -> Dict[str, Any]:
        return self.score_manager.get_pilot_profile(self.session.player_name)

    def _render_menu(self) -> None:
        self.menu.show(
            player_name=self.session.player_name,
            difficulty=self.session.difficulty,
            high_score=self.session.high_score,
            leaderboard=self.score_manager.load_high_scores(),
            sound_enabled=self.sound.enabled,
            pilot_profile=self._current_pilot_profile(),
            pilot_profiles=self.score_manager.get_all_pilot_profiles(),
        )

    def _refresh_menu(self) -> None:
        self.menu.render(
            player_name=self.session.player_name,
            difficulty=self.session.difficulty,
            high_score=self.session.high_score,
            leaderboard=self.score_manager.load_high_scores(),
            sound_enabled=self.sound.enabled,
            pilot_profile=self._current_pilot_profile(),
            pilot_profiles=self.score_manager.get_all_pilot_profiles(),
        )

    # ------------------------------------------------------------------
    # Pilot Account Selection & Creation Flow
    # ------------------------------------------------------------------
    def _open_account_selector(self, launch_after_select: bool = False) -> None:
        """Opens the New Pilot / Existing Account selector screen."""
        self.menu.open_account_select(
            player_name=self.session.player_name,
            difficulty=self.session.difficulty,
            high_score=self.session.high_score,
            leaderboard=self.score_manager.load_high_scores(),
            sound_enabled=self.sound.enabled,
            pilot_profile=self._current_pilot_profile(),
            pilot_profiles=self.score_manager.get_all_pilot_profiles(),
            launch_after_select=launch_after_select,
        )

    def _apply_selected_pilot(
        self,
        pilot_name: str,
        launch_after: bool = False,
    ) -> None:
        """Activates `pilot_name`, marks pilot confirmed, and optionally launches."""
        self.session.set_player_name(pilot_name)
        self._pilot_selected = True
        if launch_after:
            self.start_new_game()
        else:
            self.menu.show_main_view(
                player_name=self.session.player_name,
                difficulty=self.session.difficulty,
                high_score=self.session.high_score,
                leaderboard=self.score_manager.load_high_scores(),
                sound_enabled=self.sound.enabled,
                pilot_profile=self._current_pilot_profile(),
                pilot_profiles=self.score_manager.get_all_pilot_profiles(),
            )

    def _create_new_pilot_flow(self, launch_after: bool = False) -> None:
        """Prompts for a new pilot callsign and saves it to SQLite without overwriting."""
        entered = self.screen.textinput(
            "New Pilot Registration",
            "Enter your pilot callsign (max 16 characters):",
        )
        self.screen.listen()

        if entered is None:
            return

        cleaned = entered.strip()
        if not cleaned:
            return

        _created, profile = self.score_manager.register_pilot(cleaned)
        self._apply_selected_pilot(
            profile["player_name"],
            launch_after=launch_after,
        )

    def _select_existing_pilot_by_index(self, index: int) -> None:
        """Selects an existing pilot account by 0-based list index."""
        profiles = self.score_manager.get_all_pilot_profiles()
        if 0 <= index < min(len(profiles), Menu.MAX_SELECTABLE_ACCOUNTS):
            chosen_name = str(profiles[index]["player_name"])
            launch_after = self.menu.account_select_autolaunch
            self._apply_selected_pilot(chosen_name, launch_after=launch_after)

    def _on_digit_press(self, digit: int) -> None:
        if self.session.state != GameState.MENU:
            return

        if self.menu.showing_account_select:
            self._select_existing_pilot_by_index(digit - 1)
            return

        if not self.menu.is_in_subview:
            difficulty_map = {1: "Easy", 2: "Normal", 3: "Hard"}
            if digit in difficulty_map:
                self._select_difficulty(difficulty_map[digit])

    def _on_create_pilot_press(self) -> None:
        if self.session.state != GameState.MENU:
            return
        if self.menu.showing_account_select:
            self._create_new_pilot_flow(
                launch_after=self.menu.account_select_autolaunch
            )

    def _select_difficulty(self, difficulty: str) -> None:
        if self.session.state != GameState.MENU or self.menu.is_in_subview:
            return
        self.session.set_difficulty(difficulty)
        self._refresh_menu()

    def _cycle_difficulty(self, step: int) -> None:
        if self.session.state != GameState.MENU or self.menu.is_in_subview:
            return
        modes = Menu.DIFFICULTY_ORDER
        current_idx = (
            modes.index(self.session.difficulty)
            if self.session.difficulty in modes
            else 1
        )
        next_mode = modes[(current_idx + step) % len(modes)]
        self.session.set_difficulty(next_mode)
        self._refresh_menu()

    def _on_screen_click(self, x: float, y: float) -> None:
        if self.session.state in (GameState.PLAYING, GameState.PAUSED):
            if self._point_in_rect(x, y, HOME_BUTTON_RECT):
                self.return_to_menu()
                return
            if self._point_in_rect(x, y, QUIT_BUTTON_RECT):
                self.quit_game()
                return
            return

        if self.session.state != GameState.MENU:
            return

        if self.menu.showing_account_select:
            if self._point_in_rect(x, y, Menu.NEW_PILOT_BTN_RECT):
                self._create_new_pilot_flow(
                    launch_after=self.menu.account_select_autolaunch
                )
                return

            if abs(x) <= 330:
                profiles = self.score_manager.get_all_pilot_profiles()
                limit = min(len(profiles), Menu.MAX_SELECTABLE_ACCOUNTS)
                for idx in range(limit):
                    row_center_y = (
                        Menu.ACCOUNT_ROW_START_Y
                        - (idx * Menu.ACCOUNT_ROW_STEP_Y)
                        + 5.0
                    )
                    if abs(y - row_center_y) <= 15.0:
                        self._select_existing_pilot_by_index(idx)
                        return

            if y <= -220:
                self._on_back_press()
            return

        if self.menu.showing_profiles:
            if abs(x) <= 320:
                profiles = self.score_manager.get_all_pilot_profiles()
                for idx, entry in enumerate(profiles[:10]):
                    row_center_y = 128.0 - (idx * 31.0) + 6.0
                    if abs(y - row_center_y) <= 14.0:
                        self._apply_selected_pilot(
                            str(entry["player_name"]),
                            launch_after=False,
                        )
                        return
            if y <= -220:
                self._on_back_press()
            return

        if self.menu.showing_leaderboard or self.menu.showing_help:
            if y <= -220:
                self._on_back_press()
            return

        if abs(x - (LEFT_BOUNDARY + 18)) <= 24 and abs(y - 275) <= 24:
            self._on_fullscreen_press()
            return

        if abs(x - (RIGHT_BOUNDARY - 50)) <= 20 and abs(y - 275) <= 24:
            self._on_mute_press()
            return

        if abs(x - (RIGHT_BOUNDARY - 12)) <= 20 and abs(y - 275) <= 24:
            self._on_help_press()
            return

        # Clicking "PILOT: <name> [N] ACCOUNT" on bottom-left opens account chooser
        if LEFT_BOUNDARY <= x <= -20 and -228 <= y <= -196:
            self._open_account_selector(launch_after_select=False)
            return

        # Clicking PLAY box prompts for New/Existing account if not yet chosen
        if abs(x) <= 115 and abs(y - (-64)) <= 25:
            if not self._pilot_selected:
                self._open_account_selector(launch_after_select=True)
            else:
                self.start_new_game()

    def _on_left_press(self) -> None:
        if self.session.state == GameState.PLAYING:
            self.player.start_move_left()
        elif self.session.state == GameState.MENU:
            self._cycle_difficulty(-1)

    def _on_left_release(self) -> None:
        self.player.stop_move_left()

    def _on_right_press(self) -> None:
        if self.session.state == GameState.PLAYING:
            self.player.start_move_right()
        elif self.session.state == GameState.MENU:
            self._cycle_difficulty(1)

    def _on_right_release(self) -> None:
        self.player.stop_move_right()

    def _on_fire_press(self) -> None:
        if self.session.state != GameState.PLAYING:
            return

        fired = self.player.shoot(len(self.player_bullets))
        if not fired:
            return

        new_bullets = fired if isinstance(fired, list) else [fired]
        self.player_bullets.extend(new_bullets)
        for _ in new_bullets:
            self.session.record_shot()
        self.sound.play_laser()

    def _on_mute_press(self) -> None:
        self.sound.toggle_mute()
        if self.session.state == GameState.MENU:
            self._refresh_menu()
        elif self.session.state in (GameState.PLAYING, GameState.PAUSED):
            self._refresh_hud(force=True)

    def _on_fullscreen_press(self) -> None:
        self._is_fullscreen = not self._is_fullscreen
        try:
            root_window = self.screen.cv._rootwindow
            root_window.attributes("-fullscreen", self._is_fullscreen)
        except Exception:
            pass

    def _on_name_press(self) -> None:
        if self.session.state != GameState.MENU:
            return
        if self.menu.showing_account_select:
            self._create_new_pilot_flow(
                launch_after=self.menu.account_select_autolaunch
            )
            return
        if not self.menu.is_in_subview:
            self._open_account_selector(launch_after_select=False)

    def _on_leaderboard_press(self) -> None:
        if self.session.state != GameState.MENU:
            return
        self.menu.toggle_leaderboard(
            player_name=self.session.player_name,
            difficulty=self.session.difficulty,
            high_score=self.session.high_score,
            leaderboard=self.score_manager.load_high_scores(),
            sound_enabled=self.sound.enabled,
            pilot_profile=self._current_pilot_profile(),
            pilot_profiles=self.score_manager.get_all_pilot_profiles(),
        )

    def _on_profiles_press(self) -> None:
        if self.session.state != GameState.MENU:
            return
        self.menu.toggle_profiles(
            player_name=self.session.player_name,
            difficulty=self.session.difficulty,
            high_score=self.session.high_score,
            leaderboard=self.score_manager.load_high_scores(),
            sound_enabled=self.sound.enabled,
            pilot_profile=self._current_pilot_profile(),
            pilot_profiles=self.score_manager.get_all_pilot_profiles(),
        )

    def _on_help_press(self) -> None:
        if self.session.state != GameState.MENU:
            return
        self.menu.toggle_help(
            player_name=self.session.player_name,
            difficulty=self.session.difficulty,
            high_score=self.session.high_score,
            leaderboard=self.score_manager.load_high_scores(),
            sound_enabled=self.sound.enabled,
            pilot_profile=self._current_pilot_profile(),
            pilot_profiles=self.score_manager.get_all_pilot_profiles(),
        )

    def _on_back_press(self) -> None:
        if self.session.state == GameState.MENU and self.menu.is_in_subview:
            self.menu.show_main_view(
                player_name=self.session.player_name,
                difficulty=self.session.difficulty,
                high_score=self.session.high_score,
                leaderboard=self.score_manager.load_high_scores(),
                sound_enabled=self.sound.enabled,
                pilot_profile=self._current_pilot_profile(),
                pilot_profiles=self.score_manager.get_all_pilot_profiles(),
            )

    def _on_menu_press(self) -> None:
        if self.session.state in (
            GameState.PLAYING,
            GameState.PAUSED,
            GameState.GAME_OVER,
            GameState.VICTORY,
        ):
            self.return_to_menu()
        elif self.session.state == GameState.MENU and self.menu.is_in_subview:
            self._on_back_press()

    def _on_start_press(self) -> None:
        if self.session.state == GameState.MENU:
            if self.menu.showing_account_select:
                profiles = self.score_manager.get_all_pilot_profiles()
                if not profiles:
                    self._create_new_pilot_flow(
                        launch_after=self.menu.account_select_autolaunch
                    )
                elif self._pilot_selected:
                    self.start_new_game()
                return

            if not self._pilot_selected:
                self._open_account_selector(launch_after_select=True)
                return

            self.start_new_game()
        elif self.session.state in (GameState.GAME_OVER, GameState.VICTORY):
            self.start_new_game()

    def _on_pause_press(self) -> None:
        if self.session.state == GameState.PLAYING:
            self.session.state = GameState.PAUSED
            self.screens.show_pause(self.session)
        elif self.session.state == GameState.PAUSED:
            self.session.state = GameState.PLAYING
            self._last_frame_time = time.monotonic()
            self.screens.hide()
            self._refresh_hud(force=True)

    def _on_restart_press(self) -> None:
        if self.session.state in (
            GameState.PLAYING,
            GameState.PAUSED,
            GameState.GAME_OVER,
            GameState.VICTORY,
        ):
            self.start_new_game()

    def _on_quit_press(self) -> None:
        self.quit_game()

    def _on_escape_press(self) -> None:
        if self._is_fullscreen:
            self._on_fullscreen_press()
            return
        if self.session.state == GameState.MENU and self.menu.is_in_subview:
            self._on_back_press()
            return
        self.quit_game()

    def _clear_projectiles(self) -> None:
        for bullet in self.player_bullets:
            bullet.deactivate()
        self.player_bullets.clear()

        for bullet in self.enemy_bullets:
            bullet.deactivate()
        self.enemy_bullets.clear()

    def _clear_enemy_bullets(self) -> None:
        for bullet in self.enemy_bullets:
            bullet.deactivate()
        self.enemy_bullets.clear()

    def _clear_powerups(self) -> None:
        for capsule in self.powerups:
            capsule.deactivate()
        self.powerups.clear()

    def _add_bonus_score(self, points: int) -> None:
        if points <= 0:
            return
        self.session.score += points
        if self.session.score > self.session.high_score:
            self.session.high_score = self.session.score
            self.session.is_new_high_score = True

    def _persist_completed_session(self, outcome: str) -> None:
        if self._session_recorded:
            return
        self._session_recorded = True

        _qualified, rank = self.score_manager.record_session(
            self.session,
            outcome=outcome,
        )
        self.session.leaderboard_rank = rank
        self.session.high_score = max(
            self.session.high_score,
            self.score_manager.get_top_score(),
        )

    def return_to_menu(self) -> None:
        # Transition state immediately so any in-flight frame tick aborts cleanly
        self.session.state = GameState.MENU
        self._wave_transition_until = 0.0
        self.crystals_collected = 0

        self._clear_projectiles()
        self._clear_powerups()
        self.wave_manager.clear_all()
        self.player.hide_ship()
        self.effects.clear_transient()
        self.hud.hide()
        self.screens.hide()

        self.session.high_score = max(
            self.session.high_score,
            self.score_manager.get_top_score(),
        )
        self._render_menu()

    def start_new_game(self) -> None:
        self._clear_projectiles()
        self._clear_powerups()
        self.effects.clear_transient()
        self._wave_transition_until = 0.0
        self._session_recorded = False
        self._pilot_selected = True
        self._last_frame_time = time.monotonic()
        self.crystals_collected = 0

        self.menu.hide()
        self.screens.hide()

        self.session.high_score = max(
            self.session.high_score,
            self.score_manager.get_top_score(),
        )
        self.session.reset()
        self.session.state = GameState.PLAYING

        self.player.reset()
        self.wave_manager.set_difficulty(self.session.difficulty)
        self.wave_manager.spawn_wave(self.session.wave)

        self.hud.show()
        self._refresh_hud(force=True)

    def _award_wave_bonus(self, cleared_wave: int) -> int:
        bonus = cleared_wave * WAVE_CLEAR_BONUS_BASE
        self._add_bonus_score(bonus)
        return bonus

    def _begin_next_wave_transition(self) -> None:
        if self.session.state != GameState.PLAYING:
            return
        cleared_wave = self.session.wave
        bonus = self._award_wave_bonus(cleared_wave)
        self._clear_enemy_bullets()
        self.session.advance_wave()
        self.sound.play_wave_clear()

        next_wave = self.session.wave
        wave_title = self.wave_manager.get_wave_title(next_wave)
        self._wave_transition_until = time.monotonic() + WAVE_TRANSITION_DELAY_SEC

        self._refresh_hud(force=True)
        self.screens.show_wave_banner(
            cleared_wave=cleared_wave,
            bonus=bonus,
            next_wave=next_wave,
            wave_title=wave_title,
        )

    def _trigger_game_over(self, reason: str = "FLEET OVERWHELMED DEFENSES") -> None:
        self.session.state = GameState.GAME_OVER
        self._wave_transition_until = 0.0
        self._clear_projectiles()
        self._clear_powerups()
        self.wave_manager.clear_all()
        self.player.hide_ship()
        self.hud.hide()
        self.sound.play_game_over()

        self._persist_completed_session(outcome=GameState.GAME_OVER.value)
        self.screens.show_game_over(
            self.session.get_summary(),
            reason=reason,
            pilot_profile=self._current_pilot_profile(),
        )

    def _trigger_victory(self) -> None:
        self._award_wave_bonus(self.session.wave)
        self.session.state = GameState.VICTORY
        self._wave_transition_until = 0.0
        self._clear_projectiles()
        self._clear_powerups()
        self.wave_manager.clear_all()
        self.player.hide_ship()
        self.hud.hide()
        self.sound.play_victory()

        self._persist_completed_session(outcome=GameState.VICTORY.value)
        self.screens.show_victory(
            self.session.get_summary(),
            reason="GALACTIC ARMADA DEFEATED!",
            pilot_profile=self._current_pilot_profile(),
        )

    def _update_playing(self, dt: float = 1.0) -> None:
        if self.session.state != GameState.PLAYING:
            return

        self.player.update(dt=dt)

        for bullet in self.player_bullets:
            bullet.update(dt=dt)
        self.player_bullets = [b for b in self.player_bullets if b.active]

        for capsule in self.powerups:
            capsule.update(dt=dt)

        if self._wave_transition_until > 0.0:
            self.powerups = [p for p in self.powerups if p.active]
            self._refresh_hud()
            if (
                self.session.state == GameState.PLAYING
                and time.monotonic() >= self._wave_transition_until
            ):
                self._wave_transition_until = 0.0
                self.screens.hide()
                self.wave_manager.spawn_wave(self.session.wave)
            return

        self.wave_manager.update(dt=dt)
        if self.session.state != GameState.PLAYING:
            return

        enemy_bullet = self.wave_manager.try_spawn_enemy_bullet(
            len(self.enemy_bullets),
            dt=dt,
        )
        if enemy_bullet is not None:
            self.enemy_bullets.append(enemy_bullet)

        for bullet in self.enemy_bullets:
            bullet.update(dt=dt)

        report = self.collision_manager.process_collisions(
            player=self.player,
            player_bullets=self.player_bullets,
            enemy_bullets=self.enemy_bullets,
            wave_manager=self.wave_manager,
            powerups=self.powerups,
        )
        if self.session.state != GameState.PLAYING:
            return

        self.player_bullets = [b for b in self.player_bullets if b.active]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.active]
        self.powerups = [p for p in self.powerups if p.active]

        for _ in range(report.hits_landed):
            self.session.record_hit()

        if report.enemies_killed > 0:
            self.sound.play_explosion()
            self.session.record_kill(report.points_earned)
            if report.enemies_killed > 1:
                self.session.enemies_destroyed += report.enemies_killed - 1
        elif report.hits_landed > 0:
            self.sound.play_hit()

        for pos_x, pos_y in report.destroyed_positions:
            self.effects.spawn_explosion(pos_x, pos_y, color="#FACC15", count=12)
            capsule = PowerUp.maybe_spawn(pos_x, pos_y)
            if capsule is not None:
                self.powerups.append(capsule)

        if report.crystal_points > 0:
            self.crystals_collected += report.crystals_collected
            self._add_bonus_score(report.crystal_points)

        if report.shield_absorbed:
            self.sound.play_shield_block()
            self.effects.spawn_ring_flash(
                self.player.xcor(),
                self.player.ycor(),
                color="#38BDF8",
                start_radius=20.0,
                growth=3.5,
                life=10,
            )
            self.effects.spawn_floating_label(
                self.player.xcor(),
                self.player.ycor() + 24,
                f"SHIELD BLOCK! ({self.player.shield_charges} LEFT)",
                color="#38BDF8",
            )

        if report.collected_powerups:
            self.sound.play_powerup()

        for ptype in report.collected_powerups:
            if ptype == PowerUpType.SHIELD:
                self.effects.spawn_ring_flash(
                    self.player.xcor(),
                    self.player.ycor(),
                    color="#38BDF8",
                    start_radius=16.0,
                    growth=3.4,
                    life=11,
                )
                self.effects.spawn_floating_label(
                    self.player.xcor(),
                    self.player.ycor() + 24,
                    f"SHIELD x{self.player.shield_charges}!",
                    color="#38BDF8",
                )
            elif ptype in (PowerUpType.VULCAN, PowerUpType.RAPID_FIRE):
                self.effects.spawn_ring_flash(
                    self.player.xcor(),
                    self.player.ycor(),
                    color="#FACC15",
                    start_radius=16.0,
                    growth=3.4,
                    life=11,
                )
                self.effects.spawn_floating_label(
                    self.player.xcor(),
                    self.player.ycor() + 24,
                    f"VULCAN LV{self.player.vulcan_level}!",
                    color="#FACC15",
                )
            elif ptype == PowerUpType.CRYSTAL:
                self.effects.spawn_ring_flash(
                    self.player.xcor(),
                    self.player.ycor(),
                    color="#C084FC",
                    start_radius=14.0,
                    growth=3.0,
                    life=9,
                )
                self.effects.spawn_floating_label(
                    self.player.xcor(),
                    self.player.ycor() + 24,
                    "+10Pt CRYSTAL!",
                    color="#C084FC",
                )

        if self.session.state != GameState.PLAYING:
            return

        self._refresh_hud()

        if report.player_hit:
            self.sound.play_player_hit()
            self.effects.spawn_explosion(
                self.player.xcor(),
                self.player.ycor(),
                color="#FB7185",
                count=16,
            )
            remaining_lives = self.session.lose_life()
            self.player.trigger_invulnerability()
            self._refresh_hud(force=True)
            if remaining_lives <= 0:
                self._trigger_game_over("STARFIGHTER DESTROYED")
                return

        if report.defense_breached:
            self._trigger_game_over("INVADERS BREACHED DEFENSE LINE")
            return

        if (
            self.session.state == GameState.PLAYING
            and self.wave_manager.initial_enemy_count > 0
            and self.wave_manager.is_wave_cleared
        ):
            if self.wave_manager.is_final_wave(self.session.wave):
                self._trigger_victory()
            else:
                self._begin_next_wave_transition()

    def _render_active_boss_beam(self) -> None:
        boss = self.wave_manager.mothership
        if boss is not None and boss.alive and boss.beam_active:
            sx, sy = boss.beam_start
            ex, ey = boss.beam_end
            self.effects.draw_plasma_beam(sx, sy, ex, ey)

    def update(self) -> None:
        if not self.is_running:
            return

        frame_start = time.monotonic()
        elapsed_sec = max(0.0, frame_start - self._last_frame_time)
        self._last_frame_time = frame_start
        dt = max(0.25, min(elapsed_sec, MAX_DELTA_SEC) * TARGET_FPS)

        if self.session.state == GameState.PLAYING:
            self.session.add_play_time(min(elapsed_sec, 0.25))
            self._update_playing(dt=dt)
            if self.session.state == GameState.PLAYING:
                self.effects.update(scroll_stars=True, star_speed_scale=1.35, dt=dt)
                self._render_active_boss_beam()
            else:
                self.effects.update(scroll_stars=True, star_speed_scale=0.55, dt=dt)
        elif self.session.state == GameState.PAUSED:
            self.effects.update(scroll_stars=False, dt=0.0)
            self._render_active_boss_beam()
        else:
            self.effects.update(scroll_stars=True, star_speed_scale=0.55, dt=dt)

        try:
            self.screen.update()
            render_ms = (time.monotonic() - frame_start) * 1000.0
            next_delay_ms = max(1, int(FRAME_DELAY_MS - render_ms))
            self.screen.ontimer(self.update, next_delay_ms)
        except turtle.Terminator:
            self.is_running = False

    def quit_game(self) -> None:
        self.is_running = False
        self.sound.shutdown()
        try:
            self.screen.bye()
        except turtle.Terminator:
            pass

    def run(self) -> None:
        self._last_frame_time = time.monotonic()
        self.screen.ontimer(self.update, FRAME_DELAY_MS)
        self.screen.mainloop()