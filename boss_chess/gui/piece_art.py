from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageTk

PIECE_GLYPHS = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}

WHITE_FILL = "#f8fafc"
WHITE_OUTLINE = "#111827"
BLACK_FILL = "#0f172a"
BLACK_OUTLINE = "#f8fafc"
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


@lru_cache(maxsize=16)
def _font_path() -> str:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("No suitable system font found for Boss Chess piece art.")


@lru_cache(maxsize=32)
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(), size=size)


def _render_piece(symbol: str, size: int) -> Image.Image:
    glyph = PIECE_GLYPHS[symbol]
    is_white = symbol.isupper()
    fill = WHITE_FILL if is_white else BLACK_FILL
    outline = WHITE_OUTLINE if is_white else BLACK_OUTLINE

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = _load_font(int(size * 0.78))

    bbox = draw.textbbox((0, 0), glyph, font=font, stroke_width=max(1, size // 20))
    glyph_width = bbox[2] - bbox[0]
    glyph_height = bbox[3] - bbox[1]
    x = (size - glyph_width) / 2 - bbox[0]
    y = (size - glyph_height) / 2 - bbox[1] - size * 0.03

    # Soft shadow for depth.
    shadow_pos = (x + size * 0.03, y + size * 0.03)
    draw.text(
        shadow_pos,
        glyph,
        font=font,
        fill=(0, 0, 0, 72),
        stroke_width=max(1, size // 20),
        stroke_fill=(0, 0, 0, 48),
    )

    draw.text(
        (x, y),
        glyph,
        font=font,
        fill=fill,
        stroke_width=max(1, size // 20),
        stroke_fill=outline,
    )
    return canvas


def build_piece_images(master, size: int = 72) -> dict[str, ImageTk.PhotoImage]:
    images: dict[str, ImageTk.PhotoImage] = {}
    for symbol in PIECE_GLYPHS:
        pil_image = _render_piece(symbol, size)
        images[symbol] = ImageTk.PhotoImage(pil_image, master=master)
    return images
