# AI-assisted: written with Google Antigravity. Reviewed by the LunArk team.
"""Pure-Python tick clock for LunArk: Genesis.

Independent of frame rate — strictly NO pygame imports.
Converts variable delta-time (dt) into fixed discrete 1-second simulation ticks,
supporting pause (0x) and variable warp speeds (1x, 2x, 4x, 8x).
"""

from typing import Final

ALLOWED_SPEEDS: Final[tuple[int, ...]] = (0, 1, 2, 4, 8)


class TickClock:
    """Fixed-rate logic clock that converts render delta time into simulation ticks."""

    def __init__(self, tick_rate: float = 1.0, initial_speed: int = 1) -> None:
        """Initialize the clock with a tick rate in seconds and starting speed.

        Args:
            tick_rate: Duration in real seconds per 1x logic tick (default 1.0s).
            initial_speed: Initial warp speed multiplier (0, 1, 2, 4, 8).
        """
        self.tick_rate: float = max(0.01, float(tick_rate))
        self.accumulator: float = 0.0
        self.total_ticks: int = 0
        self._last_unpaused_speed: int = 1 if initial_speed == 0 else initial_speed

        if initial_speed == 0:
            self.paused: bool = True
            self.speed: int = 0
        else:
            self.paused: bool = False
            self.speed: int = initial_speed

    def update(self, dt: float) -> int:
        """Accumulate delta time and return how many fixed ticks elapsed this frame.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            int: Number of discrete simulation ticks that fired this frame.
        """
        if self.paused or self.speed <= 0 or dt <= 0.0:
            return 0

        # Scale delta time by current simulation speed
        effective_dt = dt * self.speed
        self.accumulator += effective_dt

        if self.accumulator >= self.tick_rate:
            ticks = int(self.accumulator // self.tick_rate)
            self.accumulator %= self.tick_rate
            self.total_ticks += ticks
            return ticks

        return 0

    def set_speed(self, speed: int) -> None:
        """Set simulation speed to one of 0 (pause), 1x, 2x, 4x, or 8x.

        Args:
            speed: Desired speed multiplier.
        """
        if speed not in ALLOWED_SPEEDS:
            return

        if speed == 0:
            self.paused = True
            self.speed = 0
        else:
            self.paused = False
            self.speed = speed
            self._last_unpaused_speed = speed

    def pause(self) -> None:
        """Pause logic ticks without losing previous warp speed."""
        self.paused = True
        self.speed = 0

    def resume(self) -> None:
        """Resume logic ticks at the speed in use before pausing."""
        self.paused = False
        self.speed = self._last_unpaused_speed if self._last_unpaused_speed > 0 else 1

    def toggle_pause(self) -> None:
        """Toggle between paused (0x) and resumed running speed."""
        if self.paused or self.speed == 0:
            self.resume()
        else:
            self.pause()

    def drop_to_1x(self) -> None:
        """Drop warp speed down to 1x (e.g. when an alert or hazard triggers)."""
        if self.speed > 1:
            self.set_speed(1)

    def is_paused(self) -> bool:
        """Return True if the clock is currently paused."""
        return self.paused or self.speed == 0

    def get_speed(self) -> int:
        """Return current speed multiplier (0 if paused)."""
        return 0 if self.paused else self.speed

    def get_total_ticks(self) -> int:
        """Return total cumulative ticks elapsed since start or reset."""
        return self.total_ticks

    def reset(self) -> None:
        """Reset tick counter and accumulator back to zero."""
        self.accumulator = 0.0
        self.total_ticks = 0
