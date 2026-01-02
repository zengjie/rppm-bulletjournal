from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import fitz

from bujo.calendar_model import CalendarModel
from bujo.config import Layout, Settings, Theme, Typography
from bujo.page_map import PageMap
from .primitives import Renderer


FOOTER_TEXTS = {
    "daily_log": "Rapid log your thoughts as they bubble up.",
    "weekly_action": "Write only what you can get done this week.",
    "weekly_reflection": "Tidy, acknowledge, migrate, enact.",
    "collection_index": "Organize related information by topic.",
    "future_log": "Store actions and events outside the current month.",
    "monthly_timeline": "Log events after they happen for an accurate record.",
    "monthly_action": "Organize and prioritize your monthly tasks.",
    "intention": "Intention is a commitment to a process. It guides your choices in the present moment.",
    "goals": "Goals define outcomes. They transform desires into tangible destinations.",
}


@dataclass(frozen=True)
class PageContext:
    renderer: Renderer
    calendar: CalendarModel
    page_map: PageMap
    settings: Settings
    layout: Layout
    theme: Theme
    typography: Typography


def generate_cover(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    page.draw_rect(page.rect, color=ctx.theme.black, fill=ctx.theme.black)

    left_margin = 50
    title_y = ctx.layout.target_height * 0.15

    lightning_scale = 8.0
    lightning_x = left_margin
    lightning_y = title_y + 20
    ctx.renderer.draw_lightning_white(page, lightning_x, lightning_y, scale=lightning_scale)

    text_x = left_margin + 130

    bullet_size = 90
    ctx.renderer.add_text(page, "Bullet", text_x, title_y, bullet_size, ctx.theme.white)

    journal_y = title_y + 95
    ctx.renderer.add_text(page, "Journal", text_x, journal_y, bullet_size, ctx.theme.white)

    year_y = journal_y + 130
    year_size = 140
    ctx.renderer.add_text(page, str(ctx.settings.year), text_x, year_y, year_size, ctx.theme.white)


def generate_main_index(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_text(page, "Index A", ctx.layout.content_left, ctx.layout.content_top + 10, ctx.typography.sizes["title_page"])

    y = ctx.layout.content_top + 80
    row_height = 52

    guide_links = [
        ("Symbol Reference", ctx.page_map.guide_start),
        ("The System", ctx.page_map.guide_start + 1),
        ("The Practice", ctx.page_map.guide_start + 2),
        ("Set up your logs", ctx.page_map.guide_start + 3),
        ("Intention", ctx.page_map.guide_start + 4),
        ("Goals", ctx.page_map.guide_start + 5),
        ("Future log", ctx.page_map.future_log_start),
    ]

    for i, (text, dest) in enumerate(guide_links):
        ctx.renderer.add_nav_link(page_idx, text, dest, ctx.layout.content_left, y, ctx.typography.sizes["body"], with_arrow=False)
        arrow_y = y + ctx.typography.sizes["body"] * 0.65
        arrow_x = ctx.layout.content_right - 25
        ctx.renderer.draw_arrow_right(page, arrow_x, arrow_y, ctx.typography.arrow_size_large)
        arrow_link_rect = (arrow_x - 10, y - 5, ctx.layout.content_right, y + ctx.typography.sizes["body"] + 5)
        ctx.renderer.links.add(page_idx, arrow_link_rect, dest)
        page.draw_line(
            fitz.Point(ctx.layout.content_left, y + 40),
            fitz.Point(ctx.layout.content_right, y + 40),
            color=ctx.theme.line,
            width=0.5,
        )
        y += row_height

    # Decorative separator between Guide section and calendar tables
    page.draw_line(
        fitz.Point(ctx.layout.content_left, y + 10),
        fitz.Point(ctx.layout.content_right, y + 10),
        color=ctx.theme.gray,
        width=1.5,
    )
    y += 35

    month_col_width = 180
    week_col_start = ctx.layout.content_left + month_col_width + 50

    ctx.renderer.add_text(page, "Monthly logs", ctx.layout.content_left, y, ctx.typography.sizes["body"])
    ctx.renderer.add_text(page, "Weekly logs", week_col_start, y, ctx.typography.sizes["body"])
    y += 55

    available_height = ctx.layout.content_bottom - y - 20
    month_row_height = available_height // 12

    week_starts = [1, 6, 10, 14, 19, 23, 27, 32, 36, 40, 45, 49]
    week_area_width = ctx.layout.content_right - week_col_start
    week_num_width = 95

    for month_idx in range(12):
        month = ctx.calendar.months[month_idx]
        month_page = ctx.page_map.month_timeline(month_idx)

        text_y = y + (month_row_height - ctx.typography.sizes["small"]) / 2 - 10

        ctx.renderer.add_text(page, month.name, ctx.layout.content_left, text_y, ctx.typography.sizes["small"])
        month_arrow_x = ctx.layout.content_left + 120
        month_arrow_y = text_y + ctx.typography.sizes["small"] * 0.65
        ctx.renderer.draw_arrow_right(page, month_arrow_x, month_arrow_y, ctx.typography.arrow_size_small)
        month_link_rect = (
            ctx.layout.content_left - 5,
            text_y - 5,
            month_col_width,
            text_y + ctx.typography.sizes["small"] + 5,
        )
        ctx.renderer.links.add(page_idx, month_link_rect, month_page)

        sep_x = week_col_start - 25
        page.draw_line(
            fitz.Point(sep_x, y),
            fitz.Point(sep_x, y + month_row_height - 12),
            color=ctx.theme.line,
            width=0.5,
        )

        week_start = week_starts[month_idx]
        week_end = week_starts[month_idx + 1] if month_idx < 11 else ctx.calendar.weeks_in_year + 1

        for i, w in enumerate(range(week_start, week_end)):
            week_page = ctx.page_map.weekly_action(w - 1)
            week_x = week_col_start + i * week_num_width

            ctx.renderer.add_text(page, str(w), week_x, text_y, ctx.typography.sizes["small"])
            week_arrow_x = week_x + 30
            week_arrow_y = text_y + ctx.typography.sizes["small"] * 0.65
            ctx.renderer.draw_arrow_right(page, week_arrow_x, week_arrow_y, ctx.typography.arrow_size_small)
            week_link_rect = (
                week_x - 5,
                text_y - 5,
                week_x + week_num_width - 5,
                text_y + ctx.typography.sizes["small"] + 5,
            )
            ctx.renderer.links.add(page_idx, week_link_rect, week_page)

        line_y = y + month_row_height - 12
        page.draw_line(
            fitz.Point(ctx.layout.content_left, line_y),
            fitz.Point(ctx.layout.content_right, line_y),
            color=ctx.theme.line,
            width=0.5,
        )
        y += month_row_height


def generate_year_index(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_text(page, "Index B", ctx.layout.content_left, ctx.layout.content_top + 10, ctx.typography.sizes["title_page"])
    ctx.renderer.add_text(page, "Daily logs", ctx.layout.content_left, ctx.layout.content_top + 75, ctx.typography.sizes["body"])

    y = ctx.layout.content_top + 130
    available_height = ctx.layout.content_bottom - y - 60
    month_block_height = available_height // 12

    days_per_row = 16
    day_col_start = ctx.layout.content_left + 115
    day_col_width = ctx.layout.content_right - day_col_start - 20
    day_spacing = day_col_width / days_per_row

    for month in ctx.calendar.months:
        row1_y = y + 8
        row2_y = y + month_block_height / 2 + 2

        ctx.renderer.add_text(page, month.name, ctx.layout.content_left, row1_y, ctx.typography.sizes["small"])

        row_gap = row2_y - row1_y - ctx.typography.sizes["tiny"]
        v_padding = min(8, row_gap / 2 - 1)

        for day in range(1, min(month.days + 1, 17)):
            link_left = day_col_start + (day - 1) * day_spacing
            link_right = link_left + day_spacing

            text_width = ctx.renderer.get_text_width(str(day), ctx.typography.sizes["tiny"])
            text_x = link_left + (day_spacing - text_width) / 2
            ctx.renderer.add_text(page, str(day), text_x, row1_y, ctx.typography.sizes["tiny"])

            day_of_year = ctx.calendar.day_of_year(month.index, day)
            dest_page = ctx.page_map.daily_page(day_of_year)
            link_rect = (link_left, row1_y - v_padding, link_right, row1_y + ctx.typography.sizes["tiny"] + v_padding)
            ctx.renderer.links.add(page_idx, link_rect, dest_page)

        for day in range(17, month.days + 1):
            link_left = day_col_start + (day - 17) * day_spacing
            link_right = link_left + day_spacing

            text_width = ctx.renderer.get_text_width(str(day), ctx.typography.sizes["tiny"])
            text_x = link_left + (day_spacing - text_width) / 2
            ctx.renderer.add_text(page, str(day), text_x, row2_y, ctx.typography.sizes["tiny"])

            day_of_year = ctx.calendar.day_of_year(month.index, day)
            dest_page = ctx.page_map.daily_page(day_of_year)
            link_rect = (link_left, row2_y - v_padding, link_right, row2_y + ctx.typography.sizes["tiny"] + v_padding)
            ctx.renderer.links.add(page_idx, link_rect, dest_page)

        line_y = y + month_block_height - 8
        page.draw_line(
            fitz.Point(ctx.layout.content_left, line_y),
            fitz.Point(ctx.layout.content_right, line_y),
            color=ctx.theme.line,
            width=0.5,
        )

        y += month_block_height

    ctx.renderer.add_bottom_nav(page_idx, [("Index", ctx.page_map.main_index)])


def generate_collection_index(ctx: PageContext, page_idx: int, letter: str) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, f"Index {letter}", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    y = ctx.layout.content_top + 130
    line_spacing = 60
    num_lines = ctx.settings.num_collections_per_index

    collection_offset = 0 if letter == "C" else ctx.settings.num_collections_per_index

    for i in range(num_lines):
        line_y = y + i * line_spacing
        page.draw_line(
            fitz.Point(ctx.layout.content_left, line_y),
            fitz.Point(ctx.layout.content_right, line_y),
            color=ctx.theme.line,
            width=0.5,
        )

        arrow_y = line_y + line_spacing / 2
        arrow_x = ctx.layout.content_right - 22
        ctx.renderer.draw_arrow_right(page, arrow_x, arrow_y, ctx.typography.arrow_size_large)

        collection_idx = collection_offset + i
        collection_page = ctx.page_map.collection_page(collection_idx)
        link_rect = (arrow_x - 15, arrow_y - 15, ctx.layout.content_right, arrow_y + 15)
        ctx.renderer.links.add(page_idx, link_rect, collection_page)

    bottom_line_y = y + num_lines * line_spacing
    page.draw_line(
        fitz.Point(ctx.layout.content_left, bottom_line_y),
        fitz.Point(ctx.layout.content_right, bottom_line_y),
        color=ctx.theme.line,
        width=0.5,
    )

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["collection_index"])


def generate_guide_symbol_reference(ctx: PageContext, page_idx: int) -> None:
    """Generate Symbol Reference page - quick reference for all symbols with elegant design."""
    page = ctx.renderer.doc[page_idx]
    font_header = 28
    font_section = 22
    font_desc = 22
    line_height = 1.8

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Symbol Reference", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Card dimensions and positions
    card_gap = 25
    card_padding = 20
    content_width = ctx.layout.content_width
    card_width = (content_width - card_gap * 2) // 3
    y_start = ctx.layout.content_top + 130

    # Card heights - calculate based on content
    card1_rows = 4  # N.A.M.E.
    card2_rows = 5  # Action States
    card3_rows = 3  # Signifiers
    row_height = font_desc * line_height
    max_rows = max(card1_rows, card2_rows, card3_rows)
    card_height = 45 + row_height * max_rows + card_padding

    # Card positions
    card1_x = ctx.layout.content_left
    card2_x = ctx.layout.content_left + card_width + card_gap
    card3_x = ctx.layout.content_left + card_width * 2 + card_gap * 2

    # Draw card backgrounds with subtle borders
    for card_x in [card1_x, card2_x, card3_x]:
        page.draw_rect(
            fitz.Rect(card_x, y_start, card_x + card_width, y_start + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )

    symbol_x_offset = card_padding + 5
    desc_x_offset = card_padding + 50

    # Helper to draw symbols
    def draw_dash(x: float, y: float, size: int = 14) -> None:
        page.draw_line(fitz.Point(x, y), fitz.Point(x + size, y), color=ctx.theme.black, width=2.2)

    def draw_dot(x: float, y: float, r: int = 5) -> None:
        page.draw_circle(fitz.Point(x + r, y), r, color=ctx.theme.black, fill=ctx.theme.black)

    def draw_double_line(x: float, y: float, size: int = 14) -> None:
        for offset in [-4, 4]:
            page.draw_line(fitz.Point(x, y + offset), fitz.Point(x + size, y + offset), color=ctx.theme.black, width=1.8)

    def draw_circle_outline(x: float, y: float, r: int = 6) -> None:
        page.draw_circle(fitz.Point(x + r, y), r, color=ctx.theme.black, width=2)

    def draw_x_mark(x: float, y: float, size: int = 10) -> None:
        page.draw_line(fitz.Point(x, y - size / 2), fitz.Point(x + size, y + size / 2), color=ctx.theme.black, width=2.2)
        page.draw_line(fitz.Point(x, y + size / 2), fitz.Point(x + size, y - size / 2), color=ctx.theme.black, width=2.2)

    def draw_arrow_right(x: float, y: float, size: int = 10) -> None:
        page.draw_line(fitz.Point(x, y - size / 2), fitz.Point(x + size, y), color=ctx.theme.black, width=2.2)
        page.draw_line(fitz.Point(x, y + size / 2), fitz.Point(x + size, y), color=ctx.theme.black, width=2.2)

    def draw_arrow_left(x: float, y: float, size: int = 10) -> None:
        page.draw_line(fitz.Point(x + size, y - size / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.2)
        page.draw_line(fitz.Point(x + size, y + size / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.2)

    # Card 1: Rapid Logging (N.A.M.E.)
    ctx.renderer.add_text(page, "Rapid Logging", card1_x + card_padding, y_start + card_padding, font_section)
    y = y_start + card_padding + 45

    items1 = [
        (draw_dash, "Notes"),
        (draw_dot, "Actions"),
        (draw_double_line, "Moods"),
        (draw_circle_outline, "Events"),
    ]
    for draw_fn, label in items1:
        sym_y = y + font_desc * 0.55
        draw_fn(card1_x + symbol_x_offset, sym_y)
        ctx.renderer.add_text(page, label, card1_x + desc_x_offset, y, font_desc)
        y += row_height

    # Card 2: Action States
    ctx.renderer.add_text(page, "Action States", card2_x + card_padding, y_start + card_padding, font_section)
    y = y_start + card_padding + 45

    # Incomplete
    sym_y = y + font_desc * 0.55
    draw_dot(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Incomplete", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Complete
    sym_y = y + font_desc * 0.55
    draw_x_mark(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Complete", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Migrated
    sym_y = y + font_desc * 0.55
    draw_arrow_right(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Migrated", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Scheduled
    sym_y = y + font_desc * 0.55
    draw_arrow_left(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Scheduled", card2_x + desc_x_offset, y, font_desc)
    y += row_height

    # Irrelevant
    sym_y = y + font_desc * 0.55
    draw_dot(card2_x + symbol_x_offset, sym_y)
    ctx.renderer.add_text(page, "Irrelevant", card2_x + desc_x_offset, y, font_desc)
    text_width = ctx.renderer.get_text_width("Irrelevant", font_desc)
    page.draw_line(fitz.Point(card2_x + symbol_x_offset, sym_y), fitz.Point(card2_x + desc_x_offset + text_width, sym_y), color=ctx.theme.black, width=1)

    # Card 3: Signifiers
    ctx.renderer.add_text(page, "Signifiers", card3_x + card_padding, y_start + card_padding, font_section)
    y = y_start + card_padding + 45
    icon_size = 12

    # Priority
    sym_y = y + font_desc * 0.55
    ctx.renderer.draw_star(page, card3_x + symbol_x_offset + 6, sym_y, icon_size)
    ctx.renderer.add_text(page, "Priority", card3_x + desc_x_offset, y, font_desc)
    y += row_height

    # Inspiration
    sym_y = y + font_desc * 0.6
    ctx.renderer.draw_lightbulb(page, card3_x + symbol_x_offset + 6, sym_y, icon_size)
    ctx.renderer.add_text(page, "Inspiration", card3_x + desc_x_offset, y, font_desc)
    y += row_height

    # Explore
    sym_y = y + font_desc * 0.55
    ctx.renderer.draw_eye(page, card3_x + symbol_x_offset + 6, sym_y, icon_size)
    ctx.renderer.add_text(page, "Explore", card3_x + desc_x_offset, y, font_desc)

    # Example section - calculate available space and distribute evenly
    example_start_y = y_start + card_height + 50
    available_height = ctx.layout.content_bottom - example_start_y - 30

    # Section title with decorative line
    ctx.renderer.add_text(page, "Example", ctx.layout.content_left, example_start_y, font_header)
    title_width = ctx.renderer.get_text_width("Example", font_header)
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_width + 15, example_start_y + font_header * 0.5),
        fitz.Point(ctx.layout.content_right, example_start_y + font_header * 0.5),
        color=ctx.theme.gray,
        width=0.5,
    )

    # Scenario subtitle
    subtitle_y = example_start_y + 50
    ctx.renderer.add_text(page, "Planning a Surprise Party", ctx.layout.content_left, subtitle_y, font_section, ctx.theme.gray, italic=True)

    # Calculate row parameters to fill available space
    header_y = subtitle_y + 50
    num_rows = 8
    row_area_height = available_height - (header_y - example_start_y) - 50
    line_h = row_area_height // num_rows  # Dynamic row height

    # Font sizes - larger for better fill
    font_hw = 34
    font_note = 16

    # Two-column layout
    col_gap = 50
    left_col_width = 380
    right_col_x = ctx.layout.content_left + left_col_width + col_gap

    # Column headers with underline
    ctx.renderer.add_text(page, "Recorded", ctx.layout.content_left, header_y, font_section)
    ctx.renderer.add_text(page, "After reflection", right_col_x, header_y, font_section)

    # Subtle header underline
    underline_y = header_y + 35
    page.draw_line(
        fitz.Point(ctx.layout.content_left, underline_y),
        fitz.Point(ctx.layout.content_left + left_col_width - 30, underline_y),
        color=ctx.theme.gray,
        width=0.5,
    )
    page.draw_line(
        fitz.Point(right_col_x, underline_y),
        fitz.Point(ctx.layout.content_right, underline_y),
        color=ctx.theme.gray,
        width=0.5,
    )

    example_y = underline_y + 20

    # Symbol alignment columns for left side
    sig_col = 0
    name_col = 35
    text_col = 70

    # Symbol size for example - larger
    ex_dot_r = 6
    ex_arrow = 13
    ex_x = 13

    def draw_ex_dot(x: float, y: float) -> None:
        page.draw_circle(fitz.Point(x + ex_dot_r, y), ex_dot_r, color=ctx.theme.black, fill=ctx.theme.black)

    def draw_ex_dash(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x, y), fitz.Point(x + 18, y), color=ctx.theme.black, width=2.8)

    def draw_ex_double(x: float, y: float) -> None:
        for offset in [-6, 6]:
            page.draw_line(fitz.Point(x, y + offset), fitz.Point(x + 18, y + offset), color=ctx.theme.black, width=2.2)

    def draw_ex_circle(x: float, y: float) -> None:
        page.draw_circle(fitz.Point(x + 8, y), 8, color=ctx.theme.black, width=2.8)

    def draw_ex_x(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x, y - ex_x / 2), fitz.Point(x + ex_x, y + ex_x / 2), color=ctx.theme.black, width=2.8)
        page.draw_line(fitz.Point(x, y + ex_x / 2), fitz.Point(x + ex_x, y - ex_x / 2), color=ctx.theme.black, width=2.8)

    def draw_ex_migrate(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x, y - ex_arrow / 2), fitz.Point(x + ex_arrow, y), color=ctx.theme.black, width=2.8)
        page.draw_line(fitz.Point(x, y + ex_arrow / 2), fitz.Point(x + ex_arrow, y), color=ctx.theme.black, width=2.8)

    def draw_ex_schedule(x: float, y: float) -> None:
        page.draw_line(fitz.Point(x + ex_arrow, y - ex_arrow / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.8)
        page.draw_line(fitz.Point(x + ex_arrow, y + ex_arrow / 2), fitz.Point(x, y), color=ctx.theme.black, width=2.8)

    # Example rows - each with clear structure
    left_x = ctx.layout.content_left

    # Row 1: Priority Action -> Completed
    sym_y = example_y + font_hw * 0.5
    ctx.renderer.draw_star(page, left_x + sig_col + 10, sym_y, 14)
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Book venue", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_x(right_col_x + 3, sym_y)
    ctx.renderer.add_text(page, "completed", right_col_x + 28, example_y + 10, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 2: Action -> Migrated
    sym_y = example_y + font_hw * 0.5
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Order cake", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_migrate(right_col_x, sym_y)
    ctx.renderer.add_text(page, "moved to tomorrow", right_col_x + 28, example_y + 10, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 3: Action -> Scheduled
    sym_y = example_y + font_hw * 0.5
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Buy balloons", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_schedule(right_col_x, sym_y)
    ctx.renderer.add_text(page, "scheduled to Friday", right_col_x + 28, example_y + 10, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 4: Action -> Irrelevant
    sym_y = example_y + font_hw * 0.5
    draw_ex_dot(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Print invites", left_x + text_col, example_y, font_hw, italic=True)
    striketext = "Print invites"
    ctx.renderer.add_text(page, striketext, right_col_x, example_y, font_hw, italic=True)
    strike_w = ctx.renderer.get_text_width(striketext, font_hw)
    page.draw_line(fitz.Point(right_col_x, sym_y), fitz.Point(right_col_x + strike_w, sym_y), color=ctx.theme.black, width=1.5)
    ctx.renderer.add_text(page, "use group chat", right_col_x + strike_w + 15, example_y + 10, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 5: Explore Note -> spawns new action
    sym_y = example_y + font_hw * 0.5
    ctx.renderer.draw_eye(page, left_x + sig_col + 10, sym_y, 14)
    draw_ex_dash(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "Music options?", left_x + text_col, example_y, font_hw, italic=True)
    draw_ex_dot(right_col_x + 3, sym_y)
    ctx.renderer.add_text(page, "Ask Tom for playlist", right_col_x + 28, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "new action", right_col_x + 28, example_y + font_hw * 0.95, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 6: Inspiration Note -> unchanged
    sym_y = example_y + font_hw * 0.55
    ctx.renderer.draw_lightbulb(page, left_x + sig_col + 10, sym_y, 14)
    draw_ex_dash(left_x + name_col, sym_y)
    ctx.renderer.add_text(page, "80s theme!", left_x + text_col, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "(unchanged)", right_col_x, example_y + 10, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 7: Event -> immutable
    sym_y = example_y + font_hw * 0.5
    draw_ex_circle(left_x + name_col - 3, sym_y)
    ctx.renderer.add_text(page, "Party 6pm", left_x + text_col, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "(events are facts)", right_col_x, example_y + 10, font_note, ctx.theme.gray, italic=True)
    example_y += line_h

    # Row 8: Mood -> acknowledge marker
    sym_y = example_y + font_hw * 0.5
    draw_ex_double(left_x + name_col - 3, sym_y)
    ctx.renderer.add_text(page, "Nervous", left_x + text_col, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "^", right_col_x + 6, example_y, font_hw, italic=True)
    ctx.renderer.add_text(page, "moved toward my goal", right_col_x + 35, example_y + 10, font_note, ctx.theme.gray, italic=True)


def generate_guide_system(ctx: PageContext, page_idx: int) -> None:
    """Generate The System page - elegant card-based layout for N.A.M.E. framework."""
    page = ctx.renderer.doc[page_idx]
    font_body = 22
    font_section = 20
    font_small = 18
    line_height = 1.45

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "The System", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 100

    # Introduction - concise
    intro_text = (
        "The Bullet Journal Method is a mindfulness practice designed to work like a productivity system. "
        "Use |Rapid Logging| to capture thoughts quickly with minimal syntax."
    )
    height = ctx.renderer.draw_rich_text(page, intro_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 20, line_height)
    y += height + 30

    # N.A.M.E. Section with decorative title
    ctx.renderer.add_text(page, "N.A.M.E.", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("N.A.M.E.", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 40

    # N.A.M.E. cards - 2x2 grid with larger cards
    card_gap = 25
    card_width = (ctx.layout.content_width - card_gap) // 2
    card_height = 160
    card_padding = 22

    name_items = [
        ("N", "Notes", "dash", "Ideas, insights, information to remember. Capture what you learn."),
        ("A", "Actions", "dot", "Things to do - your tasks. The backbone of your productivity."),
        ("M", "Moods", "double", "How you feel, emotionally or physically. Track your inner state."),
        ("E", "Events", "circle", "Experiences, appointments, milestones. Record what happens."),
    ]

    positions = [
        (ctx.layout.content_left, y),
        (ctx.layout.content_left + card_width + card_gap, y),
        (ctx.layout.content_left, y + card_height + card_gap),
        (ctx.layout.content_left + card_width + card_gap, y + card_height + card_gap),
    ]

    def draw_symbol(sym_type: str, cx: float, cy: float, size: int = 20) -> None:
        if sym_type == "dash":
            page.draw_line(fitz.Point(cx - size / 2, cy), fitz.Point(cx + size / 2, cy), color=ctx.theme.black, width=3)
        elif sym_type == "dot":
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, fill=ctx.theme.black)
        elif sym_type == "double":
            for offset in [-size / 4, size / 4]:
                page.draw_line(fitz.Point(cx - size / 2, cy + offset), fitz.Point(cx + size / 2, cy + offset), color=ctx.theme.black, width=2.5)
        elif sym_type == "circle":
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, width=2.5)

    for i, (letter, name, sym_type, desc) in enumerate(name_items):
        cx, cy = positions[i]
        # Card border
        page.draw_rect(
            fitz.Rect(cx, cy, cx + card_width, cy + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )
        # Large letter
        letter_x = cx + card_padding
        letter_y = cy + card_padding
        ctx.renderer.add_text(page, letter, letter_x, letter_y, 42)
        # Symbol after letter - increased spacing to prevent overlap
        sym_x = letter_x + 55
        sym_y = letter_y + 26
        draw_symbol(sym_type, sym_x, sym_y, 22)
        # Name - adjusted position for new symbol spacing
        ctx.renderer.add_text(page, name, cx + card_padding + 90, letter_y + 8, font_section + 2)
        # Description - multi-line
        ctx.renderer.draw_rich_text(page, desc, cx + card_padding, cy + card_padding + 60, font_small, card_width - card_padding * 2, 1.4)

    y = positions[2][1] + card_height + 40

    # Action States - horizontal flow with clearer design
    ctx.renderer.add_text(page, "Action States", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("Action States", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 30

    # Explanation text
    action_intro = "A dot can transform to reflect multiple states. Each transformation is a moment of reflection."
    ctx.renderer.add_text(page, action_intro, ctx.layout.content_left, y, font_small, ctx.theme.gray, italic=True)
    y += 35

    # Flow diagram - 5 states in a row
    flow_y = y + 30
    state_spacing = ctx.layout.content_width // 5
    states = [
        ("Incomplete", "dot"),
        ("Complete", "x"),
        ("Migrated", "arrow_r"),
        ("Scheduled", "arrow_l"),
        ("Irrelevant", "strike"),
    ]

    def draw_state_symbol(sym_type: str, cx: float, cy: float, size: int = 16) -> None:
        if sym_type == "dot":
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, fill=ctx.theme.black)
        elif sym_type == "x":
            hs = size / 2
            page.draw_line(fitz.Point(cx - hs, cy - hs), fitz.Point(cx + hs, cy + hs), color=ctx.theme.black, width=2.8)
            page.draw_line(fitz.Point(cx - hs, cy + hs), fitz.Point(cx + hs, cy - hs), color=ctx.theme.black, width=2.8)
        elif sym_type == "arrow_r":
            page.draw_line(fitz.Point(cx - size / 2, cy - size / 3), fitz.Point(cx + size / 2, cy), color=ctx.theme.black, width=2.8)
            page.draw_line(fitz.Point(cx - size / 2, cy + size / 3), fitz.Point(cx + size / 2, cy), color=ctx.theme.black, width=2.8)
        elif sym_type == "arrow_l":
            page.draw_line(fitz.Point(cx + size / 2, cy - size / 3), fitz.Point(cx - size / 2, cy), color=ctx.theme.black, width=2.8)
            page.draw_line(fitz.Point(cx + size / 2, cy + size / 3), fitz.Point(cx - size / 2, cy), color=ctx.theme.black, width=2.8)
        elif sym_type == "strike":
            # Dot with strikethrough extending to the right (simulating crossed-out text)
            page.draw_circle(fitz.Point(cx, cy), size / 3, color=ctx.theme.black, fill=ctx.theme.black)
            page.draw_line(fitz.Point(cx + size / 2, cy), fitz.Point(cx + size * 2.5, cy), color=ctx.theme.black, width=1.5)

    # Draw states
    for i, (name, sym_type) in enumerate(states):
        sx = ctx.layout.content_left + state_spacing * i + state_spacing // 2
        # Symbol
        draw_state_symbol(sym_type, sx, flow_y, 16)
        # Label below
        label_w = ctx.renderer.get_text_width(name, font_small)
        ctx.renderer.add_text(page, name, sx - label_w // 2, flow_y + 30, font_small)

    # Draw connecting line from Incomplete through all states
    first_x = ctx.layout.content_left + state_spacing // 2 + 20
    last_x = ctx.layout.content_left + state_spacing * 4 + state_spacing // 2 - 20
    page.draw_line(
        fitz.Point(first_x, flow_y),
        fitz.Point(last_x, flow_y),
        color=ctx.theme.gray,
        width=1,
        dashes="[4 4]",
    )

    y = flow_y + 75

    # Signifiers section - larger cards
    ctx.renderer.add_text(page, "Signifiers", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("Signifiers", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 30

    signifier_intro = "Add context to any bullet by placing a signifier in front:"
    ctx.renderer.add_text(page, signifier_intro, ctx.layout.content_left, y, font_small, ctx.theme.gray, italic=True)
    y += 35

    # Signifier cards - 3 columns, taller
    sig_card_gap = 25
    sig_card_width = (ctx.layout.content_width - sig_card_gap * 2) // 3
    sig_card_height = 140
    sig_padding = 20

    signifiers = [
        ("star", "Priority", "Important and urgent"),
        ("lightbulb", "Inspiration", "Great idea worth remembering"),
        ("eye", "Explore", "Requires further research"),
    ]

    for i, (icon_type, name, desc) in enumerate(signifiers):
        sx = ctx.layout.content_left + (sig_card_width + sig_card_gap) * i
        # Card
        page.draw_rect(
            fitz.Rect(sx, y, sx + sig_card_width, y + sig_card_height),
            color=ctx.theme.gray,
            width=0.5,
        )
        # Icon centered at top - larger
        icon_cx = sx + sig_card_width // 2
        icon_cy = y + sig_padding + 25
        if icon_type == "star":
            ctx.renderer.draw_star(page, icon_cx, icon_cy, 24)
        elif icon_type == "lightbulb":
            ctx.renderer.draw_lightbulb(page, icon_cx, icon_cy, 24)
        elif icon_type == "eye":
            ctx.renderer.draw_eye(page, icon_cx, icon_cy, 24)
        # Name centered
        name_w = ctx.renderer.get_text_width(name, font_section + 4)
        ctx.renderer.add_text(page, name, icon_cx - name_w // 2, y + sig_padding + 60, font_section + 4)
        # Description centered
        desc_w = ctx.renderer.get_text_width(desc, font_small)
        ctx.renderer.add_text(page, desc, icon_cx - desc_w // 2, y + sig_padding + 95, font_small, ctx.theme.gray)

    y += sig_card_height + 35

    # Footer note with more substance
    custom_text = "Define your own signifiers as your practice evolves. Keep it minimal - too many symbols slow you down."
    ctx.renderer.add_text(page, custom_text, ctx.layout.content_left, y, font_small, ctx.theme.gray, italic=True)
    y += 40

    # Key insight box - increased height and padding
    insight_y = y
    insight_height = 120
    insight_padding = 25
    page.draw_rect(
        fitz.Rect(ctx.layout.content_left, insight_y, ctx.layout.content_right, insight_y + insight_height),
        color=ctx.theme.gray,
        width=0.5,
    )
    # Quote mark or title - more vertical padding
    ctx.renderer.add_text(page, "The Core Insight", ctx.layout.content_left + insight_padding, insight_y + insight_padding, font_section + 2)
    # Insight text - more spacing from title
    insight_text = (
        "The power of Bullet Journal lies not in the symbols, but in the reflection they encourage. "
        "Every time you transform a bullet, you ask: does this still deserve my time and attention?"
    )
    ctx.renderer.draw_rich_text(
        page, insight_text,
        ctx.layout.content_left + insight_padding, insight_y + 60,
        font_small + 1, ctx.layout.content_width - insight_padding * 2, 1.45
    )


def generate_guide_set_up_logs(ctx: PageContext, page_idx: int) -> None:
    """Generate Set up your logs page with elegant card-based layout."""
    page = ctx.renderer.doc[page_idx]
    font_body = 22
    font_small = 19
    font_section = 20
    line_height = 1.45
    card_padding = 20

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Set up your logs", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Calculate card dimensions to fill available space evenly
    y_start = ctx.layout.content_top + 120
    available_height = ctx.layout.content_bottom - y_start - 30
    card_gap = 20
    num_cards = 4
    card_height = (available_height - card_gap * (num_cards - 1)) // num_cards
    card_width = ctx.layout.content_width

    # Log definitions with descriptions
    logs = [
        {
            "name": "Future log",
            "link_target": ctx.page_map.future_log_start,
            "description": "The Future Log lets you see your future. Store |actions| and |events| that fall outside the current month. It provides an overview of your commitments over time.",
            "columns": None,
        },
        {
            "name": "Monthly log",
            "link_target": ctx.page_map.monthly_start,
            "description": "Two pages to reset, reprioritize, and recommit to what you allow into your life every month.",
            "columns": [
                ("Timeline", "Log events after they've happened. An accurate record of your life."),
                ("Action Plan", "Organize and prioritize monthly |Tasks.| New tasks and Future Log items."),
            ],
        },
        {
            "name": "Weekly log",
            "link_target": ctx.page_map.weekly_start,
            "description": None,
            "columns": [
                ("Reflection", "Tidy entries. Acknowledge what moved you toward and away. Migrate relevant |Actions.|"),
                ("Action plan", "Write only what you can get done this week. Number your top three priorities."),
            ],
        },
        {
            "name": "Daily log",
            "link_target": ctx.page_map.daily_start,
            "description": "Declutter your mind and stay focused. |Rapid Log| your thoughts as they bubble up. This is your main workspace - the heart of daily practice.",
            "columns": None,
        },
    ]

    y = y_start
    for log in logs:
        # Draw card border
        page.draw_rect(
            fitz.Rect(ctx.layout.content_left, y, ctx.layout.content_left + card_width, y + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )

        # Log name with decorative line
        name_y = y + card_padding
        ctx.renderer.add_text(page, log["name"], ctx.layout.content_left + card_padding, name_y, ctx.typography.sizes["subheader"])
        title_w = ctx.renderer.get_text_width(log["name"], ctx.typography.sizes["subheader"])

        # Get started link at right side
        get_started_text = "Get started"
        get_started_w = ctx.renderer.get_text_width(get_started_text, font_small)
        get_started_x = ctx.layout.content_right - card_padding - get_started_w - 25
        ctx.renderer.add_text(page, get_started_text, get_started_x, name_y, font_small)
        ctx.renderer.draw_arrow_right(page, ctx.layout.content_right - card_padding - 10, name_y + font_small / 2, ctx.typography.arrow_size_small)

        # Decorative line between title and "Get started"
        line_start_x = ctx.layout.content_left + card_padding + title_w + 15
        line_end_x = get_started_x - 20
        page.draw_line(
            fitz.Point(line_start_x, name_y + ctx.typography.sizes["subheader"] * 0.45),
            fitz.Point(line_end_x, name_y + ctx.typography.sizes["subheader"] * 0.45),
            color=ctx.theme.gray,
            width=0.5,
        )

        # Link for entire header area
        link_rect = (get_started_x - 5, name_y - 5, ctx.layout.content_right - card_padding, name_y + font_small + 10)
        ctx.renderer.links.add(page_idx, link_rect, log["link_target"])

        content_y = name_y + ctx.typography.sizes["subheader"] + 15

        if log["description"]:
            # Single description
            ctx.renderer.draw_rich_text(
                page, log["description"],
                ctx.layout.content_left + card_padding, content_y,
                font_body, card_width - card_padding * 2, line_height
            )

        if log["columns"]:
            # Two-column layout
            col_gap = 30
            col_width = (card_width - card_padding * 2 - col_gap) // 2
            col1_x = ctx.layout.content_left + card_padding
            col2_x = col1_x + col_width + col_gap

            # If there's a description, start columns lower
            if log["description"]:
                content_y += font_body * line_height * 2 + 10

            for i, (col_title, col_desc) in enumerate(log["columns"]):
                col_x = col1_x if i == 0 else col2_x
                # Column title (italic)
                ctx.renderer.add_text(page, col_title, col_x, content_y, font_section, italic=True)
                # Column description
                ctx.renderer.draw_rich_text(
                    page, col_desc,
                    col_x, content_y + font_section * 1.3,
                    font_small, col_width - 10, line_height
                )

        y += card_height + card_gap


def generate_guide_practice(ctx: PageContext, page_idx: int) -> None:
    """Generate The Practice page - T.A.M.E. framework with elegant card-based layout."""
    page = ctx.renderer.doc[page_idx]
    font_body = 22
    font_section = 20
    font_small = 18
    line_height = 1.45

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "The Practice", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    y = ctx.layout.content_top + 100

    # Introduction - emphasizing N.A.M.E. -> T.A.M.E. cycle
    intro_text = (
        "|N.A.M.E.| captures your experiences. |T.A.M.E.| transforms them into clarity and action. "
        "Recording feeds reflection; reflection guides recording. This cycle is the heart of the practice."
    )
    height = ctx.renderer.draw_rich_text(page, intro_text, ctx.layout.content_left, y, font_body, ctx.layout.content_width - 20, line_height)
    y += height + 30

    # T.A.M.E. Section with decorative title
    ctx.renderer.add_text(page, "T.A.M.E.", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("T.A.M.E.", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 40

    # Card layout - 2x2 grid with larger cards
    card_gap = 25
    card_width = (ctx.layout.content_width - card_gap) // 2
    card_height = 165
    card_padding = 22

    cards = [
        ("T", "Tidy", "x", "Cross off completed tasks. Strike through what no longer matters. Clear space before moving forward."),
        ("A", "Acknowledge", "updown", "Look back at what happened. Mark things that moved you toward or away from your goals."),
        ("M", "Migrate", "arrow", "Carry forward what still matters. Rewriting confirms your commitment to each task."),
        ("E", "Enact", "play", "Turn insights into action. Set clear priorities for the next day, week, or month."),
    ]

    positions = [
        (ctx.layout.content_left, y),
        (ctx.layout.content_left + card_width + card_gap, y),
        (ctx.layout.content_left, y + card_height + card_gap),
        (ctx.layout.content_left + card_width + card_gap, y + card_height + card_gap),
    ]

    def draw_tame_symbol(sym_type: str, cx: float, cy: float, size: int = 20) -> None:
        if sym_type == "x":
            # X mark for Tidy (crossing off)
            hs = size * 0.4
            page.draw_line(fitz.Point(cx - hs, cy - hs), fitz.Point(cx + hs, cy + hs), color=ctx.theme.black, width=3)
            page.draw_line(fitz.Point(cx - hs, cy + hs), fitz.Point(cx + hs, cy - hs), color=ctx.theme.black, width=3)
        elif sym_type == "updown":
            # Up and down arrows for Acknowledge (toward/away)
            # Up arrow
            page.draw_line(fitz.Point(cx - size * 0.2, cy - size * 0.15), fitz.Point(cx - size * 0.2, cy + size * 0.35), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx - size * 0.35, cy + size * 0.05), fitz.Point(cx - size * 0.2, cy - size * 0.25), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx - size * 0.05, cy + size * 0.05), fitz.Point(cx - size * 0.2, cy - size * 0.25), color=ctx.theme.black, width=2.5)
            # Down arrow
            page.draw_line(fitz.Point(cx + size * 0.2, cy - size * 0.35), fitz.Point(cx + size * 0.2, cy + size * 0.15), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.05, cy - size * 0.05), fitz.Point(cx + size * 0.2, cy + size * 0.25), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.35, cy - size * 0.05), fitz.Point(cx + size * 0.2, cy + size * 0.25), color=ctx.theme.black, width=2.5)
        elif sym_type == "arrow":
            # Forward arrow for Migrate
            page.draw_line(fitz.Point(cx - size * 0.35, cy), fitz.Point(cx + size * 0.35, cy), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.1, cy - size * 0.3), fitz.Point(cx + size * 0.4, cy), color=ctx.theme.black, width=2.5)
            page.draw_line(fitz.Point(cx + size * 0.1, cy + size * 0.3), fitz.Point(cx + size * 0.4, cy), color=ctx.theme.black, width=2.5)
        elif sym_type == "play":
            # Play/action triangle for Enact
            pts = [
                fitz.Point(cx - size * 0.25, cy - size * 0.35),
                fitz.Point(cx - size * 0.25, cy + size * 0.35),
                fitz.Point(cx + size * 0.35, cy),
            ]
            page.draw_polyline(pts + [pts[0]], color=ctx.theme.black, width=2.5, closePath=True)

    for i, (letter, name, sym_type, desc) in enumerate(cards):
        cx, cy = positions[i]
        # Card border - subtle gray like The System page
        page.draw_rect(
            fitz.Rect(cx, cy, cx + card_width, cy + card_height),
            color=ctx.theme.gray,
            width=0.5,
        )
        # Large letter
        letter_x = cx + card_padding
        letter_y = cy + card_padding
        ctx.renderer.add_text(page, letter, letter_x, letter_y, 42)
        # Symbol after letter
        sym_x = letter_x + 55
        sym_y = letter_y + 26
        draw_tame_symbol(sym_type, sym_x, sym_y, 22)
        # Name - adjusted position
        ctx.renderer.add_text(page, name, cx + card_padding + 90, letter_y + 8, font_section + 2)
        # Description - multi-line
        ctx.renderer.draw_rich_text(page, desc, cx + card_padding, cy + card_padding + 60, font_small, card_width - card_padding * 2, 1.4)

    y = positions[2][1] + card_height + 40

    # Reflection Rhythm section with decorative title
    ctx.renderer.add_text(page, "Reflection Rhythm", ctx.layout.content_left, y, ctx.typography.sizes["subheader"])
    title_w = ctx.renderer.get_text_width("Reflection Rhythm", ctx.typography.sizes["subheader"])
    page.draw_line(
        fitz.Point(ctx.layout.content_left + title_w + 15, y + ctx.typography.sizes["subheader"] * 0.45),
        fitz.Point(ctx.layout.content_right, y + ctx.typography.sizes["subheader"] * 0.45),
        color=ctx.theme.gray,
        width=0.5,
    )
    y += 35

    font_rhythm = 20
    rhythm_line_height = 1.5

    # Daily with digital hint
    ctx.renderer.draw_rich_text(page, "|Daily:| Morning and evening - quick review and planning.", ctx.layout.content_left + 20, y, font_rhythm, ctx.layout.content_width - 60, rhythm_line_height)
    y += font_rhythm * rhythm_line_height + 5
    ctx.renderer.add_text(page, "For deeper reflection, use a digital journal or note-taking app.", ctx.layout.content_left + 40, y, font_rhythm - 2, ctx.theme.gray, italic=True)
    y += font_rhythm * rhythm_line_height + 10

    # Weekly with new suggestion
    height = ctx.renderer.draw_rich_text(page, "|Weekly:| Sunday evening - tidy the week, acknowledge progress.", ctx.layout.content_left + 20, y, font_rhythm, ctx.layout.content_width - 60, rhythm_line_height)
    y += height + 5
    ctx.renderer.add_text(page, "Review what worked and what didn't. Adjust your approach for next week.", ctx.layout.content_left + 40, y, font_rhythm - 2, ctx.theme.gray, italic=True)
    y += font_rhythm * rhythm_line_height + 10

    # Monthly with digital hint
    height = ctx.renderer.draw_rich_text(page, "|Monthly:| End of month - identify patterns, adjust direction.", ctx.layout.content_left + 20, y, font_rhythm, ctx.layout.content_width - 60, rhythm_line_height)
    y += height + 5
    ctx.renderer.add_text(page, "Consider a longer writing session to explore what you've learned.", ctx.layout.content_left + 40, y, font_rhythm - 2, ctx.theme.gray, italic=True)


def generate_guide_intention(ctx: PageContext, page_idx: int) -> None:
    """Generate Intention page - minimalist design with maximum writing space."""
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Intention", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Maximize dot grid space - extend to just above footer
    grid_top = ctx.layout.content_top + 100
    grid_bottom = ctx.layout.target_height - 70  # Leave space for footer
    ctx.renderer.draw_dot_grid(page, grid_top, grid_bottom)

    # Unified footer section
    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["intention"])


def generate_guide_goals(ctx: PageContext, page_idx: int) -> None:
    """Generate Goals page - minimalist design with maximum writing space."""
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Goals", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["header"])

    # Maximize dot grid space - extend to just above footer
    grid_top = ctx.layout.content_top + 100
    grid_bottom = ctx.layout.target_height - 70  # Leave space for footer
    ctx.renderer.draw_dot_grid(page, grid_top, grid_bottom)

    # Unified footer section
    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["goals"])


def generate_future_log(ctx: PageContext, page_idx: int, quarter: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Future Log", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    start_idx = (quarter - 1) * 3
    months = ctx.calendar.months[start_idx:start_idx + 3]

    # Extend dot grid to just above footer (footer starts at target_height - 55)
    grid_start_y = ctx.layout.content_top + 115
    grid_end_y = ctx.layout.target_height - 70

    ctx.renderer.draw_dot_grid(page, grid_start_y, grid_end_y)

    # Distribute available space evenly among 3 months
    available_height = grid_end_y - grid_start_y
    month_height = available_height // 3

    for i, month in enumerate(months):
        my = grid_start_y + i * month_height
        ctx.renderer.add_text(page, month.name, ctx.layout.content_left, my, ctx.typography.sizes["body"])
        page.draw_line(
            fitz.Point(ctx.layout.content_left, my + 45),
            fitz.Point(ctx.layout.content_right, my + 45),
            color=ctx.theme.black,
            width=0.5,
        )

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["future_log"])


def generate_monthly_timeline(ctx: PageContext, page_idx: int, month_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    month = ctx.calendar.months[month_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, month.name, ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    # Extend dot grid to just above footer
    grid_start_y = ctx.layout.content_top + 115
    grid_end_y = ctx.layout.target_height - 70

    ctx.renderer.draw_dot_grid(page, grid_start_y, grid_end_y)

    # Distribute day numbers evenly in available height
    available_height = grid_end_y - grid_start_y
    day_height = available_height / month.days

    for day in range(1, month.days + 1):
        day_y = grid_start_y + (day - 1) * day_height + ctx.typography.sizes["day_number"] / 2
        ctx.renderer.add_text(page, str(day), ctx.layout.content_left, day_y, ctx.typography.sizes["day_number"])

        day_of_year = ctx.calendar.day_of_year(month_idx, day)
        dest_page = ctx.page_map.daily_page(day_of_year)
        link_rect = (
            ctx.layout.content_left - 5,
            day_y - 5,
            ctx.layout.content_left + 35,
            day_y + ctx.typography.sizes["day_number"] + 5,
        )
        ctx.renderer.links.add(page_idx, link_rect, dest_page)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["monthly_timeline"])
    ctx.renderer.add_bottom_nav(page_idx, [("Year", ctx.page_map.year_index)])


def generate_monthly_action_plan(ctx: PageContext, page_idx: int, month_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]
    month = ctx.calendar.months[month_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, month.name, ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["monthly_action"])


def draw_date_range_input(ctx: PageContext, page: fitz.Page, x: float, y: float, font_size: float = 24) -> None:
    line_width = 25
    slash_spacing = 8

    current_x = x
    line_y = y + font_size - 2

    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )
    current_x += line_width + slash_spacing
    ctx.renderer.add_text(page, "/", current_x, y, font_size, ctx.theme.black)
    current_x += 12
    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )
    current_x += line_width + 20

    ctx.renderer.add_text(page, "to", current_x, y, font_size, ctx.theme.black, italic=True)
    current_x += 30

    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )
    current_x += line_width + slash_spacing
    ctx.renderer.add_text(page, "/", current_x, y, font_size, ctx.theme.black)
    current_x += 12
    page.draw_line(
        fitz.Point(current_x, line_y),
        fitz.Point(current_x + line_width, line_y),
        color=ctx.theme.gray,
        width=0.8,
    )


def generate_weekly_action_plan(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Weekly Action plan", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    draw_date_range_input(ctx, page, ctx.layout.content_right - 220, ctx.layout.content_top + 55, 22)

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["weekly_action"])


def generate_weekly_reflection(ctx: PageContext, page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.main_index, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.add_text(page, "Weekly Reflection", ctx.layout.content_left, ctx.layout.content_top + 50, ctx.typography.sizes["title_page"])

    draw_date_range_input(ctx, page, ctx.layout.content_right - 220, ctx.layout.content_top + 55, 22)

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 115, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["weekly_reflection"])


def generate_daily_log(ctx: PageContext, page_idx: int, month_idx: int, day: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.year_index, ctx.layout.content_left, ctx.layout.content_top + 5)

    week_num = ctx.calendar.week_of_date(month_idx, day)
    week_label = f"W{week_num}"
    week_page = ctx.page_map.weekly_action(week_num - 1)
    week_x = ctx.layout.content_left + 80
    ctx.renderer.add_nav_link(page_idx, week_label, week_page, week_x, ctx.layout.content_top + 5)

    month_name = ctx.calendar.months[month_idx].name
    monthly_page = ctx.page_map.month_timeline(month_idx)
    monthly_text_width = ctx.renderer.get_text_width(month_name, ctx.typography.sizes["nav"])
    ctx.renderer.add_nav_link(
        page_idx,
        month_name,
        monthly_page,
        ctx.layout.content_right - monthly_text_width - 40,
        ctx.layout.content_top + 5,
    )

    date_label = ctx.calendar.date_label(month_idx, day)
    ctx.renderer.add_text(page, date_label, ctx.layout.content_left, ctx.layout.content_top + 70, ctx.typography.sizes["title_page"])

    # Extend dot grid to just above footer
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 145, ctx.layout.target_height - 70)

    ctx.renderer.draw_footer_section(page, FOOTER_TEXTS["daily_log"])


def generate_daily_log_continuation(ctx: PageContext, page_idx: int, month_idx: int, day: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", ctx.page_map.year_index, ctx.layout.content_left, ctx.layout.content_top + 5)

    week_num = ctx.calendar.week_of_date(month_idx, day)
    week_label = f"W{week_num}"
    week_page = ctx.page_map.weekly_action(week_num - 1)
    week_x = ctx.layout.content_left + 80
    ctx.renderer.add_nav_link(page_idx, week_label, week_page, week_x, ctx.layout.content_top + 5)

    month_name = ctx.calendar.months[month_idx].name
    monthly_page = ctx.page_map.month_timeline(month_idx)
    monthly_text_width = ctx.renderer.get_text_width(month_name, ctx.typography.sizes["nav"])
    ctx.renderer.add_nav_link(
        page_idx,
        month_name,
        monthly_page,
        ctx.layout.content_right - monthly_text_width - 40,
        ctx.layout.content_top + 5,
    )

    date_label = ctx.calendar.date_label(month_idx, day)
    ctx.renderer.add_text(page, date_label, ctx.layout.content_left, ctx.layout.content_top + 70, ctx.typography.sizes["title_page"])

    # Continuation pages have no footer, extend grid closer to bottom
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 145, ctx.layout.target_height - 50)


def generate_collection_page(ctx: PageContext, page_idx: int, index_page_idx: int) -> None:
    page = ctx.renderer.doc[page_idx]

    ctx.renderer.add_nav_link(page_idx, "Index", index_page_idx, ctx.layout.content_left, ctx.layout.content_top + 5)
    ctx.renderer.draw_dot_grid(page, ctx.layout.content_top + 50, ctx.layout.content_bottom - 30)
