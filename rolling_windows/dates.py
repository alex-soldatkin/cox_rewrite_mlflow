from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Window:
    start_year: int
    end_year_inclusive: int
    start_ms: int
    end_ms: int

    @property
    def name_suffix(self) -> str:
        return f"{self.start_year}_{self.end_year_inclusive}"


def year_start_ms(year: int) -> int:
    dt = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def iter_year_windows(
    *,
    start_year: int,
    end_start_year: int,
    window_years: int,
    step_years: int,
) -> list[Window]:
    if window_years <= 0:
        raise ValueError("window_years must be positive")
    if step_years <= 0:
        raise ValueError("step_years must be positive")
    if end_start_year < start_year:
        raise ValueError("end_start_year must be >= start_year")

    windows: list[Window] = []
    for y in range(start_year, end_start_year + 1, step_years):
        start_ms = year_start_ms(y)
        end_year_exclusive = y + window_years
        end_ms = year_start_ms(end_year_exclusive)
        windows.append(
            Window(
                start_year=y,
                end_year_inclusive=end_year_exclusive - 1,
                start_ms=start_ms,
                end_ms=end_ms,
            )
        )
    return windows

