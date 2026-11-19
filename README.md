# AstraSeige

**A modular, 60 FPS retro arcade space shooter engineered in pure Python—featuring custom vector sprites, parallax particle effects, thread-safe synthesized audio, and persistent JSON/CSV telemetry.**

![Python Version](https://img.shields.io/badge/Python-3.10%2B-38BDF8?style=flat-square&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-4ADE80?style=flat-square)
![Architecture](https://img.shields.io/badge/Architecture-Modular%20OOP%20%7C%2060%20FPS-FACC15?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-11%20Unit%20%26%20Integration%20Tests-A855F7?style=flat-square)

---

## Overview

**AstraSeige** is a full-featured desktop arcade game built from the ground up using **only the Python Standard Library** (`turtle`, `tkinter`, `json`, `csv`, `threading`, `queue`, `time`, `math`, `random`, `enum`, `dataclasses`, and `unittest`). No third-party `pip` packages or external asset files are required.

Players pilot a starfighter defending the lower perimeter across a **10-wave galactic campaign** against four distinct invader classes, collecting timed tactical power-ups, competing for a persistent **Top-10 Hall of Fame**, and logging detailed combat telemetry after every mission[cite: 19, 20, 22].

---

## Key Features

### Gameplay & Combat Mechanics
* **Non-Blocking 60 FPS Loop:** Driven by `screen.ontimer()` and manual frame buffering (`screen.tracer(0)`), ensuring smooth input response and deterministic frame pacing without blocking `while True` loops[cite: 18, 22].
* **Polymorphic Invader Hierarchy:**
  * **Scout Invader (`BasicInvader`):** Agile front-line unit (`1 HP`, `10 PTS`)[cite: 19].
  * **Armoured Invader (`ArmouredInvader`):** Heavy-plated vanguard (`3 HP`, `30 PTS`) with dynamic armor color degradation (`#F59E0B` → `#FB923C` → `#FACC15`) on each hit[cite: 19].
  * **Elite Invader (`EliteInvader`):** High-rank command ship (`4 HP`, `60 PTS`) with elevated firing priority and multi-stage armor damage indicators[cite: 19].
  * **Mystery Saucer (`BonusUFO`):** High-speed upper-lane target awarding `100` to `250` randomized bonus points[cite: 19].
* **Tactical Power-Up Capsules:** Destroyed enemies have a chance to drop falling capsules:
  * **Energy Shield (`SHIELD`):** Projects a 7-second protective halo around the starfighter that absorbs enemy projectiles with an expanding shockwave ring[cite: 20, 22].
  * **Weapon Overdrive (`RAPID_FIRE`):** Grants 6 seconds of reduced firing cooldown and an expanded active laser cap[cite: 20, 22].
* **10-Wave Escalating Campaign:** Progressive fleet compositions, wave-completion point bonuses, and non-blocking intermission banners.
* **Three Combat Difficulty Presets:**
  * **Easy:** `4` starting lives, relaxed fleet pacing[cite: 15, 21].
  * **Normal:** `3` starting lives, balanced arcade pacing[cite: 15, 21].
  * **Hard:** `2` starting lives, aggressive fleet speed and enemy fire rates[cite: 15, 21].

### Graphics, Audio & Telemetry
* **Custom Vector Polygon Sprites (`src/ui/sprites.py`):** Multi-vertex geometric silhouettes registered directly on the Turtle canvas for the player starfighter and all four enemy classes, complete with automatic fallback shapes for headless environments.
* **Single-Pen Visual Effects Engine (`src/ui/effects.py`):** Zero-leak rendering pipeline featuring a 3-layer parallax scrolling deep-space starfield, radial particle explosion bursts, shield absorption shockwave rings, and floating score/buff callouts.
* **Non-Blocking Retro Sound Synthesizer (`src/audio/sound_manager.py`):** Dispatches multi-tone arcade sound effects (`laser`, `hit`, `explosion`, `powerup`, `shield_block`, `player_hit`, `wave_clear`, `game_over`, `victory`) to a bounded daemon worker thread so audio playback never stalls frame updates, complete with an instant `[S]` mute toggle.
* **Persistent Hall of Fame & Match Logs (`src/storage/score_manager.py`):** Automatically loads the all-time high score on startup, ranks qualifying runs in `data/high_scores.json` (Top 10), and appends full post-mission telemetry rows to `data/game_history.csv`.

---

## Project Directory Structure

```text
AstraSeige/
├── main.py                         # Application entry point & clean shutdown guard
├── config.py                       # Screen geometry, physics constants & difficulty presets
├── .gitignore                      # Git exclusion rules (cache, venvs, local save data)
├── README.md                       # Project documentation
├── data/                           # Auto-created runtime persistence directory
│   ├── high_scores.json            # Persistent Top-10 leaderboard
│   └── game_history.csv            # Complete chronological session telemetry log
├── src/
│   ├── audio/
│   │   └── sound_manager.py        # Thread-safe, non-blocking retro tone synthesizer
│   ├── entities/
│   │   ├── bullet.py               # Player laser & enemy bolt projectile physics
│   │   ├── enemy.py                # Base invader class, HP system & formation movement
│   │   ├── enemy_types.py          # BasicInvader, ArmouredInvader, EliteInvader, BonusUFO
│   │   ├── player.py               # Starfighter controls, cooldowns, shield & rapid-fire buffs
│   │   └── powerup.py              # Falling power-up capsule spawning & lifecycle
│   ├── game/
│   │   ├── collision_manager.py    # AABB collision resolution, bullet clashes & breach checks
│   │   ├── game_manager.py         # Central 60 FPS coordinator, input router & state machine
│   │   ├── game_state.py           # GameState enum & live GameSession telemetry model
│   │   └── wave_manager.py         # 10-wave fleet spawning, movement & frontline shooting
│   ├── storage/
│   │   └── score_manager.py        # JSON leaderboard ranking & CSV match history writer
│   └── ui/
│       ├── effects.py              # Parallax starfield, particle explosions & pulse rings
│       ├── hud.py                  # Snapshot-cached live HUD, life icons & buff timers
│       ├── menu.py                 # Title screen, difficulty cards, pilot entry & Hall of Fame
│       ├── screens.py              # Pause modal, wave banners & Game Over/Victory debriefs
│       └── sprites.py              # Custom vector polygon shape definitions & registration
└── tests/
    └── test_game_systems.py        # Headless unittest suite (11 unit & integration tests)



## Prerequisites & Installation

### Prerequisites

- **Python 3.10 or higher**
- **Tkinter** (included by default with standard Windows and macOS Python installers; on Debian/Ubuntu Linux, install via `sudo apt-get install python3-tk` if missing)

### Setup

```bash
git clone https://github.com/AnthonyQuant/AstraSeige.git
cd AstraSeige
```

No virtual environment or external dependency installation is required.

## Running the Game

Launch **AstraSeige** from the repository root:

```bash
python main.py
```

### Controls Reference

| Key | Active Screen | Action |
|---|---|---|
| `Left` / `Right` or `A` / `D` | Gameplay / Menu | Move starfighter horizontally / cycle difficulty `game_manager.py` |
| `Space` | Gameplay | Fire plasma laser `game_manager.py` |
| `1` / `2` / `3` | Main Menu | Select `Easy`, `Normal`, or `Hard` difficulty `game_manager.py` |
| `N` | Main Menu | Register custom pilot callsign (up to 16 characters) `game_manager.py` |
| `H` | Main Menu | Toggle the Top-10 High Scores Hall of Fame `game_manager.py` |
| `Enter` | Menu / Debrief | Launch mission / play again `game_manager.py` |
| `P` | Gameplay / Paused | Pause or resume active mission `game_manager.py` |
| `R` | Gameplay / Paused / Debrief | Restart mission immediately `game_manager.py` |
| `S` | Any Screen | Mute or unmute retro sound effects `game_manager.py` |
| `M` | Paused / Debrief | Return to Main Menu[cite: 22] |
| `Backspace` / `Esc` | Leaderboard / Any | Return from leaderboard / exit application[cite: 22] |

## Architecture & Engineering Highlights

1. **Deterministic State Machine (`GameState`):** Clean separation between `MENU`, `PLAYING`, `PAUSED`, `GAME_OVER`, and `VICTORY` states prevents stray projectiles, ghost inputs, or duplicate score commits. `game_state.py + 1`
2. **Axis-Aligned Bounding Box (AABB) Combat Engine:** `CollisionManager` processes player bullets vs. enemies, mid-air projectile-on-projectile interception, enemy bolts vs. player/shield, power-up capsule pickups, and defensive-line breaches in a single deterministic pass per frame[cite: 22].
3. **Zero-Leak Canvas Rendering:** Both `HUD` (via tuple snapshot diffing) and `Effects` (via bounded particle lists on two reusable pens) avoid creating per-frame `Turtle` instances, eliminating Tkinter canvas memory growth during extended multi-wave runs. `hud.py`
4. **Headless Test Isolation:** `tests/test_game_systems.py` patches `turtle.Turtle` and `turtle.Screen` with stateful in-memory stubs, allowing all gameplay, collision, and file persistence logic to be verified in CI/headless terminals without opening a GUI window.

## Automated Test Suite

Run the full unit and integration test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

### Test Coverage Breakdown

- `TestGameSession`: Verifies difficulty preset life synchronization, shot/hit accuracy math, new high-score flags, and per-run metric resets.
- `TestEntitiesAndPowerUps`: Validates horizontal playfield boundary clamping, weapon cooldown enforcement, `RAPID_FIRE` buff activation, and multi-HP armor degradation (`ArmouredInvader` & `EliteInvader`).
- `TestWaveAndCollisionSystems`: Tests wave spawning, final-wave detection, player bullet hits, `SHIELD` projectile absorption, power-up capsule collection, and defensive-line breach triggers.
- `TestScoreManagerPersistence`: Uses isolated temporary directories to verify Top-10 JSON leaderboard sorting/capping and CSV telemetry serialization.
- `TestSoundManager`: Confirms non-blocking queue dispatch, `[S]` mute state toggling, and clean daemon thread shutdown.

## Data Persistence Schema

Runtime files are automatically created inside `data/` upon completing your first mission[cite: 22]:

- `data/high_scores.json`: Stores up to 10 top-scoring runs sorted descending by score, containing `player_name`, `score`, `wave`, `difficulty`, `accuracy`, and `timestamp`.
- `data/game_history.csv`: Appends one row per completed run (`GAME_OVER` or `VICTORY`) recording `timestamp`, `player_name`, `outcome`, `difficulty`, `score`, `wave`, `enemies_destroyed`, `shots_fired`, `shots_hit`, and `accuracy`.

## Author & License

Developed by **Anthony Matthew Omokpo** (GitHub: `@AnthonyQuant`).

Released under the **MIT License.**