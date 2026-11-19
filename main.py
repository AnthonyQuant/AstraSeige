"""main.py

Entry point for Space Invaders: Galactic Assault.
"""

import turtle

from src.game.game_manager import GameManager


def main() -> None:
    """Initializes and launches the Space Invaders game."""
    try:
        game = GameManager()
        game.run()
    except (turtle.Terminator, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()