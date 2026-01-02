from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import calendar
from typing import List, Tuple


@dataclass(frozen=True)
class MonthInfo:
    index: int
    name: str
    abbrev: str
    days: int
    start_day_of_year: int


@dataclass(frozen=True)
class CalendarModel:
    year: int
    months: List[MonthInfo]
    total_days: int
    weeks_in_year: int

    @classmethod
    def for_year(cls, year: int) -> "CalendarModel":
        months: List[MonthInfo] = []
        day_cursor = 0
        for month in range(1, 13):
            days = calendar.monthrange(year, month)[1]
            info = MonthInfo(
                index=month - 1,
                name=calendar.month_name[month],
                abbrev=calendar.month_abbr[month],
                days=days,
                start_day_of_year=day_cursor,
            )
            months.append(info)
            day_cursor += days

        weeks_in_year = date(year, 12, 28).isocalendar().week
        return cls(year=year, months=months, total_days=day_cursor, weeks_in_year=weeks_in_year)

    def month(self, month_idx: int) -> MonthInfo:
        return self.months[month_idx]

    def day_of_year(self, month_idx: int, day: int) -> int:
        return self.months[month_idx].start_day_of_year + (day - 1)

    def date_label(self, month_idx: int, day: int) -> str:
        return f"{self.months[month_idx].abbrev} {day}"

    def week_of_date(self, month_idx: int, day: int) -> int:
        """Return the ISO week number (1-based) for a given month and day."""
        d = date(self.year, month_idx + 1, day)
        return d.isocalendar().week

    def week_date_range(self, week_num: int) -> Tuple[date, date]:
        """Return (Monday, Sunday) dates for the given ISO week number."""
        # ISO week: Week 1 contains January 4th
        jan4 = date(self.year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        start = week1_monday + timedelta(weeks=week_num - 1)
        end = start + timedelta(days=6)
        return start, end

    def week_date_range_label(self, week_num: int) -> str:
        """Return formatted date range label for the given ISO week (e.g., 'Dec 29 - Jan 4')."""
        start, end = self.week_date_range(week_num)
        start_label = f"{calendar.month_abbr[start.month]} {start.day}"
        end_label = f"{calendar.month_abbr[end.month]} {end.day}"
        return f"{start_label} - {end_label}"

    def day_of_week_abbrev(self, month_idx: int, day: int) -> str:
        """Return abbreviated day name (Mon, Tue, etc.)."""
        d = date(self.year, month_idx + 1, day)
        return calendar.day_abbr[d.weekday()]

    def compute_week_starts(self) -> List[int]:
        """Return list of first ISO week number for each month (0-indexed month).

        This accounts for ISO week rules where week 1 may start in December
        of the previous year, and week 52/53 may extend into January of
        the next year.
        """
        result = []
        for month_idx in range(12):
            first_day = date(self.year, month_idx + 1, 1)
            iso_year, week_num, _ = first_day.isocalendar()
            # If ISO year differs from calendar year, find the first week
            # that actually belongs to this year
            if iso_year < self.year:
                # First day of Jan is in last week of previous year
                # Find first Monday of this year
                for d in range(1, 8):
                    test_date = date(self.year, 1, d)
                    if test_date.isocalendar().year == self.year:
                        week_num = test_date.isocalendar().week
                        break
            result.append(week_num)
        return result

    def week_primary_month(self, week_num: int) -> int:
        """Return the month index (0-based) where most days of this week fall.

        For a week spanning two months, returns the month with 4+ days.
        """
        start_date, end_date = self.week_date_range(week_num)

        # Count days in each month
        days_per_month: dict[int, int] = {}
        current = start_date
        while current <= end_date:
            # Only count days within this year
            if current.year == self.year:
                month_idx = current.month - 1
                days_per_month[month_idx] = days_per_month.get(month_idx, 0) + 1
            current += timedelta(days=1)

        if not days_per_month:
            # All days are outside this year, default to January or December
            if start_date.year < self.year:
                return 0  # January
            else:
                return 11  # December

        # Return month with most days
        return max(days_per_month, key=lambda m: days_per_month[m])

    def compute_weeks_by_month(self) -> List[List[int]]:
        """Return list of week numbers for each month, based on majority days.

        Returns a list of 12 lists, where each inner list contains the week
        numbers that primarily belong to that month.
        """
        result: List[List[int]] = [[] for _ in range(12)]
        for week_num in range(1, self.weeks_in_year + 1):
            month_idx = self.week_primary_month(week_num)
            result[month_idx].append(week_num)
        return result

    def is_last_day_of_month(self, month_idx: int, day: int) -> bool:
        """Return True if this is the last day of the month."""
        return day == self.months[month_idx].days

    def is_last_day_of_week(self, month_idx: int, day: int) -> bool:
        """Return True if this is Sunday (last day of ISO week)."""
        d = date(self.year, month_idx + 1, day)
        return d.weekday() == 6  # Sunday = 6
