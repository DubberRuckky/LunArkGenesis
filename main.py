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
    args, _ = parser.parse_known_args()

    app = App(skip_startup=args.skip_startup)
    app.run()


if __name__ == "__main__":
    main()
