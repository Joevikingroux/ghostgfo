"""
Generate ghostcfo.ico — all required Windows icon sizes.

Run once on the build machine before PyInstaller:
    pip install Pillow
    python assets/generate_icon.py

Produces:  assets/ghostcfo.ico
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "ghostcfo.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]

# Brand colours
BG       = (0, 0, 0, 0)          # transparent background
TEAL     = (45, 212, 191)        # #2DD4BF
CYAN     = (6, 182, 212)         # #06B6D4
WHITE    = (255, 255, 255, 255)
DARK_BG  = (12, 12, 18, 255)     # near-black fill


def _lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG)
    d = ImageDraw.Draw(img)

    pad = max(1, size // 16)
    r = size // 2 - pad  # radius of outer circle

    cx, cy = size // 2, size // 2

    # --- Gradient circle background (teal -> cyan, top-left to bottom-right) ---
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r * r:
                t = (x + y) / (size * 2)
                col = _lerp_color(TEAL + (255,), CYAN + (255,), t)
                img.putpixel((x, y), col)

    # --- Ghost shape (white, centred) ---
    # Ghost = rounded rectangle head + scalloped bottom
    gw = int(size * 0.52)
    gh = int(size * 0.60)
    gx = cx - gw // 2
    gy = cy - gh // 2 - int(size * 0.04)

    ghost_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost_img)

    # Head arc (top half rounded)
    head_r = gw // 2
    head_cx = cx
    head_cy = gy + head_r
    gd.ellipse(
        [head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r],
        fill=WHITE,
    )
    # Body rectangle
    body_top = head_cy
    body_bot = gy + gh - int(size * 0.10)
    gd.rectangle([gx, body_top, gx + gw, body_bot], fill=WHITE)

    # Scalloped bottom — 3 bumps
    scallop_y = body_bot
    bump_w = gw // 3
    bump_r = bump_w // 2
    for i in range(3):
        bx = gx + i * bump_w + bump_r
        gd.ellipse(
            [bx - bump_r, scallop_y - bump_r, bx + bump_r, scallop_y + bump_r],
            fill=WHITE,
        )

    # Eyes — two dark circles
    eye_r = max(1, int(size * 0.055))
    eye_y = head_cy - int(size * 0.02)
    eye_offset = int(gw * 0.22)
    for ex in [cx - eye_offset, cx + eye_offset]:
        gd.ellipse(
            [ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r],
            fill=DARK_BG,
        )

    # Merge ghost onto gradient circle
    img = Image.alpha_composite(img, ghost_img)

    # --- Thin white border around circle ---
    border_d = ImageDraw.Draw(img)
    bw = max(1, size // 48)
    border_d.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=(255, 255, 255, 160),
        width=bw,
    )

    return img


def main() -> None:
    frames = []
    for s in SIZES:
        frame = draw_icon(s)
        frames.append(frame)
        print(f"  {s}x{s} OK")

    # Save as multi-resolution ICO
    frames[0].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"\nSaved -> {OUT}")

    # Also save a 256px PNG for the Inno Setup installer banner
    png_out = Path(__file__).parent / "ghostcfo_256.png"
    frames[-1].save(png_out, format="PNG")
    print(f"Saved -> {png_out}")


if __name__ == "__main__":
    main()
