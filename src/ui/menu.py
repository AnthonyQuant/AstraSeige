"""src/ui/menu.py

Retro pixel-art Launch Home Screen, Pilot Hangar Account Selector (New Pilot or
Existing Account), interactive [?] Fleet & Power-Up Guide, Top-10 High Scores
Leaderboard, and [U] Pilot Career Database renderer for AstraSeige.
"""

import turtle
from typing import Any, Dict, List, Optional, Tuple

from config import (
    DEFAULT_DIFFICULTY,
    DEFAULT_PLAYER_NAME,
    DIFFICULTY_SETTINGS,
    LEFT_BOUNDARY,
    MAX_WAVES,
    RIGHT_BOUNDARY,
)
from src.ui.pixel_sprites import resolve_pixel_sprite


class Menu:
    """Renders the pre-game Title Screen, Account Selector, [?] Guide, Scores, and Pilot DB."""

    DIFFICULTY_ORDER: Tuple[str, ...] = ("Easy", "Normal", "Hard")
    DIFFICULTY_ACCENTS: Dict[str, str] = {
        "Easy": "#4ADE80",
        "Normal": "#38BDF8",
        "Hard": "#FB7185",
    }

    # Layout constants for clickable Pilot Account Selector rows
    NEW_PILOT_BTN_RECT: Tuple[float, float, float, float] = (0.0, 174.0, 350.0, 36.0)
    ACCOUNT_ROW_START_Y: float = 96.0
    ACCOUNT_ROW_STEP_Y: float = 33.0
    MAX_SELECTABLE_ACCOUNTS: int = 8

    def __init__(self) -> None:
        self._pen = turtle.Turtle(visible=False)
        self._pen.penup()
        self._pen.speed(0)

        self.is_visible: bool = False
        self.showing_leaderboard: bool = False
        self.showing_help: bool = False
        self.showing_profiles: bool = False
        self.showing_account_select: bool = False
        self.account_select_autolaunch: bool = False

    @property
    def is_in_subview(self) -> bool:
        """True when any modal/sub-screen is open over the main Title Screen."""
        return (
            self.showing_leaderboard
            or self.showing_help
            or self.showing_profiles
            or self.showing_account_select
        )

    # ------------------------------------------------------------------
    # Visibility & Sub-View Toggles
    # ------------------------------------------------------------------
    def _clear_canvas(self) -> None:
        try:
            self._pen.clearstamps()
        except Exception:
            pass
        self._pen.clear()

    def _reset_subviews(self) -> None:
        self.showing_leaderboard = False
        self.showing_help = False
        self.showing_profiles = False
        self.showing_account_select = False
        self.account_select_autolaunch = False

    def show(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.is_visible = True
        self._reset_subviews()
        self.render(
            player_name=player_name,
            difficulty=difficulty,
            high_score=high_score,
            leaderboard=leaderboard,
            sound_enabled=sound_enabled,
            pilot_profile=pilot_profile,
            pilot_profiles=pilot_profiles,
        )

    def hide(self) -> None:
        self.is_visible = False
        self._reset_subviews()
        self._clear_canvas()

    def open_account_select(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
        launch_after_select: bool = False,
    ) -> None:
        """Opens the New Pilot / Existing Account selector view."""
        self.is_visible = True
        self._reset_subviews()
        self.showing_account_select = True
        self.account_select_autolaunch = bool(launch_after_select)
        self.render(
            player_name=player_name,
            difficulty=difficulty,
            high_score=high_score,
            leaderboard=leaderboard,
            sound_enabled=sound_enabled,
            pilot_profile=pilot_profile,
            pilot_profiles=pilot_profiles,
        )

    def toggle_leaderboard(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        target = not self.showing_leaderboard
        self.is_visible = True
        self._reset_subviews()
        self.showing_leaderboard = target
        self.render(
            player_name=player_name,
            difficulty=difficulty,
            high_score=high_score,
            leaderboard=leaderboard,
            sound_enabled=sound_enabled,
            pilot_profile=pilot_profile,
            pilot_profiles=pilot_profiles,
        )

    def toggle_profiles(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Switches between the main Title Screen and the [U] Pilot Career Database."""
        target = not self.showing_profiles
        self.is_visible = True
        self._reset_subviews()
        self.showing_profiles = target
        self.render(
            player_name=player_name,
            difficulty=difficulty,
            high_score=high_score,
            leaderboard=leaderboard,
            sound_enabled=sound_enabled,
            pilot_profile=pilot_profile,
            pilot_profiles=pilot_profiles,
        )

    def toggle_help(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        target = not self.showing_help
        self.is_visible = True
        self._reset_subviews()
        self.showing_help = target
        self.render(
            player_name=player_name,
            difficulty=difficulty,
            high_score=high_score,
            leaderboard=leaderboard,
            sound_enabled=sound_enabled,
            pilot_profile=pilot_profile,
            pilot_profiles=pilot_profiles,
        )

    def show_main_view(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.is_visible = True
        self._reset_subviews()
        self.render(
            player_name=player_name,
            difficulty=difficulty,
            high_score=high_score,
            leaderboard=leaderboard,
            sound_enabled=sound_enabled,
            pilot_profile=pilot_profile,
            pilot_profiles=pilot_profiles,
        )

    # ------------------------------------------------------------------
    # Pixel Icon & Geometry Helpers
    # ------------------------------------------------------------------
    def _draw_box(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        border_color: str,
        fill_color: Optional[str] = None,
        line_width: int = 2,
    ) -> None:
        half_w = width / 2.0
        half_h = height / 2.0
        left = center_x - half_w
        right = center_x + half_w
        top = center_y + half_h
        bottom = center_y - half_h

        self._pen.pensize(line_width)
        if fill_color:
            self._pen.color(border_color, fill_color)
        else:
            self._pen.color(border_color)

        self._pen.goto(left, top)
        self._pen.pendown()
        if fill_color:
            self._pen.begin_fill()
        self._pen.goto(right, top)
        self._pen.goto(right, bottom)
        self._pen.goto(left, bottom)
        self._pen.goto(left, top)
        if fill_color:
            self._pen.end_fill()
        self._pen.penup()

    def _draw_horizontal_divider(self, y: float, color: str = "#1E293B") -> None:
        self._pen.pensize(1)
        self._pen.color(color)
        self._pen.goto(LEFT_BOUNDARY + 20, y)
        self._pen.pendown()
        self._pen.goto(RIGHT_BOUNDARY - 20, y)
        self._pen.penup()

    def _stamp_sprite(
        self,
        shape_name: str,
        fallback_shape: str,
        fallback_color: str,
        x: float,
        y: float,
    ) -> None:
        chosen = resolve_pixel_sprite(shape_name, fallback_shape)
        self._pen.shape(chosen)
        self._pen.color(fallback_color)
        self._pen.goto(x, y)
        try:
            self._pen.stamp()
        except Exception:
            pass

    def _draw_starburst(self, cx: float, cy: float) -> None:
        layers = (
            ("#DC2626", 18.0),
            ("#F97316", 13.0),
            ("#FACC15", 8.0),
            ("#FEF9C3", 4.0),
        )
        for color, radius in layers:
            self._draw_box(
                center_x=cx,
                center_y=cy,
                width=radius * 1.6,
                height=radius * 0.9,
                border_color=color,
                fill_color=color,
                line_width=1,
            )
            self._draw_box(
                center_x=cx,
                center_y=cy,
                width=radius * 0.9,
                height=radius * 1.6,
                border_color=color,
                fill_color=color,
                line_width=1,
            )

        spark_offsets = ((-13, 11), (13, 11), (-13, -11), (13, -11))
        for dx, dy in spark_offsets:
            self._draw_box(
                center_x=cx + dx,
                center_y=cy + dy,
                width=4,
                height=4,
                border_color="#FB923C",
                fill_color="#FB923C",
                line_width=1,
            )

    def _draw_fullscreen_icon(self, cx: float, cy: float) -> None:
        self._pen.color("#F8FAFC")
        self._pen.pensize(3)
        arm = 6.0
        span = 11.0
        corners = ((-1, 1), (1, 1), (-1, -1), (1, -1))
        for sx, sy in corners:
            tip_x = cx + sx * span
            tip_y = cy + sy * span
            self._pen.goto(tip_x - sx * arm, tip_y)
            self._pen.pendown()
            self._pen.goto(tip_x, tip_y)
            self._pen.goto(tip_x, tip_y - sy * arm)
            self._pen.penup()

        self._pen.color("#64748B")
        self._pen.goto(cx, cy - 26)
        self._pen.write("[F]", align="center", font=("Courier", 9, "bold"))

    def _draw_speaker_and_help_icons(
        self,
        speaker_x: float,
        help_x: float,
        cy: float,
        sound_enabled: bool,
    ) -> None:
        self._draw_box(
            center_x=speaker_x - 7,
            center_y=cy,
            width=7,
            height=10,
            border_color="#F8FAFC",
            fill_color="#F8FAFC",
            line_width=1,
        )
        self._pen.color("#F8FAFC", "#F8FAFC")
        self._pen.goto(speaker_x - 3, cy + 5)
        self._pen.pendown()
        self._pen.begin_fill()
        self._pen.goto(speaker_x + 4, cy + 10)
        self._pen.goto(speaker_x + 4, cy - 10)
        self._pen.goto(speaker_x - 3, cy - 5)
        self._pen.goto(speaker_x - 3, cy + 5)
        self._pen.end_fill()
        self._pen.penup()

        if sound_enabled:
            self._pen.pensize(2)
            self._pen.color("#F8FAFC")
            for offset, half_h in ((8, 5), (12, 9)):
                self._pen.goto(speaker_x + offset, cy + half_h)
                self._pen.pendown()
                self._pen.goto(speaker_x + offset + 2, cy)
                self._pen.goto(speaker_x + offset, cy - half_h)
                self._pen.penup()
        else:
            self._pen.pensize(2)
            self._pen.color("#FB7185")
            self._pen.goto(speaker_x + 8, cy + 6)
            self._pen.pendown()
            self._pen.goto(speaker_x + 15, cy - 6)
            self._pen.penup()
            self._pen.goto(speaker_x + 15, cy + 6)
            self._pen.pendown()
            self._pen.goto(speaker_x + 8, cy - 6)
            self._pen.penup()

        self._pen.color("#64748B")
        self._pen.goto(speaker_x + 2, cy - 26)
        self._pen.write("[S]", align="center", font=("Courier", 9, "bold"))

        self._pen.color("#F8FAFC")
        self._pen.goto(help_x, cy - 12)
        self._pen.write("?", align="center", font=("Courier", 20, "bold"))
        self._pen.color("#64748B")
        self._pen.goto(help_x, cy - 26)
        self._pen.write("[?]", align="center", font=("Courier", 9, "bold"))

    # ------------------------------------------------------------------
    # Main Render Dispatcher
    # ------------------------------------------------------------------
    def render(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
        leaderboard: Optional[List[Dict[str, Any]]] = None,
        sound_enabled: bool = True,
        pilot_profile: Optional[Dict[str, Any]] = None,
        pilot_profiles: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if not self.is_visible:
            return

        self._clear_canvas()

        if self.showing_account_select:
            self._render_account_selector(
                profiles=pilot_profiles or [],
                active_pilot=player_name,
                launch_after_select=self.account_select_autolaunch,
            )
        elif self.showing_leaderboard:
            self._render_leaderboard(leaderboard or [])
        elif self.showing_profiles:
            self._render_pilot_profiles(pilot_profiles or [], active_pilot=player_name)
        elif self.showing_help:
            self._render_help_guide()
        else:
            self._render_title_screen(
                player_name=player_name,
                difficulty=difficulty,
                high_score=high_score,
                sound_enabled=sound_enabled,
                pilot_profile=pilot_profile,
            )

    # ------------------------------------------------------------------
    # Pilot Account Selector View (New Pilot or Existing Account)
    # ------------------------------------------------------------------
    def _render_account_selector(
        self,
        profiles: List[Dict[str, Any]],
        active_pilot: str = DEFAULT_PLAYER_NAME,
        launch_after_select: bool = False,
    ) -> None:
        """Renders the pre-game New Pilot / Existing Account chooser."""
        self._pen.color("#38BDF8")
        self._pen.goto(0, 246)
        self._pen.write(
            "PILOT HANGAR — SELECT ACCOUNT",
            align="center",
            font=("Courier", 21, "bold"),
        )

        subtitle = (
            "CHOOSE AN EXISTING ACCOUNT OR REGISTER A NEW CALLSIGN TO LAUNCH"
            if launch_after_select
            else "SELECT AN EXISTING ACCOUNT OR CREATE A NEW PILOT CALLSIGN"
        )
        self._pen.color("#94A3B8")
        self._pen.goto(0, 218)
        self._pen.write(
            subtitle,
            align="center",
            font=("Courier", 10, "bold"),
        )

        # Prominent [+ NEW PILOT] button
        bx, by, bw, bh = self.NEW_PILOT_BTN_RECT
        self._draw_box(
            center_x=bx,
            center_y=by,
            width=bw,
            height=bh,
            border_color="#22C55E",
            fill_color="#071910",
            line_width=2,
        )
        self._pen.color("#4ADE80")
        self._pen.goto(bx, by - 7)
        self._pen.write(
            "[+ NEW PILOT]   PRESS [C] OR CLICK",
            align="center",
            font=("Courier", 12, "bold"),
        )

        self._draw_horizontal_divider(142, color="#334155")

        header_row = (
            f"{'KEY':<6}{'PILOT':<17}{'BEST SCORE':>12}{'STAGE':>9}{'BEST TIME':>12}{'GAMES':>7}"
        )
        self._pen.color("#94A3B8")
        self._pen.goto(0, 121)
        self._pen.write(
            header_row,
            align="center",
            font=("Courier", 10, "bold"),
        )

        self._draw_horizontal_divider(109, color="#1E293B")

        if not profiles:
            self._pen.color("#FACC15")
            self._pen.goto(0, 18)
            self._pen.write(
                "NO EXISTING ACCOUNTS FOUND",
                align="center",
                font=("Courier", 15, "bold"),
            )
            self._pen.color("#CBD5E1")
            self._pen.goto(0, -14)
            self._pen.write(
                "Press [C] or [ENTER] (or click [+ NEW PILOT]) to add your name first!",
                align="center",
                font=("Courier", 10, "normal"),
            )
        else:
            active_key = active_pilot.strip().lower()
            visible_profiles = profiles[: self.MAX_SELECTABLE_ACCOUNTS]
            for idx, entry in enumerate(visible_profiles):
                row_y = self.ACCOUNT_ROW_START_Y - (idx * self.ACCOUNT_ROW_STEP_Y)
                key_badge = f"[{idx + 1}]"
                pilot = str(entry.get("player_name", DEFAULT_PLAYER_NAME))[:15]
                score = int(entry.get("high_score", 0))
                stage = f"{int(entry.get('highest_wave', 0))}/{MAX_WAVES}"
                best_time = str(entry.get("best_time_formatted", "--:--"))
                games = int(entry.get("games_played", 0))

                is_current = pilot.lower() == active_key
                self._draw_box(
                    center_x=0,
                    center_y=row_y + 5,
                    width=660,
                    height=26,
                    border_color="#22C55E" if is_current else "#1E293B",
                    fill_color="#0A192F" if is_current else "#090D1A",
                    line_width=1,
                )

                line = (
                    f"{key_badge:<6}{pilot:<17}{score:>12,}{stage:>9}{best_time:>12}{games:>7}"
                )
                self._pen.color("#4ADE80" if is_current else "#E2E8F0")
                self._pen.goto(0, row_y - 2)
                self._pen.write(
                    line,
                    align="center",
                    font=("Courier", 10, "bold" if is_current else "normal"),
                )

        self._draw_horizontal_divider(-212, color="#334155")

        self._pen.color("#4ADE80")
        self._pen.goto(0, -248)
        self._pen.write(
            "[1-8] SELECT ACCOUNT   •   [C] NEW PILOT   •   [ESC / BACKSPACE] BACK",
            align="center",
            font=("Courier", 10, "bold"),
        )

    # ------------------------------------------------------------------
    # Title Screen View
    # ------------------------------------------------------------------
    def _render_title_screen(
        self,
        player_name: str,
        difficulty: str,
        high_score: int,
        sound_enabled: bool,
        pilot_profile: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._draw_fullscreen_icon(cx=LEFT_BOUNDARY + 18, cy=275)
        self._draw_speaker_and_help_icons(
            speaker_x=RIGHT_BOUNDARY - 52,
            help_x=RIGHT_BOUNDARY - 12,
            cy=275,
            sound_enabled=sound_enabled,
        )

        self._stamp_sprite("crab_red", "square", "#F43F5E", -74, 182)
        self._stamp_sprite("green_invader", "square", "#22C55E", 0, 182)
        self._stamp_sprite("crab_cyan", "square", "#38BDF8", 74, 182)

        self._pen.color("#22C55E")
        self._pen.goto(0, 108)
        self._pen.write(
            "ASTRA",
            align="center",
            font=("Courier", 38, "bold"),
        )

        self._draw_starburst(cx=-155, cy=74)
        self._pen.color("#F43F5E")
        self._pen.goto(0, 50)
        self._pen.write(
            "SEIGE",
            align="center",
            font=("Courier", 38, "bold"),
        )
        self._draw_starburst(cx=155, cy=74)

        self._pen.color("#E2E8F0")
        self._pen.goto(0, -4)
        self._pen.write(
            f"High Score: {max(0, int(high_score))}",
            align="center",
            font=("Courier", 15, "bold"),
        )

        # Neon Green-Outlined PLAY Button Box
        self._draw_box(
            center_x=0,
            center_y=-64,
            width=230,
            height=48,
            border_color="#22C55E",
            fill_color="#07130D",
            line_width=2,
        )
        self._pen.color("#22C55E")
        self._pen.goto(0, -74)
        self._pen.write(
            "PLAY",
            align="center",
            font=("Courier", 18, "bold"),
        )

        self._pen.color("#64748B")
        self._pen.goto(0, -106)
        self._pen.write(
            "PRESS [ENTER] TO START",
            align="center",
            font=("Courier", 10, "bold"),
        )

        # Active Pilot SQLite Career Strip
        profile = pilot_profile or {}
        p_best = int(profile.get("high_score", 0))
        p_wave = int(profile.get("highest_wave", 0))
        p_time = str(profile.get("best_time_formatted", "--:--"))
        p_games = int(profile.get("games_played", 0))

        self._draw_box(
            center_x=0,
            center_y=-148,
            width=660,
            height=34,
            border_color="#1E293B",
            fill_color="#0B1120",
            line_width=1,
        )
        self._pen.color("#38BDF8")
        self._pen.goto(0, -155)
        self._pen.write(
            f"PILOT RECORD  |  BEST: {p_best:,}  •  STAGE: {p_wave}/{MAX_WAVES}  •  TIME: {p_time}  •  GAMES: {p_games}",
            align="center",
            font=("Courier", 10, "bold"),
        )

        # Bottom Status & Quick-Select Bar
        self._draw_horizontal_divider(-184, color="#1E293B")

        diff_accent = self.DIFFICULTY_ACCENTS.get(difficulty, "#38BDF8")
        preset = DIFFICULTY_SETTINGS.get(difficulty, {})
        lives = preset.get("starting_lives", 3)

        self._pen.color("#4ADE80")
        self._pen.goto(LEFT_BOUNDARY + 14, -214)
        self._pen.write(
            f"PILOT: {player_name} [N] ACCOUNT",
            align="left",
            font=("Courier", 11, "bold"),
        )

        self._pen.color(diff_accent)
        self._pen.goto(RIGHT_BOUNDARY - 14, -214)
        self._pen.write(
            f"MODE: {difficulty.upper()} ({lives} LIVES) [1/2/3]",
            align="right",
            font=("Courier", 11, "bold"),
        )

        self._pen.color("#CBD5E1")
        self._pen.goto(0, -248)
        self._pen.write(
            "[H] TOP-10   •   [U] PILOT DB   •   [?] INTEL   •   [Q / ESC] QUIT",
            align="center",
            font=("Courier", 10, "bold"),
        )

    # ------------------------------------------------------------------
    # [U] Pilot Career Database View
    # ------------------------------------------------------------------
    def _render_pilot_profiles(
        self,
        profiles: List[Dict[str, Any]],
        active_pilot: str = DEFAULT_PLAYER_NAME,
    ) -> None:
        """Renders per-pilot SQLite records: High Score, Best Time, Max Stage, Games."""
        self._pen.color("#38BDF8")
        self._pen.goto(0, 242)
        self._pen.write(
            "PILOT CAREER DATABASE",
            align="center",
            font=("Courier", 23, "bold"),
        )

        self._pen.color("#94A3B8")
        self._pen.goto(0, 214)
        self._pen.write(
            "CLICK ANY PILOT TO SWITCH ACCOUNT  •  (data/astraseige.db)",
            align="center",
            font=("Courier", 10, "bold"),
        )

        self._draw_horizontal_divider(195, color="#334155")

        header_row = (
            f"{'PILOT':<18}{'HIGH SCORE':>12}{'BEST TIME':>12}{'STAGE':>9}{'GAMES':>8}"
        )
        self._pen.color("#94A3B8")
        self._pen.goto(0, 170)
        self._pen.write(
            header_row,
            align="center",
            font=("Courier", 11, "bold"),
        )

        self._draw_horizontal_divider(156, color="#1E293B")

        if not profiles:
            self._pen.color("#64748B")
            self._pen.goto(0, 20)
            self._pen.write(
                "NO PILOT PROFILES SAVED YET",
                align="center",
                font=("Courier", 15, "bold"),
            )
            self._pen.goto(0, -12)
            self._pen.write(
                "Press [N] to register a pilot or play a mission to log stats!",
                align="center",
                font=("Courier", 10, "normal"),
            )
        else:
            active_key = active_pilot.strip().lower()
            for idx, entry in enumerate(profiles[:10]):
                row_y = 128 - (idx * 31)
                pilot = str(entry.get("player_name", DEFAULT_PLAYER_NAME))[:16]
                score = int(entry.get("high_score", 0))
                best_time = str(entry.get("best_time_formatted", "--:--"))
                stage = f"{int(entry.get('highest_wave', 0))}/{MAX_WAVES}"
                games = int(entry.get("games_played", 0))

                is_current = pilot.lower() == active_key
                line = (
                    f"{pilot:<18}{score:>12,}{best_time:>12}{stage:>9}{games:>8}"
                )
                self._pen.color("#4ADE80" if is_current else "#CBD5E1")
                self._pen.goto(0, row_y)
                self._pen.write(
                    line,
                    align="center",
                    font=("Courier", 11, "bold" if is_current else "normal"),
                )

        self._draw_horizontal_divider(-212, color="#334155")

        self._pen.color("#4ADE80")
        self._pen.goto(0, -248)
        self._pen.write(
            "[U / BACKSPACE] Back to Title Screen     |     [ENTER] Launch Mission",
            align="center",
            font=("Courier", 11, "bold"),
        )

    # ------------------------------------------------------------------
    # [?] Fleet Intel & Power-Up Guide Sub-View
    # ------------------------------------------------------------------
    def _render_help_guide(self) -> None:
        self._pen.color("#22C55E")
        self._pen.goto(0, 245)
        self._pen.write(
            "ASTRASEIGE TACTICAL BRIEFING",
            align="center",
            font=("Courier", 21, "bold"),
        )

        self._draw_horizontal_divider(224, color="#334155")

        self._pen.color("#38BDF8")
        self._pen.goto(0, 198)
        self._pen.write(
            "HOSTILE FLEET CLASSIFICATION",
            align="center",
            font=("Courier", 12, "bold"),
        )

        roster = (
            ("green_invader", "#22C55E", "SCOUT (1 HP)", "10 PTS", -265),
            ("crab_cyan", "#38BDF8", "CLUSTER (1-2 HP)", "15-35 PTS", -90),
            ("saucer_enemy", "#FB923C", "SAUCER (3 HP)", "30 PTS", 90),
            ("purple_invader", "#A855F7", "ELITE (4 HP)", "60 PTS", 265),
        )
        for shape_key, color, label, pts, x_pos in roster:
            self._stamp_sprite(shape_key, "square", color, x_pos, 155)
            self._pen.color(color)
            self._pen.goto(x_pos, 120)
            self._pen.write(label, align="center", font=("Courier", 9, "bold"))
            self._pen.color("#E2E8F0")
            self._pen.goto(x_pos, 104)
            self._pen.write(pts, align="center", font=("Courier", 9, "normal"))

        self._stamp_sprite("mothership_boss", "circle", "#F43F5E", -175, 45)
        self._pen.color("#F43F5E")
        self._pen.goto(45, 50)
        self._pen.write(
            "DREADNOUGHT MOTHERSHIP BOSS (500 PTS)",
            align="center",
            font=("Courier", 11, "bold"),
        )
        self._pen.color("#CBD5E1")
        self._pen.goto(45, 30)
        self._pen.write(
            "Appears on Waves 5 & 10 • Fires sweeping plasma beams",
            align="center",
            font=("Courier", 9, "normal"),
        )

        self._draw_horizontal_divider(6, color="#1E293B")

        self._pen.color("#FACC15")
        self._pen.goto(0, -18)
        self._pen.write(
            "POWER-UPS & BONUS DROPS",
            align="center",
            font=("Courier", 12, "bold"),
        )

        pickups = (
            ("powerup_shield", "#38BDF8", "AEGIS SHIELD", "+1 Stackable Block", -235),
            ("powerup_vulcan", "#FACC15", "VULCAN CORE", "3-Way / 5-Way Spread", 0),
            ("powerup_crystal", "#C084FC", "AETHER CRYSTAL", "+10Pt Instant Bonus", 235),
        )
        for shape_key, color, title, desc, x_pos in pickups:
            self._stamp_sprite(shape_key, "circle", color, x_pos, -58)
            self._pen.color(color)
            self._pen.goto(x_pos, -92)
            self._pen.write(title, align="center", font=("Courier", 10, "bold"))
            self._pen.color("#CBD5E1")
            self._pen.goto(x_pos, -108)
            self._pen.write(desc, align="center", font=("Courier", 9, "normal"))

        self._draw_horizontal_divider(-132, color="#1E293B")

        self._pen.color("#94A3B8")
        self._pen.goto(0, -162)
        self._pen.write(
            "[A/D] or [◄/►] Move Starfighter   •   [SPACE] Fire   •   [P] Pause",
            align="center",
            font=("Courier", 10, "bold"),
        )
        self._pen.goto(0, -184)
        self._pen.write(
            "[1/2/3] Difficulty  •  [N] Account  •  [M] Home  •  [S] Mute  •  [Q] Quit",
            align="center",
            font=("Courier", 10, "normal"),
        )

        self._draw_horizontal_divider(-212, color="#334155")

        self._pen.color("#4ADE80")
        self._pen.goto(0, -248)
        self._pen.write(
            "[? / BACKSPACE] Back to Title Screen     |     [ENTER] Launch Mission",
            align="center",
            font=("Courier", 11, "bold"),
        )

    # ------------------------------------------------------------------
    # Top-10 Leaderboard View
    # ------------------------------------------------------------------
    def _render_leaderboard(self, leaderboard: List[Dict[str, Any]]) -> None:
        self._pen.color("#FACC15")
        self._pen.goto(0, 242)
        self._pen.write(
            "TOP-10 HIGH SCORES",
            align="center",
            font=("Courier", 24, "bold"),
        )

        self._pen.color("#38BDF8")
        self._pen.goto(0, 214)
        self._pen.write(
            "ASTRASEIGE HALL OF FAME",
            align="center",
            font=("Courier", 11, "bold"),
        )

        self._draw_horizontal_divider(195, color="#334155")

        header_row = (
            f"{'RANK':<6}{'PILOT':<18}{'SCORE':>9}{'WAVE':>8}{'MODE':>10}{'ACC':>8}"
        )
        self._pen.color("#94A3B8")
        self._pen.goto(0, 170)
        self._pen.write(
            header_row,
            align="center",
            font=("Courier", 11, "bold"),
        )

        self._draw_horizontal_divider(156, color="#1E293B")

        if not leaderboard:
            self._pen.color("#64748B")
            self._pen.goto(0, 20)
            self._pen.write(
                "NO FLIGHT RECORDS LOGGED YET",
                align="center",
                font=("Courier", 15, "bold"),
            )
            self._pen.goto(0, -12)
            self._pen.write(
                "Complete a mission to claim the #1 spot on the leaderboard!",
                align="center",
                font=("Courier", 11, "normal"),
            )
        else:
            medal_colors = {0: "#FACC15", 1: "#E2E8F0", 2: "#FB923C"}
            for idx, entry in enumerate(leaderboard[:10]):
                row_y = 128 - (idx * 31)
                rank_label = f"#{idx + 1}"
                pilot = str(entry.get("player_name", DEFAULT_PLAYER_NAME))[:16]
                score = int(entry.get("score", 0))
                wave = int(entry.get("wave", 1))
                mode = str(entry.get("difficulty", DEFAULT_DIFFICULTY)).upper()
                acc = f"{float(entry.get('accuracy', 0.0)):.1f}%"

                line = (
                    f"{rank_label:<6}{pilot:<18}{score:>9,}{wave:>8}{mode:>10}{acc:>8}"
                )
                self._pen.color(medal_colors.get(idx, "#CBD5E1"))
                self._pen.goto(0, row_y)
                self._pen.write(
                    line,
                    align="center",
                    font=("Courier", 11, "bold" if idx < 3 else "normal"),
                )

        self._draw_horizontal_divider(-212, color="#334155")

        self._pen.color("#4ADE80")
        self._pen.goto(0, -248)
        self._pen.write(
            "[H / BACKSPACE] Back to Title Screen     |     [ENTER] Launch Mission",
            align="center",
            font=("Courier", 11, "bold"),
        )