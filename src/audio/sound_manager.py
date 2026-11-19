"""src/audio/sound_manager.py

Non-blocking retro arcade sound effect engine for Space Invaders: Galactic Assault.
Dispatches synthesized tone sequences to a background daemon thread so audio
playback never stalls the 60 FPS Turtle ontimer() loop.
"""

import queue
import sys
import threading
import time
from typing import Dict, Optional, Sequence, Tuple

try:
    import winsound  # type: ignore[import-not-found]
except ImportError:
    winsound = None  # type: ignore[assignment]

ToneStep = Tuple[int, int]  # (frequency_hz, duration_ms)


class SoundManager:
    """Thread-safe, non-blocking retro arcade sound player with mute toggle."""

    SOUND_EFFECTS: Dict[str, Tuple[ToneStep, ...]] = {
        "laser": ((920, 28), (640, 24)),
        "hit": ((440, 25),),
        "explosion": ((240, 35), (160, 45), (110, 55)),
        "ufo": ((520, 40), (660, 40), (520, 40)),
        "powerup": ((523, 45), (659, 45), (784, 65)),
        "shield_block": ((330, 35), (587, 50)),
        "player_hit": ((220, 65), (147, 85), (98, 110)),
        "wave_clear": ((523, 55), (659, 55), (784, 55), (1047, 95)),
        "game_over": ((392, 95), (349, 95), (311, 110), (262, 160)),
        "victory": ((523, 65), (659, 65), (784, 65), (1047, 110), (1319, 150)),
    }

    def __init__(self, enabled: bool = True) -> None:
        self.enabled: bool = bool(enabled)
        self._queue: "queue.Queue[Optional[Tuple[ToneStep, ...]]]" = queue.Queue(
            maxsize=4
        )
        self._stop_event = threading.Event()
        self._worker = threading.Thread(
            target=self._audio_worker,
            name="SpaceInvadersAudioWorker",
            daemon=True,
        )
        self._worker.start()

    # ------------------------------------------------------------------
    # Mute State & Queue Dispatch
    # ------------------------------------------------------------------
    def toggle_mute(self) -> bool:
        """Toggles audio mute state and returns the new `enabled` status."""
        self.enabled = not self.enabled
        if not self.enabled:
            self._drain_queue()
        return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        """Explicitly enables or mutes sound playback."""
        self.enabled = bool(enabled)
        if not self.enabled:
            self._drain_queue()

    def _drain_queue(self) -> None:
        """Discards any queued tone sequences immediately."""
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def play(self, effect_name: str) -> None:
        """Queues a named retro sound effect without blocking the calling thread."""
        if not self.enabled or self._stop_event.is_set():
            return

        sequence = self.SOUND_EFFECTS.get(effect_name)
        if not sequence:
            return

        # Drop oldest pending effect if queue is full so rapid fire never lags
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass

        try:
            self._queue.put_nowait(sequence)
        except queue.Full:
            pass

    # ------------------------------------------------------------------
    # Convenience Effect Triggers
    # ------------------------------------------------------------------
    def play_laser(self) -> None:
        self.play("laser")

    def play_hit(self) -> None:
        self.play("hit")

    def play_explosion(self) -> None:
        self.play("explosion")

    def play_ufo(self) -> None:
        self.play("ufo")

    def play_powerup(self) -> None:
        self.play("powerup")

    def play_shield_block(self) -> None:
        self.play("shield_block")

    def play_player_hit(self) -> None:
        self.play("player_hit")

    def play_wave_clear(self) -> None:
        self.play("wave_clear")

    def play_game_over(self) -> None:
        self.play("game_over")

    def play_victory(self) -> None:
        self.play("victory")

    # ------------------------------------------------------------------
    # Background Audio Worker
    # ------------------------------------------------------------------
    def _play_sequence(self, sequence: Sequence[ToneStep]) -> None:
        """Plays a sequence of (frequency_hz, duration_ms) tones on the worker thread."""
        for freq_hz, duration_ms in sequence:
            if not self.enabled or self._stop_event.is_set():
                return

            if winsound is not None and sys.platform == "win32":
                try:
                    safe_freq = max(37, min(32767, int(freq_hz)))
                    safe_dur = max(10, int(duration_ms))
                    winsound.Beep(safe_freq, safe_dur)
                except RuntimeError:
                    time.sleep(duration_ms / 1000.0)
            else:
                # Non-Windows fallback: sleep for tone cadence without throwing
                time.sleep(duration_ms / 1000.0)

    def _audio_worker(self) -> None:
        """Background consumer loop that plays queued effects sequentially."""
        while not self._stop_event.is_set():
            try:
                sequence = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue

            if sequence is None:
                break

            self._play_sequence(sequence)

    def shutdown(self) -> None:
        """Signals the background audio thread to exit cleanly."""
        self._stop_event.set()
        self._drain_queue()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass