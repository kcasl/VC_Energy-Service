from pathlib import Path
from PIL import Image

src = Path(
    r"C:\Users\sadd2\.cursor\projects\c-Project-VC03\assets"
    r"\c__Users_sadd2_AppData_Roaming_Cursor_User_workspaceStorage_66e0df80ac4fe15a86c8e45a78905639_images_top-logo-eb3dd056-25a4-4c22-823d-6caeb3555aba.png"
)
im = Image.open(src).convert("RGBA")
pix = im.load()
width, height = im.size
for y in range(height):
    for x in range(width):
        r, g, b, a = pix[x, y]
        if r + g + b < 36:
            pix[x, y] = (r, g, b, 0)
out = Path(r"C:\Project\VC03\public\brand")
out.mkdir(parents=True, exist_ok=True)
im.save(out / "kentech.png")
print("saved", width, height)
