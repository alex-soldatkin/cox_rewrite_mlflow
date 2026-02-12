from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PeriodType(str, Enum):
    """Supported temporal period types for rolling windows."""
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    BIANNUAL = "biannual"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class Window:
    start_year: int
    end_year_inclusive: int
    start_ms: int
    end_ms: int
    period_type: str = "yearly"
    quarter: Optional[int] = None  # 1-4 for quarterly
    half: Optional[int] = None      # 1-2 for biannual
    month: Optional[int] = None     # 1-12 for monthly

    @property
    def name_suffix(self) -> str:
        """Generate period-aware window name."""
        if self.period_type == PeriodType.QUARTERLY and self.quarter:
            return f"Q{self.quarter}_{self.start_year}"
        elif self.period_type == PeriodType.BIANNUAL and self.half:
            return f"H{self.half}_{self.start_year}"
        elif self.period_type == PeriodType.MONTHLY and self.month:
            return f"M{self.month:02d}_{self.start_year}"
        else:
            # Default yearly format
            return f"{self.start_year}_{self.end_year_inclusive}"


def year_start_ms(year: int) -> int:
    """Calculate millisecond timestamp for start of year."""
    dt = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def period_start_ms(year: int, quarter: Optional[int] = None, 
                    half: Optional[int] = None, month: Optional[int] = None) -> int:
    """
    Calculate millisecond timestamp for start of arbitrary period.
    
    Args:
        year: Year
        quarter: 1-4 for quarterly periods
        half: 1-2 for biannual periods
        month: 1-12 for monthly periods
        
    Returns:
        Millisecond timestamp
    """
    if quarter:
        # Quarters: Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct
        month_num = (quarter - 1) * 3 + 1
    elif half:
        # Halves: H1=Jan, H2=Jul
        month_num = (half - 1) * 6 + 1
    elif month:
        month_num = month
    else:
        # Default to start of year
        month_num = 1
    
    dt = datetime(year, month_num, 1, 0, 0, 0, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def iter_period_windows(
    *,
    start_year: int,
    end_start_year: int,
    window_size: int,
    step_size: int,
    period_type: str = "yearly",
) -> list[Window]:
    """
    Generate rolling windows for arbitrary temporal periods.
    
    Args:
        start_year: First window start year
        end_start_year: Last window start year
        window_size: Window size in the chosen period (e.g., 1 quarter, 2 years)
        step_size: Step size in the chosen period
        period_type: Type of period (yearly, quarterly, biannual, monthly)
        
    Returns:
        List of Window objects with period-aware naming
        
    Examples:
        # Quarterly windows from 2010-2012
        >>> iter_period_windows(start_year=2010, end_start_year=2012, 
        ...                     window_size=1, step_size=1, period_type="quarterly")
        [Window(Q1_2010), Window(Q2_2010), ..., Window(Q4_2012)]
        
        # Biannual windows from 2003-2021
        >>> iter_period_windows(start_year=2003, end_start_year=2021,
        ...                     window_size=1, step_size=1, period_type="biannual")
        [Window(H1_2003), Window(H2_2003), ..., Window(H2_2021)]
    """
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if step_size <= 0:
        raise ValueError("step_size must be positive")
    if end_start_year < start_year:
        raise ValueError("end_start_year must be >= start_year")
    
    # Normalise period type
    try:
        period = PeriodType(period_type.lower())
    except ValueError:
        raise ValueError(f"Invalid period_type: {period_type}. Must be one of: {[p.value for p in PeriodType]}")
    
    windows: list[Window] = []
    
    if period == PeriodType.YEARLY:
        # Yearly windows (original implementation)
        for y in range(start_year, end_start_year + 1, step_size):
            start_ms = year_start_ms(y)
            end_year_exclusive = y + window_size
            end_ms = year_start_ms(end_year_exclusive)
            windows.append(
                Window(
                    start_year=y,
                    end_year_inclusive=end_year_exclusive - 1,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    period_type=period.value,
                )
            )
    
    elif period == PeriodType.QUARTERLY:
        # Quarterly windows
        # Generate all quarters from start_year to end_start_year
        for y in range(start_year, end_start_year + 1):
            for q in range(1, 5):  # Q1-Q4
                start_ms = period_start_ms(y, quarter=q)
                
                # Calculate end period
                end_q = q + window_size
                end_y = y
                while end_q > 4:
                    end_q -= 4
                    end_y += 1
                end_ms = period_start_ms(end_y, quarter=end_q)
                
                windows.append(
                    Window(
                        start_year=y,
                        end_year_inclusive=end_y if end_q > 1 else end_y - 1,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        period_type=period.value,
                        quarter=q,
                    )
                )
        
        # Apply step_size filter
        if step_size > 1:
            windows = windows[::step_size]
    
    elif period == PeriodType.BIANNUAL:
        # Biannual (half-yearly) windows
        for y in range(start_year, end_start_year + 1):
            for h in range(1, 3):  # H1, H2
                start_ms = period_start_ms(y, half=h)
                
                # Calculate end period
                end_h = h + window_size
                end_y = y
                while end_h > 2:
                    end_h -= 2
                    end_y += 1
                end_ms = period_start_ms(end_y, half=end_h)
                
                windows.append(
                    Window(
                        start_year=y,
                        end_year_inclusive=end_y if end_h > 1 else end_y - 1,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        period_type=period.value,
                        half=h,
                    )
                )
        
        # Apply step_size filter
        if step_size > 1:
            windows = windows[::step_size]
    
    elif period == PeriodType.MONTHLY:
        # Monthly windows
        for y in range(start_year, end_start_year + 1):
            for m in range(1, 13):  # Months 1-12
                start_ms = period_start_ms(y, month=m)
                
                # Calculate end period
                end_m = m + window_size
                end_y = y
                while end_m > 12:
                    end_m -= 12
                    end_y += 1
                end_ms = period_start_ms(end_y, month=end_m)
                
                windows.append(
                    Window(
                        start_year=y,
                        end_year_inclusive=end_y if end_m > 1 else end_y - 1,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        period_type=period.value,
                        month=m,
                    )
                )
        
        # Apply step_size filter
        if step_size > 1:
            windows = windows[::step_size]
    
    return windows


def iter_year_windows(
    *,
    start_year: int,
    end_start_year: int,
    window_years: int,
    step_years: int,
) -> list[Window]:
    """
    Generate yearly rolling windows (backwards compatibility wrapper).
    
    This function is maintained for backwards compatibility.
    Consider using iter_period_windows() with period_type="yearly" instead.
    """
    return iter_period_windows(
        start_year=start_year,
        end_start_year=end_start_year,
        window_size=window_years,
        step_size=step_years,
        period_type="yearly",
    )

