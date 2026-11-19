"""src/game/game_state.py

Operational game states and live session telemetry model for AstraSeige.
"""

from enum import Enum
from typing import Any, Dict, Optional

from config import DEFAULT_DIFFICULTY, DEFAULT_PLAYER_NAME, DIFFICULTY_SETTINGS


class GameState(Enum):
    """Represents the active screen or operational mode of the application."""

    MENU = "MENU"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"
    VICTORY = "VICTORY"


class GameSession:
    """Encapsulates all runtime metrics and player statistics for a single play session."""

    def __init__(
        self,
        player_name: str = DEFAULT_PLAYER_NAME,
        difficulty: str = DEFAULT_DIFFICULTY,
        high_score: int = 0,
    ) -> None:
        self.player_name: str = player_name.strip() or DEFAULT_PLAYER_NAME
        self.difficulty: str = (
            difficulty if difficulty in DIFFICULTY_SETTINGS else DEFAULT_DIFFICULTY
        )
        self.state: GameState = GameState.MENU
        self.high_score: int = max(0, int(high_score))

        # Per-run metrics initialized via reset()
        self.score: int = 0
        self.lives: int = DIFFICULTY_SETTINGS[self.difficulty]["starting_lives"]
        self.wave: int = 1
        self.highest_wave: int = 1
        self.shots_fired: int = 0
        self.hits: int = 0
        self.enemies_destroyed: int = 0
        self.elapsed_time_sec: float = 0.0
        self.is_new_high_score: bool = False
        self.leaderboard_rank: int = 0

    def set_player_name(self, player_name: str) -> None:
        """Updates and sanitizes the active pilot callsign."""
        cleaned = (player_name or "").strip()
        self.player_name = cleaned[:16] if cleaned else DEFAULT_PLAYER_NAME

    def set_difficulty(self, difficulty: str) -> None:
        """Updates the selected difficulty preset and syncs starting lives."""
        if difficulty in DIFFICULTY_SETTINGS:
            self.difficulty = difficulty
            self.lives = DIFFICULTY_SETTINGS[difficulty]["starting_lives"]

    def reset(self, difficulty: Optional[str] = None) -> None:
        """Resets all per-run counters while preserving player name and high score."""
        if difficulty is not None and difficulty in DIFFICULTY_SETTINGS:
            self.difficulty = difficulty

        preset = DIFFICULTY_SETTINGS[self.difficulty]
        self.score = 0
        self.lives = preset["starting_lives"]
        self.wave = 1
        self.highest_wave = 1
        self.shots_fired = 0
        self.hits = 0
        self.enemies_destroyed = 0
        self.elapsed_time_sec = 0.0
        self.is_new_high_score = False
        self.leaderboard_rank = 0

    def add_play_time(self, dt_sec: float) -> None:
        """Accumulates active gameplay duration in seconds (excludes pauses)."""
        if dt_sec > 0.0:
            self.elapsed_time_sec += float(dt_sec)

    @staticmethod
    def format_duration(seconds: Optional[float]) -> str:
        """Formats elapsed seconds as MM:SS.d."""
        if seconds is None or seconds <= 0.0:
            return "00:00.0"
        total_tenths = int(round(float(seconds) * 10))
        minutes, rem_tenths = divmod(total_tenths, 600)
        secs = rem_tenths / 10.0
        return f"{minutes:02d}:{secs:04.1f}"

    def record_shot(self) -> None:
        self.shots_fired += 1

    def record_hit(self) -> None:
        self.hits += 1

    def record_kill(self, points: int) -> None:
        self.enemies_destroyed += 1
        self.score += max(0, int(points))
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high_score = True

    def advance_wave(self) -> None:
        self.wave += 1
        if self.wave > self.highest_wave:
            self.highest_wave = self.wave

    def lose_life(self) -> int:
        self.lives = max(0, self.lives - 1)
        return self.lives

    @property
    def shots_hit(self) -> int:
        return self.hits

    @property
    def accuracy(self) -> float:
        if self.shots_fired == 0:
            return 0.0
        return round((self.hits / self.shots_fired) * 100.0, 1)

    def get_summary(self) -> Dict[str, Any]:
        """Returns a structured dictionary of session telemetry for UI screens and storage."""
        return {
            "player_name": self.player_name,
            "score": self.score,
            "high_score": self.high_score,
            "is_new_high_score": self.is_new_high_score,
            "leaderboard_rank": self.leaderboard_rank,
            "wave": self.wave,
            "highest_wave": self.highest_wave,
            "enemies_destroyed": self.enemies_destroyed,
            "shots_fired": self.shots_fired,
            "hits": self.hits,
            "accuracy": self.accuracy,
            "difficulty": self.difficulty,
            "elapsed_time_sec": round(self.elapsed_time_sec, 2),
            "formatted_time": self.format_duration(self.elapsed_time_sec),
        }