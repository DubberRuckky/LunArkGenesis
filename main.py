# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Entry point for LunArk: Genesis.

Initializes the game engine and starts the main application loop.
"""

import argparse

from game.app import App


def main() -> None:
    """Instantiate and execute the LunArk application."""
    parser = argparse.ArgumentParser(description="LunArk: Genesis entry point")
    parser.add_argument(
        "--skip-startup",
        action="store_true",
        help="Skip startup sequence cards and open directly on Title screen",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable developer debug shortcuts (F4 for Win, F5 for Lose)",
    )
    args, _ = parser.parse_known_args()

    app = App(skip_startup=args.skip_startup, debug=args.debug)
    app.run()


if __name__ == "__main__":
    main()
