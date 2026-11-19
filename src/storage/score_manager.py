"""src/storage/score_manager.py

Persistent storage engine managing:
1. Per-pilot SQLite database (`data/astraseige.db`) tracking high score, best
   completion/survival time, highest stage reached, and total games played.
2. Global JSON Top-10 high-score leaderboard (`data/high_scores.json`).
3. Append-only CSV session telemetry history (`data/game_history.csv`).
"""

import csv
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from config import (
    DATABASE_FILE,
    DEFAULT_DIFFICULTY,
    DEFAULT_PLAYER_NAME,
    GAME_HISTORY_FILE,
    HIGH_SCORES_FILE,
)


class ScoreManager:
    """Handles SQLite per-pilot profiles, JSON Top-10 scores, and CSV match logs."""

    CSV_HEADERS: Tuple[str, ...] = (
        "timestamp",
        "player_name",
        "difficulty",
        "outcome",
        "score",
        "wave",
        "enemies_destroyed",
        "shots_fired",
        "shots_hit",
        "accuracy",
    )

    def __init__(
        self,
        high_scores_path: Path = HIGH_SCORES_FILE,
        history_path: Path = GAME_HISTORY_FILE,
        max_entries: int = 10,
        db_path: Optional[Path] = None,
    ) -> None:
        self.high_scores_path: Path = Path(high_scores_path)
        self.history_path: Path = Path(history_path)
        self.max_entries: int = max(1, int(max_entries))

        if db_path is not None:
            self.db_path: Path = Path(db_path)
        elif self.high_scores_path == Path(HIGH_SCORES_FILE):
            self.db_path = Path(DATABASE_FILE)
        else:
            self.db_path = self.high_scores_path.parent / "astraseige.db"

        self._ensure_storage_dirs()
        self._init_database()

    def _ensure_storage_dirs(self) -> None:
        """Creates parent data directories if they do not yet exist."""
        try:
            self.high_scores_path.parent.mkdir(parents=True, exist_ok=True)
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    @staticmethod
    def _sanitize_name(player_name: Optional[str]) -> str:
        """Normalizes and bounds player callsigns for clean storage and UI rendering."""
        cleaned = (player_name or "").strip()
        if not cleaned:
            return DEFAULT_PLAYER_NAME
        return cleaned[:16]

    @staticmethod
    def format_duration(seconds: Optional[float]) -> str:
        """Formats elapsed seconds as MM:SS.d (or '--:--' when unset)."""
        if seconds is None or seconds <= 0:
            return "--:--"
        total_tenths = int(round(float(seconds) * 10))
        minutes, rem_tenths = divmod(total_tenths, 600)
        secs = rem_tenths / 10.0
        return f"{minutes:02d}:{secs:04.1f}"

    # ------------------------------------------------------------------
    # SQLite Per-Pilot Career Database
    # ------------------------------------------------------------------
    def _connect_db(self) -> sqlite3.Connection:
        """Opens a SQLite connection with Row access enabled."""
        self._ensure_storage_dirs()
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Creates `pilot_profiles` and migrates `best_survival_sec` if needed."""
        try:
            with self._connect_db() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pilot_profiles (
                        pilot_key TEXT PRIMARY KEY,
                        player_name TEXT NOT NULL,
                        high_score INTEGER NOT NULL DEFAULT 0,
                        best_time_sec REAL,
                        best_survival_sec REAL,
                        highest_wave INTEGER NOT NULL DEFAULT 0,
                        games_played INTEGER NOT NULL DEFAULT 0,
                        victories INTEGER NOT NULL DEFAULT 0,
                        total_kills INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                try:
                    conn.execute(
                        "ALTER TABLE pilot_profiles ADD COLUMN best_survival_sec REAL"
                    )
                except sqlite3.OperationalError:
                    pass
        except sqlite3.Error:
            pass

    def _resolve_display_time(
        self,
        best_victory_sec: Optional[float],
        best_survival_sec: Optional[float],
    ) -> Tuple[Optional[float], str]:
        """Returns fastest victory clear time if available, else longest survival time."""
        if best_victory_sec is not None and best_victory_sec > 0:
            return best_victory_sec, self.format_duration(best_victory_sec)
        if best_survival_sec is not None and best_survival_sec > 0:
            return best_survival_sec, self.format_duration(best_survival_sec)
        return None, "--:--"

    def _row_to_profile(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Converts a SQLite row into a normalized pilot career dictionary."""
        raw_victory = row["best_time_sec"]
        victory_val = float(raw_victory) if raw_victory is not None else None

        raw_survival = (
            row["best_survival_sec"] if "best_survival_sec" in row.keys() else None
        )
        survival_val = float(raw_survival) if raw_survival is not None else None

        effective_sec, formatted_time = self._resolve_display_time(
            victory_val, survival_val
        )

        return {
            "player_name": str(row["player_name"]),
            "high_score": int(row["high_score"]),
            "best_time_sec": effective_sec,
            "best_victory_sec": victory_val,
            "best_survival_sec": survival_val,
            "best_time_formatted": formatted_time,
            "highest_wave": int(row["highest_wave"]),
            "games_played": int(row["games_played"]),
            "victories": int(row["victories"]),
            "total_kills": int(row["total_kills"]),
            "updated_at": str(row["updated_at"]),
        }

    def pilot_exists(self, player_name: str) -> bool:
        """Returns True if an account with `player_name` already exists in SQLite."""
        clean_name = self._sanitize_name(player_name)
        pilot_key = clean_name.lower()
        try:
            with self._connect_db() as conn:
                row = conn.execute(
                    "SELECT 1 FROM pilot_profiles WHERE pilot_key = ?",
                    (pilot_key,),
                ).fetchone()
                return row is not None
        except sqlite3.Error:
            return False

    def register_pilot(self, player_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Creates a new pilot account if not already present; returns (created, profile)."""
        clean_name = self._sanitize_name(player_name)
        pilot_key = clean_name.lower()

        if self.pilot_exists(clean_name):
            return False, self.get_pilot_profile(clean_name)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._connect_db() as conn:
                conn.execute(
                    """
                    INSERT INTO pilot_profiles (
                        pilot_key,
                        player_name,
                        high_score,
                        best_time_sec,
                        best_survival_sec,
                        highest_wave,
                        games_played,
                        victories,
                        total_kills,
                        updated_at
                    )
                    VALUES (?, ?, 0, NULL, NULL, 0, 0, 0, 0, ?)
                    """,
                    (pilot_key, clean_name, now_str),
                )
        except sqlite3.Error:
            pass

        return True, self.get_pilot_profile(clean_name)

    def get_pilot_profile(self, player_name: str) -> Dict[str, Any]:
        """Fetches the career stats for `player_name`, returning zeroed defaults if new."""
        clean_name = self._sanitize_name(player_name)
        pilot_key = clean_name.lower()

        try:
            with self._connect_db() as conn:
                row = conn.execute(
                    "SELECT * FROM pilot_profiles WHERE pilot_key = ?",
                    (pilot_key,),
                ).fetchone()
                if row is not None:
                    return self._row_to_profile(row)
        except sqlite3.Error:
            pass

        return {
            "player_name": clean_name,
            "high_score": 0,
            "best_time_sec": None,
            "best_victory_sec": None,
            "best_survival_sec": None,
            "best_time_formatted": "--:--",
            "highest_wave": 0,
            "games_played": 0,
            "victories": 0,
            "total_kills": 0,
            "updated_at": "",
        }

    def update_pilot_profile(
        self,
        player_name: str,
        score: int,
        wave: int,
        elapsed_time_sec: float = 0.0,
        outcome: str = "GAME_OVER",
        enemies_destroyed: int = 0,
    ) -> Dict[str, Any]:
        """Upserts a pilot's high score, best clear/survival time, max stage, and games."""
        clean_name = self._sanitize_name(player_name)
        pilot_key = clean_name.lower()
        existing = self.get_pilot_profile(clean_name)

        new_high_score = max(existing["high_score"], max(0, int(score)))
        new_highest_wave = max(existing["highest_wave"], max(1, int(wave)))
        new_games_played = existing["games_played"] + 1
        is_victory = str(outcome).upper() == "VICTORY"
        new_victories = existing["victories"] + (1 if is_victory else 0)
        new_total_kills = existing["total_kills"] + max(0, int(enemies_destroyed))

        best_victory_sec: Optional[float] = existing.get("best_victory_sec")
        best_survival_sec: Optional[float] = existing.get("best_survival_sec")
        run_time = round(max(0.0, float(elapsed_time_sec)), 2)

        if run_time > 0.0:
            if best_survival_sec is None or run_time > best_survival_sec:
                best_survival_sec = run_time
            if is_victory and (
                best_victory_sec is None or run_time < best_victory_sec
            ):
                best_victory_sec = run_time

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._connect_db() as conn:
                conn.execute(
                    """
                    INSERT INTO pilot_profiles (
                        pilot_key,
                        player_name,
                        high_score,
                        best_time_sec,
                        best_survival_sec,
                        highest_wave,
                        games_played,
                        victories,
                        total_kills,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pilot_key) DO UPDATE SET
                        player_name = excluded.player_name,
                        high_score = excluded.high_score,
                        best_time_sec = excluded.best_time_sec,
                        best_survival_sec = excluded.best_survival_sec,
                        highest_wave = excluded.highest_wave,
                        games_played = excluded.games_played,
                        victories = excluded.victories,
                        total_kills = excluded.total_kills,
                        updated_at = excluded.updated_at
                    """,
                    (
                        pilot_key,
                        clean_name,
                        new_high_score,
                        best_victory_sec,
                        best_survival_sec,
                        new_highest_wave,
                        new_games_played,
                        new_victories,
                        new_total_kills,
                        now_str,
                    ),
                )
        except sqlite3.Error:
            pass

        effective_sec, formatted_time = self._resolve_display_time(
            best_victory_sec, best_survival_sec
        )

        return {
            "player_name": clean_name,
            "high_score": new_high_score,
            "best_time_sec": effective_sec,
            "best_victory_sec": best_victory_sec,
            "best_survival_sec": best_survival_sec,
            "best_time_formatted": formatted_time,
            "highest_wave": new_highest_wave,
            "games_played": new_games_played,
            "victories": new_victories,
            "total_kills": new_total_kills,
            "updated_at": now_str,
        }

    def get_all_pilot_profiles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns up to `limit` pilot career records sorted by high score and recency."""
        try:
            with self._connect_db() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM pilot_profiles
                    ORDER BY
                        high_score DESC,
                        highest_wave DESC,
                        updated_at DESC
                    LIMIT ?
                    """,
                    (max(1, int(limit)),),
                ).fetchall()
                return [self._row_to_profile(row) for row in rows]
        except sqlite3.Error:
            return []

    # ------------------------------------------------------------------
    # JSON Top-10 High-Score Leaderboard
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_score_entry(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None
        try:
            score = int(raw.get("score", 0))
            if score <= 0:
                return None

            return {
                "player_name": ScoreManager._sanitize_name(
                    str(raw.get("player_name", DEFAULT_PLAYER_NAME))
                ),
                "score": score,
                "wave": max(1, int(raw.get("wave", 1))),
                "difficulty": str(raw.get("difficulty", DEFAULT_DIFFICULTY)),
                "enemies_destroyed": max(0, int(raw.get("enemies_destroyed", 0))),
                "accuracy": round(float(raw.get("accuracy", 0.0)), 1),
                "timestamp": str(raw.get("timestamp", "")),
            }
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _sort_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            entries,
            key=lambda item: (
                item["score"],
                item["wave"],
                item["accuracy"],
            ),
            reverse=True,
        )

    def load_high_scores(self) -> List[Dict[str, Any]]:
        if not self.high_scores_path.exists():
            return []

        try:
            with self.high_scores_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(payload, list):
            return []

        valid_entries: List[Dict[str, Any]] = []
        for item in payload:
            normalized = self._normalize_score_entry(item)
            if normalized is not None:
                valid_entries.append(normalized)

        return self._sort_entries(valid_entries)[: self.max_entries]

    def _save_high_scores(self, entries: List[Dict[str, Any]]) -> bool:
        self._ensure_storage_dirs()
        trimmed = self._sort_entries(entries)[: self.max_entries]
        try:
            with self.high_scores_path.open("w", encoding="utf-8") as handle:
                json.dump(trimmed, handle, indent=2)
            return True
        except OSError:
            return False

    def get_top_score(self) -> int:
        scores = self.load_high_scores()
        return scores[0]["score"] if scores else 0

    def is_high_score(self, score: int) -> bool:
        if score <= 0:
            return False

        scores = self.load_high_scores()
        if len(scores) < self.max_entries:
            return True
        return score > scores[-1]["score"]

    def record_high_score(
        self,
        player_name: str,
        score: int,
        wave: int,
        difficulty: str = DEFAULT_DIFFICULTY,
        enemies_destroyed: int = 0,
        accuracy: float = 0.0,
    ) -> Tuple[bool, int]:
        numeric_score = int(score)
        if numeric_score <= 0:
            return False, 0

        entries = self.load_high_scores()
        new_entry: Dict[str, Any] = {
            "player_name": self._sanitize_name(player_name),
            "score": numeric_score,
            "wave": max(1, int(wave)),
            "difficulty": difficulty or DEFAULT_DIFFICULTY,
            "enemies_destroyed": max(0, int(enemies_destroyed)),
            "accuracy": round(float(accuracy), 1),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        combined = self._sort_entries(entries + [new_entry])[: self.max_entries]
        if new_entry not in combined:
            return False, 0

        rank = combined.index(new_entry) + 1
        self._save_high_scores(combined)
        return True, rank

    def reset_leaderboard(self) -> None:
        self._save_high_scores([])

    # ------------------------------------------------------------------
    # CSV Session Telemetry History
    # ------------------------------------------------------------------
    def log_game_history(
        self,
        player_name: str,
        difficulty: str,
        outcome: str,
        score: int,
        wave: int,
        enemies_destroyed: int,
        shots_fired: int,
        shots_hit: int,
        accuracy: float,
    ) -> bool:
        self._ensure_storage_dirs()
        write_header = (
            not self.history_path.exists() or self.history_path.stat().st_size == 0
        )

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self._sanitize_name(player_name),
            difficulty or DEFAULT_DIFFICULTY,
            str(outcome).upper(),
            int(score),
            max(1, int(wave)),
            max(0, int(enemies_destroyed)),
            max(0, int(shots_fired)),
            max(0, int(shots_hit)),
            round(float(accuracy), 1),
        ]

        try:
            with self.history_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if write_header:
                    writer.writerow(self.CSV_HEADERS)
                writer.writerow(row)
            return True
        except OSError:
            return False

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, str]]:
        if not self.history_path.exists():
            return []

        try:
            with self.history_path.open("r", newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
            return rows[-max(1, int(limit)) :][::-1]
        except OSError:
            return []

    def record_session(
        self,
        session: Any,
        outcome: Optional[str] = None,
    ) -> Tuple[bool, int]:
        """Updates the pilot's SQLite profile, logs CSV history, and updates Top-10 JSON."""
        resolved_outcome = outcome
        if resolved_outcome is None:
            state = getattr(session, "state", None)
            resolved_outcome = getattr(state, "value", str(state or "UNKNOWN"))

        player_name = str(getattr(session, "player_name", DEFAULT_PLAYER_NAME))
        difficulty = str(getattr(session, "difficulty", DEFAULT_DIFFICULTY))
        score = int(getattr(session, "score", 0))
        wave = int(getattr(session, "wave", 1))
        enemies_destroyed = int(getattr(session, "enemies_destroyed", 0))
        shots_fired = int(getattr(session, "shots_fired", 0))
        shots_hit = int(getattr(session, "shots_hit", 0))
        accuracy = float(getattr(session, "accuracy", 0.0))
        elapsed_time_sec = float(getattr(session, "elapsed_time_sec", 0.0))

        self.update_pilot_profile(
            player_name=player_name,
            score=score,
            wave=wave,
            elapsed_time_sec=elapsed_time_sec,
            outcome=resolved_outcome,
            enemies_destroyed=enemies_destroyed,
        )

        self.log_game_history(
            player_name=player_name,
            difficulty=difficulty,
            outcome=resolved_outcome,
            score=score,
            wave=wave,
            enemies_destroyed=enemies_destroyed,
            shots_fired=shots_fired,
            shots_hit=shots_hit,
            accuracy=accuracy,
        )

        return self.record_high_score(
            player_name=player_name,
            score=score,
            wave=wave,
            difficulty=difficulty,
            enemies_destroyed=enemies_destroyed,
            accuracy=accuracy,
        )