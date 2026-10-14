"""Generate the brand's simple code-native Windows icon."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).parent
image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((20, 20, 492, 492), radius=112, fill="#203c35")
draw.rounded_rectangle((38, 38, 474, 474), radius=98, outline="#537466", width=3)
# A distinctive geometric Z; no reliance on installed fonts.
draw.polygon([(139, 150), (372, 150), (372, 195), (217, 335), (372, 335), (372, 379), (139, 379), (139, 335), (294, 194), (139, 194)], fill="#e3cd9c")
draw.ellipse((359, 105, 397, 143), fill="#80ad95")
image.save(root / "assets" / "icon.png")
image.save(root / "assets" / "icon.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
