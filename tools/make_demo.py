"""Animated tour made entirely from real application screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent.parent
media = root / "docs" / "media"
fontpath = Path("C:/Windows/Fonts/segoeui.ttf")
font = ImageFont.truetype(str(fontpath), 22) if fontpath.exists() else ImageFont.load_default(size=22)
small = ImageFont.truetype(str(fontpath), 13) if fontpath.exists() else ImageFont.load_default(size=13)
entries = [("today.png", "A clear plan for today"), ("board.png", "Projects, checklists & recurring tasks"),
           ("notes.png", "A place for searchable ideas"), ("focus.png", "One thing. Your full attention."),
           ("review.png", "Activity based on recorded work"), ("backup.png", "Your workspace. Your control.")]
frames = []
for name, title in entries:
    screenshot = Image.open(media / name).convert("RGB")
    screenshot.thumbnail((1060, 850))
    canvas = Image.new("RGB", (1100, 940), "#172c25")
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 15), "ZODERISE FOCUS", font=font, fill="#e3cd9c")
    draw.text((24, 49), title, font=small, fill="#c5d2c6")
    canvas.paste(screenshot, ((1100-screenshot.width)//2, 80))
    draw.text((24, 911), "Real app walkthrough · Sample workspace · Local-first productivity", font=small, fill="#c5d2c6")
    frames.append(canvas.quantize(colors=192))
frames[0].save(media / "demo.gif", save_all=True, append_images=frames[1:], duration=[2400]*len(frames), loop=0, optimize=True)
print(media / "demo.gif")
