# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Entry point for LunArk: Genesis.

Initializes the game engine and starts the main application loop.
"""

from game.app import App


def main() -> None:
    """Instantiate and execute the LunArk application."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
