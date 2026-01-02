from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import fitz

from ..config import Layout, Theme, Typography
from ..link_manager import LinkManager


@dataclass(frozen=True)
class FontSpec:
    name: str
    font: fitz.Font
    file: Optional[Path]


class FontManager:
    def __init__(self, typography: Typography, asset_root: Path) -> None:
        self.typography = typography
        self.asset_root = asset_root
        self._resolved = False
        self._regular: Optional[FontSpec] = None
        self._italic: Optional[FontSpec] = None
        self._missing: list[str] = []

    def resolve(self) -> None:
        if self._resolved:
            return

        regular_path = self.asset_root / self.typography.font_path_regular
        italic_path = self.asset_root / self.typography.font_path_italic

        if regular_path.exists():
            regular_font = fitz.Font(fontfile=str(regular_path))
            self._regular = FontSpec(self.typography.font_name_regular, regular_font, regular_path)
        else:
            self._missing.append(str(regular_path))
            regular_font = fitz.Font(fontname=self.typography.fallback_regular)
            self._regular = FontSpec(self.typography.fallback_regular, regular_font, None)

        if italic_path.exists():
            italic_font = fitz.Font(fontfile=str(italic_path))
            self._italic = FontSpec(self.typography.font_name_italic, italic_font, italic_path)
        else:
            self._missing.append(str(italic_path))
            italic_font = fitz.Font(fontname=self.typography.fallback_italic)
            self._italic = FontSpec(self.typography.fallback_italic, italic_font, None)

        self._resolved = True

    def missing_fonts(self) -> list[str]:
        self.resolve()
        return list(self._missing)

    def font(self, italic: bool = False) -> FontSpec:
        self.resolve()
        return self._italic if italic else self._regular  # type: ignore[return-value]

    def register_page(self, page: fitz.Page) -> None:
        self.resolve()
        for spec in (self._regular, self._italic):
            if spec and spec.file is not None:
                page.insert_font(fontname=spec.name, fontfile=str(spec.file))

    def text_length(self, text: str, font_size: float, italic: bool = False) -> float:
        spec = self.font(italic=italic)
        return spec.font.text_length(text, fontsize=font_size)


