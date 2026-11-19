"""src/ui/hud.py

Live gameplay Heads-Up Display (HUD), live mission timer, stacked power-up
inventory counters, clickable [HOME] / [QUIT] action buttons, and playfield
boundary overlay for AstraSeige.
"""

import turtle
from typing import Any, Dict, Optional, Tuple

from config import (
    DEFENSE_LINE_Y,
    DIFFICULTY_SETTINGS,
    LEFT_BOUNDARY,
    MAX_WAVES,
    RIGHT_BOUNDARY,
)
from src.ui.pixel_sprites import resolve_pixel_sprite

DIFFICULTY_COLORS: Dict[str, str] = {
    "Easy": "#4ADE80",
    "Normal": "#38BDF8",
    "Hard": "#FB7185",
}

# Clickable bottom-bar button bounds: (center_x, center_y, width, height)
HOME_BUTTON_RECT: Tuple[float, float, float, float] = (-190.0, -302.0, 82.0, 22.0)
QUIT_BUTTON_RECT: Tuple[float, float, float, float] = (330.0, -302.0, 80.0, 22.0)


class HUD:
    """Renders real-time telemetry using isolated per-region pens to eliminate flicker."""

    def __init__(self) -> None:
        self._static_pen = self._make_pen()
        self._lives_pen = self._make_pen()
        self._wave_pen = self._make_pen()
        self._clock_pen = self._make_pen()
        self._score_pen = self._make_pen()
        self._powerup_pen = self._make_pen()
        self._status_pen = self._make_pen()
        self._boss_pen = self._make_pen()

        self._all_dynamic_pens = (
            self._lives_pen,
            self._wave_pen,
            self._clock_pen,
            self._score_pen,
            self._powerup_pen,
            self._status_pen,
            self._boss_pen,
        )

        self._visible: bool = False
        self._reset_snapshots()

    @staticmethod
    def _make_pen() -> turtle.Turtle:
        pen = turtle.Turtle(visible=False)
        pen.penup()
        pen.speed(0)
        return pen

    def _reset_snapshots(self) -> None:
        self._lives_snap: Optional[Tuple[Any, ...]] = None
        self._wave_snap: Optional[Tuple[Any, ...]] = None
        self._clock_snap: Optional[int] = None
        self._score_snap: Optional[Tuple[Any, ...]] = None
        self._powerup_snap: Optional[Tuple[Any, ...]] = None
        self._status_snap: Optional[Tuple[Any, ...]] = None
        self._boss_snap: Optional[float] = None

    # ------------------------------------------------------------------
    # Visibility & Frame Chrome
    # ------------------------------------------------------------------
    @staticmethod
    def _clear_pen(pen: turtle.Turtle) -> None:
        try:
            pen.clearstamps()
        except Exception:
            pass
        pen.clear()

    def _clear_all_dynamic(self) -> None:
        for pen in self._all_dynamic_pens:
            self._clear_pen(pen)

    def show(self) -> None:
        """Draws static arena dividers, action buttons, and resets dynamic caches."""
        self._visible = True
        self._reset_snapshots()
        self._draw_arena_frame()

    def hide(self) -> None:
        """Clears all HUD elements when leaving active gameplay screens."""
        self._visible = False
        self._reset_snapshots()
        self._static_pen.clear()
        self._clear_all_dynamic()

    def _draw_static_button(
        self,
        rect: Tuple[float, float, float, float],
        label: str,
        border_color: str,
        fill_color: str,
        text_color: str,
    ) -> None:
        cx, cy, width, height = rect
        left = cx - (width / 2.0)
        right = cx + (width / 2.0)
        top = cy + (height / 2.0)
        bottom = cy - (height / 2.0)

        self._static_pen.pensize(1)
        self._static_pen.color(border_color, fill_color)
        self._static_pen.goto(left, top)
        self._static_pen.pendown()
        self._static_pen.begin_fill()
        self._static_pen.goto(right, top)
        self._static_pen.goto(right, bottom)
        self._static_pen.goto(left, bottom)
        self._static_pen.goto(left, top)
        self._static_pen.end_fill()
        self._static_pen.penup()

        self._static_pen.color(text_color)
        self._static_pen.goto(cx, cy - 7)
        self._static_pen.write(label, align="center", font=("Courier", 9, "bold"))

    def _draw_arena_frame(self) -> None:
        """Draws the top/bottom HUD dividers, breach line, and [HOME]/[QUIT] buttons."""
        self._static_pen.clear()

        self._static_pen.color("#1E293B")
        self._static_pen.pensize(2)
        for border_y in (268, -284):
            self._static_pen.penup()
            self._static_pen.goto(LEFT_BOUNDARY - 5, border_y)
            self._static_pen.pendown()
            self._static_pen.goto(RIGHT_BOUNDARY + 5, border_y)
            self._static_pen.penup()

        self._static_pen.color("#475569")
        self._static_pen.pensize(1)
        dash_len = 14
        gap_len = 10
        cursor_x = float(LEFT_BOUNDARY)
        while cursor_x < RIGHT_BOUNDARY:
            seg_end = min(float(RIGHT_BOUNDARY), cursor_x + dash_len)
            self._static_pen.goto(cursor_x, DEFENSE_LINE_Y)
            self._static_pen.pendown()
            self._static_pen.goto(seg_end, DEFENSE_LINE_Y)
            self._static_pen.penup()
            cursor_x += dash_len + gap_len

        self._draw_static_button(
            rect=HOME_BUTTON_RECT,
            label="[M] HOME",
            border_color="#38BDF8",
            fill_color="#0C1E33",
            text_color="#38BDF8",
        )
        self._draw_static_button(
            rect=QUIT_BUTTON_RECT,
            label="[Q] QUIT",
            border_color="#FB7185",
            fill_color="#2A0D16",
            text_color="#FB7185",
        )

    # ------------------------------------------------------------------
    # Pixel Icon Stampers & Life Indicators
    # ------------------------------------------------------------------
    @staticmethod
    def _stamp_icon(
        pen: turtle.Turtle,
        shape_name: str,
        fallback_shape: str,
        color: str,
        x: float,
        y: float,
    ) -> bool:
        chosen = resolve_pixel_sprite(shape_name, fallback_shape)
        if chosen != shape_name:
            return False
        pen.shape(chosen)
        pen.color(color)
        pen.goto(x, y)
        try:
            pen.stamp()
            return True
        except Exception:
            return False

    def _draw_mini_ship_icon(
        self,
        center_x: float,
        center_y: float,
        active: bool = True,
    ) -> None:
        fill = "#22C55E" if active else "#1E293B"
        outline = "#4ADE80" if active else "#334155"

        if active and self._stamp_icon(
            self._lives_pen, "hud_mini_ship", "triangle", fill, center_x, center_y
        ):
            return

        self._lives_pen.pensize(1)
        self._lives_pen.color(outline, fill)
        self._lives_pen.goto(center_x, center_y + 8)
        self._lives_pen.pendown()
        self._lives_pen.begin_fill()
        self._lives_pen.goto(center_x - 8, center_y - 6)
        self._lives_pen.goto(center_x, center_y - 3)
        self._lives_pen.goto(center_x + 8, center_y - 6)
        self._lives_pen.goto(center_x, center_y + 8)
        self._lives_pen.end_fill()
        self._lives_pen.penup()

    def _draw_heart_icon(
        self,
        center_x: float,
        center_y: float,
        filled: bool = True,
    ) -> None:
        shape_key = "hud_heart_full" if filled else "hud_heart_empty"
        color = "#F43F5E" if filled else "#9D174D"
        if self._stamp_icon(
            self._lives_pen, shape_key, "circle", color, center_x, center_y
        ):
            return

        self._lives_pen.color(color)
        self._lives_pen.goto(center_x, center_y - 6)
        self._lives_pen.write(
            "♥" if filled else "♡",
            align="center",
            font=("Courier", 12, "bold"),
        )

    def _draw_boss_health_bar(self, hp_ratio: float) -> None:
        clamped = max(0.0, min(1.0, float(hp_ratio)))
        bar_w = 220.0
        bar_h = 8.0
        left = -bar_w / 2.0
        top = 262.0
        bottom = top - bar_h

        self._boss_pen.pensize(1)
        self._boss_pen.color("#F43F5E", "#1F0913")
        self._boss_pen.goto(left, top)
        self._boss_pen.pendown()
        self._boss_pen.begin_fill()
        self._boss_pen.goto(left + bar_w, top)
        self._boss_pen.goto(left + bar_w, bottom)
        self._boss_pen.goto(left, bottom)
        self._boss_pen.goto(left, top)
        self._boss_pen.end_fill()
        self._boss_pen.penup()

        if clamped > 0.0:
            fill_w = bar_w * clamped
            self._boss_pen.color("#FB7185", "#F43F5E")
            self._boss_pen.goto(left, top)
            self._boss_pen.pendown()
            self._boss_pen.begin_fill()
            self._boss_pen.goto(left + fill_w, top)
            self._boss_pen.goto(left + fill_w, bottom)
            self._boss_pen.goto(left, bottom)
            self._boss_pen.goto(left, top)
            self._boss_pen.end_fill()
            self._boss_pen.penup()

        self._boss_pen.color("#FDA4AF")
        self._boss_pen.goto(0, 241)
        self._boss_pen.write(
            "MOTHERSHIP DREADNOUGHT",
            align="center",
            font=("Courier", 8, "bold"),
        )

    @staticmethod
    def _format_clock(seconds: float) -> str:
        total_secs = max(0, int(seconds))
        mins, secs = divmod(total_secs, 60)
        return f"{mins:02d}:{secs:02d}"

    # ------------------------------------------------------------------
    # Dynamic Telemetry Update (Isolated Per-Region Redraws)
    # ------------------------------------------------------------------
    def update(
        self,
        session: Any,
        active_buffs: Optional[Dict[str, float]] = None,
        sound_enabled: bool = True,
        shield_charges: Optional[int] = None,
        vulcan_level: int = 1,
        crystals_collected: int = 0,
        boss_hp_ratio: Optional[float] = None,
        force: bool = False,
    ) -> None:
        """Redraws only the specific HUD regions whose values actually changed."""
        if not self._visible:
            return

        buffs = active_buffs or {}
        buff_items = tuple(sorted(buffs.items()))

        resolved_shields = shield_charges
        if resolved_shields is None:
            resolved_shields = 0
            for key, val in buffs.items():
                if key.startswith("SHIELD x"):
                    resolved_shields = int(val)
                    break

        # 1. Top-Left: Mini-Fighter Life Slots + Pixel Hearts
        max_slots = max(
            int(session.lives),
            DIFFICULTY_SETTINGS.get(str(session.difficulty), {}).get("starting_lives", 3),
        )
        max_slots = max(1, min(6, max_slots))
        current_lives = max(0, min(max_slots, int(session.lives)))
        lives_snap = (current_lives, max_slots)

        if force or lives_snap != self._lives_snap:
            self._lives_snap = lives_snap
            self._clear_pen(self._lives_pen)
            for idx in range(max_slots):
                slot_x = LEFT_BOUNDARY + 12 + (idx * 22)
                is_alive_slot = idx < current_lives
                self._draw_mini_ship_icon(center_x=slot_x, center_y=298, active=is_alive_slot)
                self._draw_heart_icon(center_x=slot_x, center_y=278, filled=is_alive_slot)

        # 2. Top-Center: Wave Progress & All-Time Best
        wave_snap = (
            int(session.wave),
            int(session.high_score),
            bool(session.is_new_high_score),
        )
        if force or wave_snap != self._wave_snap:
            self._wave_snap = wave_snap
            self._clear_pen(self._wave_pen)
            best_color = "#FACC15" if session.is_new_high_score else "#38BDF8"
            best_label = "NEW BEST" if session.is_new_high_score else "BEST"

            self._wave_pen.color("#E2E8F0")
            self._wave_pen.goto(0, 294)
            self._wave_pen.write(
                f"WAVE {session.wave:02d}/{MAX_WAVES:02d}",
                align="center",
                font=("Courier", 12, "bold"),
            )

            self._wave_pen.color(best_color)
            self._wave_pen.goto(0, 275)
            self._wave_pen.write(
                f"{best_label}: {session.high_score:06d}",
                align="center",
                font=("Courier", 10, "bold"),
            )

        # 3. Top-Center-Right: Live Mission Clock (Text-Only, Zero Stamps)
        elapsed_whole_sec = int(getattr(session, "elapsed_time_sec", 0.0))
        if force or elapsed_whole_sec != self._clock_snap:
            self._clock_snap = elapsed_whole_sec
            self._clock_pen.clear()
            self._clock_pen.color("#94A3B8")
            self._clock_pen.goto(152, 274)
            self._clock_pen.write(
                f"TIME {self._format_clock(elapsed_whole_sec)}",
                align="center",
                font=("Courier", 10, "bold"),
            )

        # 4. Top-Right: Gold Coin Icon + Neon Green Score Counter
        score_snap = (int(session.score), str(session.difficulty))
        if force or score_snap != self._score_snap:
            self._score_snap = score_snap
            self._clear_pen(self._score_pen)

            coin_x = RIGHT_BOUNDARY - 102
            if not self._stamp_icon(
                self._score_pen, "hud_coin", "circle", "#FACC15", coin_x, 299
            ):
                self._score_pen.color("#FACC15")
                self._score_pen.goto(coin_x, 291)
                self._score_pen.write("●", align="center", font=("Courier", 14, "bold"))

            self._score_pen.color("#22C55E")
            self._score_pen.goto(RIGHT_BOUNDARY, 291)
            self._score_pen.write(
                f"{session.score:06d}",
                align="right",
                font=("Courier", 15, "bold"),
            )

            diff_label = str(session.difficulty)
            diff_color = DIFFICULTY_COLORS.get(diff_label, "#38BDF8")
            self._score_pen.color(diff_color)
            self._score_pen.goto(RIGHT_BOUNDARY, 274)
            self._score_pen.write(
                f"MODE: {diff_label.upper()}",
                align="right",
                font=("Courier", 10, "bold"),
            )

        # 5. Mothership Boss Integrity Bar
        boss_pct = round(boss_hp_ratio, 2) if boss_hp_ratio is not None else None
        if force or boss_pct != self._boss_snap:
            self._boss_snap = boss_pct
            self._clear_pen(self._boss_pen)
            if boss_pct is not None:
                self._draw_boss_health_bar(boss_pct)

        # 6. Right-Side Stacked Power-Up Inventory Readout
        powerup_snap = (
            int(resolved_shields),
            int(vulcan_level),
            int(crystals_collected),
        )
        if force or powerup_snap != self._powerup_snap:
            self._powerup_snap = powerup_snap
            self._clear_pen(self._powerup_pen)

            badge_icon_x = RIGHT_BOUNDARY - 16
            badge_text_x = RIGHT_BOUNDARY - 36

            shield_color = "#38BDF8" if resolved_shields > 0 else "#64748B"
            self._powerup_pen.color(shield_color)
            self._powerup_pen.goto(badge_text_x, 232)
            self._powerup_pen.write(
                f"{resolved_shields} x",
                align="right",
                font=("Courier", 12, "bold"),
            )
            if not self._stamp_icon(
                self._powerup_pen,
                "powerup_shield",
                "circle",
                shield_color,
                badge_icon_x,
                240,
            ):
                self._powerup_pen.goto(badge_icon_x, 232)
                self._powerup_pen.write("◈", align="center", font=("Courier", 13, "bold"))

            vulcan_color = "#FACC15" if vulcan_level > 1 else "#94A3B8"
            self._powerup_pen.color(vulcan_color)
            self._powerup_pen.goto(badge_text_x, 200)
            self._powerup_pen.write(
                f"LV{max(1, int(vulcan_level))}",
                align="right",
                font=("Courier", 12, "bold"),
            )
            if not self._stamp_icon(
                self._powerup_pen,
                "powerup_vulcan",
                "square",
                vulcan_color,
                badge_icon_x,
                208,
            ):
                self._powerup_pen.goto(badge_icon_x, 200)
                self._powerup_pen.write("✦", align="center", font=("Courier", 13, "bold"))

            crystal_color = "#C084FC" if crystals_collected > 0 else "#64748B"
            crystal_label = (
                f"+10Pt ({crystals_collected})" if crystals_collected > 0 else "+10Pt"
            )
            self._powerup_pen.color(crystal_color)
            self._powerup_pen.goto(badge_text_x, 168)
            self._powerup_pen.write(
                crystal_label,
                align="right",
                font=("Courier", 11, "bold"),
            )
            if not self._stamp_icon(
                self._powerup_pen,
                "powerup_crystal",
                "triangle",
                crystal_color,
                badge_icon_x,
                176,
            ):
                self._powerup_pen.goto(badge_icon_x, 168)
                self._powerup_pen.write("◆", align="center", font=("Courier", 13, "bold"))

        # 7. Bottom Status Strip: Pilot, Buffs & Sound/Pause Prompts
        status_snap = (
            str(session.player_name),
            buff_items,
            bool(sound_enabled),
            int(vulcan_level),
        )
        if force or status_snap != self._status_snap:
            self._status_snap = status_snap
            self._clear_pen(self._status_pen)

            pilot_short = str(session.player_name)[:11]
            self._status_pen.color("#94A3B8")
            self._status_pen.goto(LEFT_BOUNDARY, -308)
            self._status_pen.write(
                f"PILOT: {pilot_short}",
                align="left",
                font=("Courier", 9, "bold"),
            )

            if buff_items:
                parts = []
                for name, secs in buff_items:
                    if name.startswith("SHIELD x") or name.startswith("VULCAN LV"):
                        parts.append(name)
                    else:
                        parts.append(f"{name}: {secs:.1f}s")
                buff_banner = " | ".join(parts)
                banner_color = "#FACC15" if vulcan_level > 1 else "#38BDF8"
                self._status_pen.color(banner_color)
                self._status_pen.goto(25, -308)
                self._status_pen.write(
                    buff_banner,
                    align="center",
                    font=("Courier", 9, "bold"),
                )
            else:
                self._status_pen.color("#64748B")
                self._status_pen.goto(25, -308)
                self._status_pen.write(
                    "◄/► MOVE • SPACE FIRE",
                    align="center",
                    font=("Courier", 9, "normal"),
                )

            sfx_status = "ON" if sound_enabled else "OFF"
            self._status_pen.color("#94A3B8")
            self._status_pen.goto(282, -308)
            self._status_pen.write(
                f"[S]{sfx_status} [P]PAUSE",
                align="right",
                font=("Courier", 9, "normal"),
            )