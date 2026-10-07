"""Build tray icon image with optional percent label."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


def build_icon(label: str | None, warn: bool = False) -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    bg = (180, 60, 60, 255) if warn else (45, 120, 200, 255)
    draw.ellipse((4, 4, size - 4, size - 4), fill=bg)

    text = label if label is not None else "—"
    if len(text) > 4:
        text = text[:4]

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) / 2
    y = (size - th) / 2 - 2
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    return image