class Renderer:
    def __init__(
        self,
        doc: fitz.Document,
        layout: Layout,
        theme: Theme,
        typography: Typography,
        font_manager: FontManager,
        links: LinkManager,
    ) -> None:
        self.doc = doc
        self.layout = layout
        self.theme = theme
        self.typography = typography
        self.font_manager = font_manager
        self.links = links

    def add_text(
        self,
        page: fitz.Page,
        text: str,
        x: float,
        y: float,
        font_size: float = 24,
        color: Tuple = None,
        italic: bool = False,
    ) -> None:
        if color is None:
            color = self.theme.black
        self.font_manager.register_page(page)
        spec = self.font_manager.font(italic=italic)
        page.insert_text(
            fitz.Point(x, y + font_size),
            text,
            fontsize=font_size,
            fontname=spec.name,
            fontfile=str(spec.file) if spec.file is not None else None,
            color=color,
        )

    def get_text_width(self, text: str, font_size: float, italic: bool = False) -> float:
        return self.font_manager.text_length(text, font_size, italic=italic)

    def draw_rich_text(
        self,
        page: fitz.Page,
        text: str,
        x: float,
        y: float,
        font_size: float = 22,
        max_width: Optional[float] = None,
        line_height: float = 1.4,
    ) -> float:
        if max_width is None:
            max_width = self.layout.content_width - 60

        parts = text.split("|")
        words_with_style = []

        for i, part in enumerate(parts):
            is_italic = (i % 2 == 1)
            for word in part.split():
                words_with_style.append((word, is_italic))

        current_x = x
        current_y = y
        space_width = self.get_text_width(" ", font_size)

        for word, is_italic in words_with_style:
            word_width = self.get_text_width(word, font_size, italic=is_italic)

            if current_x + word_width > x + max_width:
                current_x = x
                current_y += font_size * line_height

            self.add_text(page, word, current_x, current_y, font_size, self.theme.black, italic=is_italic)
            current_x += word_width + space_width

        return current_y - y + font_size * line_height

    def draw_dot_grid(self, page: fitz.Page, start_y: float | None = None, end_y: float | None = None) -> None:
        if start_y is None:
            start_y = self.layout.content_top + 60
        if end_y is None:
            end_y = self.layout.content_bottom - 130

        shape = page.new_shape()

        y = start_y
        while y < end_y:
            x = self.layout.content_left
            while x < self.layout.content_right:
                rect = fitz.Rect(x, y, x + self.layout.dot_size, y + self.layout.dot_size)
                shape.draw_rect(rect)
                x += self.layout.dot_spacing
            y += self.layout.dot_spacing

        shape.finish(color=self.theme.black, fill=self.theme.black)
        shape.commit()

    def draw_lightning(self, page: fitz.Page, x: float, y: float, scale: float = 1.8, color=None) -> None:
        if color is None:
            color = self.theme.black
        points = [
            (8, 0), (15, 0), (9, 10), (16, 10),
            (0, 26), (5, 13), (0, 13), (8, 0)
        ]
        scaled_points = [fitz.Point(x + p[0] * scale, y + p[1] * scale) for p in points]
        page.draw_polyline(scaled_points, color=color, fill=color, closePath=True)

    def draw_lightning_white(self, page: fitz.Page, x: float, y: float, scale: float = 1.8) -> None:
        points = [
            (8, 0), (15, 0), (9, 10), (16, 10),
            (0, 26), (5, 13), (0, 13), (8, 0)
        ]
        scaled_points = [(x + px * scale, y + py * scale) for px, py in points]
        shape = page.new_shape()
        shape.draw_polyline([fitz.Point(px, py) for px, py in scaled_points])
        shape.finish(fill=self.theme.white, closePath=True)
        shape.commit()

    def draw_star(self, page: fitz.Page, x: float, y: float, size: float = 12, color=None) -> None:
        """Draw a five-pointed star (priority signifier)."""
        if color is None:
            color = self.theme.black
        import math
        points = []
        for i in range(5):
            outer_angle = math.radians(-90 + i * 72)
            points.append((
                x + size * math.cos(outer_angle),
                y + size * math.sin(outer_angle)
            ))
            inner_angle = math.radians(-90 + i * 72 + 36)
            points.append((
                x + size * 0.38 * math.cos(inner_angle),
                y + size * 0.38 * math.sin(inner_angle)
            ))
        fitz_points = [fitz.Point(px, py) for px, py in points]
        page.draw_polyline(fitz_points, color=color, fill=color, closePath=True)

    def draw_lightbulb(self, page: fitz.Page, x: float, y: float, size: float = 12, color=None) -> None:
        """Draw a simple hand-drawn style lightbulb icon - clearer design."""
        if color is None:
            color = self.theme.black
        stroke = 2.0
        # Main bulb - larger and more centered
        r = size * 0.5
        bulb_center_y = y - r * 0.3
        page.draw_circle(fitz.Point(x, bulb_center_y), r, color=color, width=stroke)
        # Neck/base - narrower and shorter
        neck_w = r * 0.5
        neck_top = bulb_center_y + r * 0.9
        neck_bot = bulb_center_y + r * 1.3
        page.draw_line(fitz.Point(x - neck_w, neck_top), fitz.Point(x - neck_w * 0.7, neck_bot), color=color, width=stroke)
        page.draw_line(fitz.Point(x + neck_w, neck_top), fitz.Point(x + neck_w * 0.7, neck_bot), color=color, width=stroke)
        page.draw_line(fitz.Point(x - neck_w * 0.7, neck_bot), fitz.Point(x + neck_w * 0.7, neck_bot), color=color, width=stroke)
        # Filament lines inside bulb for clarity
        filament_y = bulb_center_y + r * 0.1
        filament_w = r * 0.35
        page.draw_line(fitz.Point(x - filament_w, filament_y), fitz.Point(x, filament_y - r * 0.3), color=color, width=stroke * 0.7)
        page.draw_line(fitz.Point(x, filament_y - r * 0.3), fitz.Point(x + filament_w, filament_y), color=color, width=stroke * 0.7)

    def draw_eye(self, page: fitz.Page, x: float, y: float, size: float = 12, color=None) -> None:
        """Draw a simple hand-drawn style eye icon."""
        if color is None:
            color = self.theme.black
        stroke = 1.8
        w = size * 0.9
        h = size * 0.45
        page.draw_line(fitz.Point(x - w, y), fitz.Point(x - w * 0.3, y - h), color=color, width=stroke)
        page.draw_line(fitz.Point(x - w * 0.3, y - h), fitz.Point(x + w * 0.3, y - h), color=color, width=stroke)
        page.draw_line(fitz.Point(x + w * 0.3, y - h), fitz.Point(x + w, y), color=color, width=stroke)
        page.draw_line(fitz.Point(x - w, y), fitz.Point(x - w * 0.3, y + h), color=color, width=stroke)
        page.draw_line(fitz.Point(x - w * 0.3, y + h), fitz.Point(x + w * 0.3, y + h), color=color, width=stroke)
        page.draw_line(fitz.Point(x + w * 0.3, y + h), fitz.Point(x + w, y), color=color, width=stroke)
        pupil_r = size * 0.2
        page.draw_circle(fitz.Point(x, y), pupil_r, color=color, fill=color)

    def draw_arrow_right(self, page: fitz.Page, x: float, y: float, size: float, color=None) -> None:
        if color is None:
            color = self.theme.black
        shaft_length = size * 1.2
        head_size = size * 0.6
        stroke_width = size * 0.12

        tip_x = x + shaft_length
        tip_y = y

        page.draw_line(
            fitz.Point(x, y),
            fitz.Point(tip_x - head_size * 0.3, y),
            color=color, width=stroke_width,
        )
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x - head_size, tip_y - head_size * 0.7),
            color=color, width=stroke_width,
        )
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x - head_size, tip_y + head_size * 0.7),
            color=color, width=stroke_width,
        )

    def draw_arrow_left(self, page: fitz.Page, x: float, y: float, size: float, color=None) -> None:
        if color is None:
            color = self.theme.black
        shaft_length = size * 1.2
        head_size = size * 0.6
        stroke_width = size * 0.12

        tip_x = x
        tip_y = y

        page.draw_line(
            fitz.Point(x + shaft_length, y),
            fitz.Point(tip_x + head_size * 0.3, y),
            color=color, width=stroke_width,
        )
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x + head_size, tip_y - head_size * 0.7),
            color=color, width=stroke_width,
        )
        page.draw_line(
            fitz.Point(tip_x, tip_y),
            fitz.Point(tip_x + head_size, tip_y + head_size * 0.7),
            color=color, width=stroke_width,
        )

    def draw_footer_section(self, page: fitz.Page, footer_text: str) -> None:
        """Draw a compact footer section with gray divider line and lightning icon."""
        # Compact layout - position from actual page bottom, not content_bottom
        # Footer needs ~45px: divider line + 8px gap + text/icon (~36px)
        line_y = self.layout.target_height - 55
        text_y = line_y + 8

        # Gray divider line
        page.draw_line(
            fitz.Point(self.layout.content_left, line_y),
            fitz.Point(self.layout.content_right, line_y),
            color=self.theme.gray,
            width=0.5,
        )

        # Smaller lightning icon
        self.draw_lightning(page, self.layout.content_left, text_y + 2, scale=1.4)

        # Footer text in gray - strip rich text markers for simple rendering
        plain_text = footer_text.replace("|", "")
        self.add_text(
            page,
            plain_text,
            self.layout.content_left + 30,
            text_y,
            font_size=self.typography.sizes["footer"] - 2,
            color=self.theme.gray,
        )

    def add_nav_link(
        self,
        page_idx: int,
        text: str,
        dest_page_idx: int,
        x: float,
        y: float,
        font_size: float | None = None,
        with_arrow: bool = True,
    ) -> None:
        if font_size is None:
            font_size = self.typography.sizes["nav"]

        page = self.doc[page_idx]
        text_x = x

        if with_arrow:
            arrow_size = font_size * 0.5
            arrow_y = y + font_size * 0.65
            self.draw_arrow_left(page, x, arrow_y, arrow_size)
            text_x = x + arrow_size * 1.5 + 8

        self.add_text(page, text, text_x, y, font_size)

        text_width = self.get_text_width(text, font_size)
        link_rect = (x - 5, y - 2, text_x + text_width + 10, y + font_size + 6)
        self.links.add(page_idx, link_rect, dest_page_idx)

    def add_bottom_nav(self, page_idx: int, links: list[tuple[str, int]]) -> None:
        y = self.layout.target_height - 50
        x = self.layout.content_right - 10

        for text, dest_page_idx in reversed(links):
            text_width = self.get_text_width(text, self.typography.sizes["nav"])
            x = x - text_width - 30
            self.add_nav_link(page_idx, text, dest_page_idx, x, y, with_arrow=False)
