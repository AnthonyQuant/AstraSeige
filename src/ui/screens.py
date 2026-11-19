"""src/ui/screens.py

Modal overlay and end-of-run screen renderers (Pause, Wave Intermission,
Game Over, and Victory debrief screens) for AstraSeige.
"""

import turtle
from typing import Any, Dict, Optional

from config import DEFAULT_DIFFICULTY, DEFAULT_PLAYER_NAME, MAX_WAVES


class Screens:
    """Renders non-gameplay overlays and post-mission debrief screens."""

    def __init__(self) -> None:
        self._pen = turtle.Turtle(visible=False)
        self._pen.penup()
        self._pen.speed(0)
        self.is_visible: bool = False

    def hide(self) -> None:
        self.is_visible = False
        self._pen.clear()

    def _draw_panel(
        self,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        border_color: str,
        fill_color: str = "#0F172A",
        line_width: int = 2,
    ) -> None:
        half_w = width / 2.0
        half_h = height / 2.0
        left = center_x - half_w
        right = center_x + half_w
        top = center_y + half_h
        bottom = center_y - half_h

        self._pen.pensize(line_width)
        self._pen.color(border_color, fill_color)
        self._pen.goto(left, top)
        self._pen.pendown()
        self._pen.begin_fill()
        self._pen.goto(right, top)
        self._pen.goto(right, bottom)
        self._pen.goto(left, bottom)
        self._pen.goto(left, top)
        self._pen.end_fill()
        self._pen.penup()

    def _draw_rule(self, y: float, half_width: float, color: str = "#1E293B") -> None:
        self._pen.pensize(1)
        self._pen.color(color)
        self._pen.goto(-half_width, y)
        self._pen.pendown()
        self._pen.goto(half_width, y)
        self._pen.penup()

    def show_wave_banner(
        self,
        cleared_wave: int,
        bonus: int,
        next_wave: int,
        wave_title: str,
    ) -> None:
        self.is_visible = True
        self._pen.clear()

        self._draw_panel(
            center_x=0,
            center_y=12,
            width=490,
            height=104,
            border_color="#38BDF8",
            fill_color="#0F172A",
            line_width=2,
        )

        self._pen.color("#4ADE80")
        self._pen.goto(0, 26)
        self._pen.write(
            f"WAVE {cleared_wave} CLEARED!   (+{bonus} PTS)",
            align="center",
            font=("Courier", 16, "bold"),
        )

        self._pen.color("#E2E8F0")
        self._pen.goto(0, -14)
        self._pen.write(
            f"INCOMING WAVE {next_wave}/{MAX_WAVES}: {wave_title}",
            align="center",
            font=("Courier", 12, "bold"),
        )

    def show_pause(self, session: Any) -> None:
        self.is_visible = True
        self._pen.clear()

        self._draw_panel(
            center_x=0,
            center_y=10,
            width=460,
            height=265,
            border_color="#38BDF8",
            fill_color="#0F172A",
            line_width=3,
        )

        self._pen.color("#38BDF8")
        self._pen.goto(0, 96)
        self._pen.write(
            "GAME PAUSED",
            align="center",
            font=("Courier", 24, "bold"),
        )

        self._draw_rule(78, half_width=195, color="#1E293B")

        score = int(getattr(session, "score", 0))
        wave = int(getattr(session, "wave", 1))
        difficulty = str(getattr(session, "difficulty", DEFAULT_DIFFICULTY)).upper()

        self._pen.color("#E2E8F0")
        self._pen.goto(0, 46)
        self._pen.write(
            f"WAVE {wave:02d}/{MAX_WAVES:02d}   •   SCORE: {score:06d}   •   {difficulty}",
            align="center",
            font=("Courier", 11, "bold"),
        )

        self._draw_rule(26, half_width=195, color="#1E293B")

        controls = (
            ("[P]", "Resume Mission", "#4ADE80"),
            ("[R]", "Restart Campaign", "#FACC15"),
            ("[M]", "Return to Home Screen", "#38BDF8"),
            ("[Q / ESC]", "Quit Game", "#FB7185"),
        )
        for idx, (key_label, action_label, accent) in enumerate(controls):
            row_y = -6 - (idx * 28)
            self._pen.color(accent)
            self._pen.goto(-145, row_y)
            self._pen.write(
                f"{key_label:<9}",
                align="left",
                font=("Courier", 12, "bold"),
            )
            self._pen.color("#CBD5E1")
            self._pen.goto(-45, row_y)
            self._pen.write(
                action_label,
                align="left",
                font=("Courier", 12, "normal"),
            )

    def show_game_over(
        self,
        summary: Dict[str, Any],
        reason: str = "FLEET OVERWHELMED DEFENSES",
        pilot_profile: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._render_end_screen(
            summary=summary,
            title="GAME OVER",
            subtitle=reason,
            accent_color="#FB7185",
            panel_fill="#0F172A",
            replay_prompt="[R / ENTER] Try Again",
            pilot_profile=pilot_profile,
        )

    def show_victory(
        self,
        summary: Dict[str, Any],
        reason: str = "GALACTIC ARMADA DEFEATED!",
        pilot_profile: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._render_end_screen(
            summary=summary,
            title="VICTORY!",
            subtitle=reason,
            accent_color="#4ADE80",
            panel_fill="#0B1914",
            replay_prompt="[R / ENTER] Play Again",
            pilot_profile=pilot_profile,
        )

    def _render_end_screen(
        self,
        summary: Dict[str, Any],
        title: str,
        subtitle: str,
        accent_color: str,
        panel_fill: str,
        replay_prompt: str,
        pilot_profile: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.is_visible = True
        self._pen.clear()

        self._draw_panel(
            center_x=0,
            center_y=0,
            width=600,
            height=485,
            border_color=accent_color,
            fill_color=panel_fill,
            line_width=3,
        )

        self._pen.color(accent_color)
        self._pen.goto(0, 188)
        self._pen.write(
            title,
            align="center",
            font=("Courier", 30, "bold"),
        )

        self._pen.color("#E2E8F0")
        self._pen.goto(0, 158)
        self._pen.write(
            subtitle.upper(),
            align="center",
            font=("Courier", 12, "bold"),
        )

        is_new_best = bool(summary.get("is_new_high_score", False))
        rank = int(summary.get("leaderboard_rank", 0))
        callout_text: Optional[str] = None
        if is_new_best and rank > 0:
            callout_text = f"★ NEW ALL-TIME RECORD  •  LEADERBOARD RANK #{rank} ★"
        elif is_new_best:
            callout_text = "★ NEW ALL-TIME HIGH SCORE! ★"
        elif rank > 0:
            callout_text = f"★ QUALIFIED FOR TOP-10 LEADERBOARD: RANK #{rank} ★"

        if callout_text:
            self._pen.color("#FACC15")
            self._pen.goto(0, 130)
            self._pen.write(
                callout_text,
                align="center",
                font=("Courier", 11, "bold"),
            )

        self._draw_rule(114, half_width=260, color="#334155")

        pilot = str(summary.get("player_name", DEFAULT_PLAYER_NAME))
        difficulty = str(summary.get("difficulty", DEFAULT_DIFFICULTY)).upper()
        score = int(summary.get("score", 0))
        wave = int(summary.get("wave", 1))
        kills = int(summary.get("enemies_destroyed", 0))
        shots_fired = int(summary.get("shots_fired", 0))
        hits = int(summary.get("hits", 0))
        accuracy = float(summary.get("accuracy", 0.0))
        mission_time = str(summary.get("formatted_time", "00:00.0"))

        stats_rows = (
            ("PILOT / MODE", f"{pilot}  ({difficulty})", "#CBD5E1"),
            ("FINAL SCORE", f"{score:,}", "#FACC15"),
            ("MISSION TIME", mission_time, "#38BDF8"),
            ("WAVE REACHED", f"{wave} / {MAX_WAVES}", "#E2E8F0"),
            ("INVADERS DESTROYED", f"{kills}", "#4ADE80"),
            ("FIRING ACCURACY", f"{accuracy:.1f}%  ({hits}/{shots_fired} HITS)", "#E2E8F0"),
        )

        for idx, (label, value, val_color) in enumerate(stats_rows):
            row_y = 84 - (idx * 28)
            self._pen.color("#94A3B8")
            self._pen.goto(-235, row_y)
            self._pen.write(
                label,
                align="left",
                font=("Courier", 11, "bold"),
            )
            self._pen.color(val_color)
            self._pen.goto(235, row_y)
            self._pen.write(
                value,
                align="right",
                font=("Courier", 12, "bold"),
            )

        # Pilot Career SQLite Summary Box
        profile = pilot_profile or {}
        p_best = int(profile.get("high_score", max(score, int(summary.get("high_score", 0)))))
        p_time = str(profile.get("best_time_formatted", "--:--"))
        p_wave = int(profile.get("highest_wave", wave))
        p_games = int(profile.get("games_played", 1))

        self._draw_panel(
            center_x=0,
            center_y=-114,
            width=520,
            height=46,
            border_color="#1E293B",
            fill_color="#070D19",
            line_width=1,
        )
        self._pen.color("#38BDF8")
        self._pen.goto(0, -106)
        self._pen.write(
            f"PILOT CAREER ({pilot.upper()})",
            align="center",
            font=("Courier", 9, "bold"),
        )
        self._pen.color("#E2E8F0")
        self._pen.goto(0, -126)
        self._pen.write(
            f"BEST: {p_best:,}  •  BEST TIME: {p_time}  •  STAGE: {p_wave}/{MAX_WAVES}  •  GAMES: {p_games}",
            align="center",
            font=("Courier", 10, "bold"),
        )

        self._draw_rule(-154, half_width=260, color="#334155")

        self._pen.color("#4ADE80")
        self._pen.goto(0, -192)
        self._pen.write(
            f"{replay_prompt}     |     [M] Home     |     [Q / ESC] Quit",
            align="center",
            font=("Courier", 11, "bold"),
        )