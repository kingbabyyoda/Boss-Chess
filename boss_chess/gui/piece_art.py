from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw, ImageTk

PIECE_ORDER = "PNBRQKpnbrqk"

PIECE_STYLES: dict[str, tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int, int, int]]] = {
    "Classic": ((248, 250, 252, 255), (15, 23, 42, 255), (15, 23, 42, 255)),
    "Slate": ((226, 232, 240, 255), (30, 41, 59, 255), (15, 23, 42, 255)),
    "Neon": ((34, 211, 238, 255), (124, 58, 237, 255), (248, 250, 252, 255)),
}

SHADOW = (0, 0, 0, 70)


def _style_palette(piece_set: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int, int, int]]:
    return PIECE_STYLES.get(piece_set, PIECE_STYLES["Classic"])


def _palette(symbol: str, piece_set: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int, int, int]]:
    white_fill, white_outline, accent = _style_palette(piece_set)
    black_fill, black_outline, _ = _style_palette(piece_set)
    return (white_fill, white_outline, accent) if symbol.isupper() else (black_fill, black_outline, accent)


def _stroke(size: int) -> int:
    return max(1, size // 18)


def _canvas(size: int) -> Image.Image:
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def _draw_pawn(draw: ImageDraw.ImageDraw, fill, outline, accent, size: int) -> None:
    s = _stroke(size)
    w = size
    draw.ellipse((w * 0.37, w * 0.10, w * 0.63, w * 0.36), fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.32, w * 0.28, w * 0.68, w * 0.66), radius=w * 0.12, fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.22, w * 0.72, w * 0.78, w * 0.86), radius=w * 0.05, fill=fill, outline=outline, width=s)
    draw.ellipse((w * 0.47, w * 0.16, w * 0.53, w * 0.22), fill=accent)


def _draw_rook(draw: ImageDraw.ImageDraw, fill, outline, accent, size: int) -> None:
    s = _stroke(size)
    w = size
    draw.rectangle((w * 0.31, w * 0.20, w * 0.69, w * 0.68), fill=fill, outline=outline, width=s)
    for x0 in (w * 0.28, w * 0.42, w * 0.56):
        draw.rectangle((x0, w * 0.10, x0 + w * 0.10, w * 0.22), fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.22, w * 0.72, w * 0.78, w * 0.86), radius=w * 0.05, fill=fill, outline=outline, width=s)
    draw.rectangle((w * 0.41, w * 0.34, w * 0.59, w * 0.40), fill=accent)


def _draw_bishop(draw: ImageDraw.ImageDraw, fill, outline, accent, size: int) -> None:
    s = _stroke(size)
    w = size
    draw.ellipse((w * 0.30, w * 0.12, w * 0.70, w * 0.56), fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.33, w * 0.46, w * 0.67, w * 0.76), radius=w * 0.09, fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.23, w * 0.78, w * 0.77, w * 0.86), radius=w * 0.05, fill=fill, outline=outline, width=s)
    draw.line((w * 0.50, w * 0.20, w * 0.42, w * 0.41), fill=outline, width=s + 1)
    draw.line((w * 0.42, w * 0.41, w * 0.58, w * 0.47), fill=outline, width=s + 1)
    draw.ellipse((w * 0.46, w * 0.24, w * 0.54, w * 0.30), fill=accent)


def _draw_knight(draw: ImageDraw.ImageDraw, fill, outline, accent, size: int) -> None:
    s = _stroke(size)
    w = size
    pts = [
        (w * 0.32, w * 0.80),
        (w * 0.37, w * 0.58),
        (w * 0.44, w * 0.44),
        (w * 0.39, w * 0.24),
        (w * 0.52, w * 0.12),
        (w * 0.69, w * 0.20),
        (w * 0.72, w * 0.43),
        (w * 0.60, w * 0.54),
        (w * 0.68, w * 0.67),
        (w * 0.67, w * 0.80),
    ]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.rounded_rectangle((w * 0.24, w * 0.80, w * 0.76, w * 0.86), radius=w * 0.05, fill=fill, outline=outline, width=s)
    draw.ellipse((w * 0.55, w * 0.28, w * 0.60, w * 0.33), fill=accent)


def _draw_queen(draw: ImageDraw.ImageDraw, fill, outline, accent, size: int) -> None:
    s = _stroke(size)
    w = size
    pts = [
        (w * 0.24, w * 0.28),
        (w * 0.32, w * 0.14),
        (w * 0.42, w * 0.28),
        (w * 0.50, w * 0.12),
        (w * 0.58, w * 0.28),
        (w * 0.68, w * 0.14),
        (w * 0.76, w * 0.28),
        (w * 0.69, w * 0.68),
        (w * 0.31, w * 0.68),
    ]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.ellipse((w * 0.28, w * 0.16, w * 0.36, w * 0.24), fill=fill, outline=outline, width=s)
    draw.ellipse((w * 0.46, w * 0.08, w * 0.54, w * 0.16), fill=fill, outline=outline, width=s)
    draw.ellipse((w * 0.64, w * 0.16, w * 0.72, w * 0.24), fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.23, w * 0.78, w * 0.77, w * 0.86), radius=w * 0.05, fill=fill, outline=outline, width=s)
    draw.ellipse((w * 0.48, w * 0.20, w * 0.52, w * 0.24), fill=accent)


def _draw_king(draw: ImageDraw.ImageDraw, fill, outline, accent, size: int) -> None:
    s = _stroke(size)
    w = size
    draw.rounded_rectangle((w * 0.33, w * 0.18, w * 0.67, w * 0.61), radius=w * 0.10, fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.28, w * 0.57, w * 0.72, w * 0.79), radius=w * 0.08, fill=fill, outline=outline, width=s)
    draw.rounded_rectangle((w * 0.22, w * 0.80, w * 0.78, w * 0.86), radius=w * 0.05, fill=fill, outline=outline, width=s)
    draw.rectangle((w * 0.47, w * 0.06, w * 0.53, w * 0.19), fill=fill, outline=outline, width=s)
    draw.rectangle((w * 0.42, w * 0.10, w * 0.58, w * 0.15), fill=fill, outline=outline, width=s)
    draw.ellipse((w * 0.48, w * 0.12, w * 0.52, w * 0.16), fill=accent)


_DRAWERS = {
    "P": _draw_pawn,
    "N": _draw_knight,
    "B": _draw_bishop,
    "R": _draw_rook,
    "Q": _draw_queen,
    "K": _draw_king,
}


@lru_cache(maxsize=96)
def _render_piece(symbol: str, size: int, piece_set: str) -> Image.Image:
    fill, outline, accent = _palette(symbol, piece_set)
    base = _canvas(size)
    shadow = _canvas(size)
    shadow_draw = ImageDraw.Draw(shadow)
    base_draw = ImageDraw.Draw(base)
    drawer = _DRAWERS[symbol.upper()]
    drawer(shadow_draw, SHADOW, SHADOW, SHADOW, size)
    drawer(base_draw, fill, outline, accent, size)
    return Image.alpha_composite(shadow, base)


def build_piece_images(master, size: int = 72, piece_set: str = "Classic") -> dict[str, ImageTk.PhotoImage]:
    return {symbol: ImageTk.PhotoImage(_render_piece(symbol, size, piece_set), master=master) for symbol in PIECE_ORDER}
