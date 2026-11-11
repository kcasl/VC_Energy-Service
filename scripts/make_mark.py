"""Crop the product mark and drop the navy field so it sits on the sidebar."""

from pathlib import Path

from PIL import Image

src = Path(r"C:\Users\sadd2\.cursor\projects\c-Project-VC03\assets\vitality-logo.jpg")
im = Image.open(src).convert("RGBA")
pix = im.load()
width, height = im.size
bg = pix[2, 2][:3]


def close(color: tuple[int, int, int]) -> bool:
    return sum(abs(color[i] - bg[i]) for i in range(3)) < 48


for y in range(height):
    for x in range(width):
        r, g, b, a = pix[x, y]
        if close((r, g, b)):
            pix[x, y] = (r, g, b, 0)

bbox = im.getbbox()
if not bbox:
    raise SystemExit("mark is empty")
pad = 12
left = max(0, bbox[0] - pad)
top = max(0, bbox[1] - pad)
right = min(width, bbox[2] + pad)
bottom = min(height, bbox[3] + pad)
cropped = im.crop((left, top, right, bottom))
out = Path(r"C:\Project\VC03\public\brand")
out.mkdir(parents=True, exist_ok=True)
cropped.save(out / "mark.png")
print("saved", cropped.size)
