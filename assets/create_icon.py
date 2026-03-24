"""
Generate assets/aria.ico — run once locally or in CI before PyInstaller.
Produces a green circle with "A" at multiple resolutions for Windows.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def make_frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = max(2, size // 8)
    d.ellipse([margin, margin, size - margin, size - margin], fill=(0, 180, 120, 255))
    # Draw "A" text centred
    font_size = max(8, size // 2)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), "A", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2
    d.text((tx, ty), "A", fill="white", font=font)
    return img

sizes = [16, 32, 48, 64, 128, 256]
frames = [make_frame(s) for s in sizes]

out = Path(__file__).parent / "aria.ico"
frames[0].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:])
print(f"✅  Created {out}")
