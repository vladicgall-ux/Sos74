"""One-off generator for the motivational card images under assets/motivation/.

Run manually with `python generate_motivation_assets.py` whenever MOTIVATIONS
in motivation.py changes and the images need regenerating. Not used at
bot runtime.
"""

from PIL import Image, ImageDraw, ImageFont

from motivation_data import MOTIVATIONS

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

WHITE = (255, 255, 255)
CREAM = (255, 236, 214)
DARK = (30, 20, 18)

# A rotating set of on-brand gradient pairs (warm SOS74 orange/red family
# plus a couple of cooler accents for variety between cards).
PALETTES = [
    ((255, 106, 0), (211, 30, 30)),
    ((255, 145, 0), (168, 20, 90)),
    ((255, 94, 58), (120, 20, 60)),
    ((255, 170, 40), (200, 50, 30)),
    ((255, 120, 20), (90, 20, 90)),
    ((250, 140, 20), (160, 10, 40)),
    ((255, 100, 60), (60, 30, 110)),
    ((255, 160, 0), (190, 40, 20)),
    ((255, 110, 40), (130, 10, 70)),
    ((255, 150, 30), (100, 20, 100)),
]


def vertical_gradient(size, top, bottom):
    w, h = size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        grad.putpixel((0, y), (r, g, b))
    return grad.resize(size)


def draw_padlock(draw, cx, cy, scale, color):
    body_w, body_h = 92 * scale, 74 * scale
    body_top = cy - body_h * 0.15
    body = [cx - body_w / 2, body_top, cx + body_w / 2, body_top + body_h]
    draw.rounded_rectangle(body, radius=14 * scale, fill=color)

    shackle_r, shackle_w = 42 * scale, 14 * scale
    box = [cx - shackle_r, body_top - shackle_r * 1.55, cx + shackle_r, body_top + shackle_r * 0.55]
    draw.arc(box, start=180, end=360, fill=color, width=int(shackle_w))


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_card(path, quote, top, bottom, size=1080):
    img = vertical_gradient((size, size), top, bottom)
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.09)
    max_width = size - margin * 2

    font_size = 68
    font = ImageFont.truetype(BOLD, font_size)
    lines = wrap_text(draw, quote, font, max_width)
    while (len(lines) > 5 or font_size > 40) and font_size > 40:
        font_size -= 4
        font = ImageFont.truetype(BOLD, font_size)
        lines = wrap_text(draw, quote, font, max_width)
        if len(lines) <= 5:
            break

    line_height = int(font_size * 1.35)
    block_height = line_height * len(lines)
    start_y = size * 0.42 - block_height / 2

    draw.text((size / 2, size * 0.16), "“", font=ImageFont.truetype(BOLD, 140), fill=(255, 255, 255, 90), anchor="mm")

    for i, line in enumerate(lines):
        draw.text((size / 2, start_y + i * line_height), line, font=font, fill=WHITE, anchor="ma")

    draw_padlock(draw, size / 2, size * 0.84, scale=size / 1400, color=(255, 255, 255, 220))
    font_brand = ImageFont.truetype(BOLD, int(size * 0.045))
    draw.text((size / 2, size * 0.92), "SOS74", font=font_brand, fill=CREAM, anchor="mm")

    img.save(path, "PNG")


if __name__ == "__main__":
    import os

    out_dir = os.path.join(os.path.dirname(__file__), "assets", "motivation")
    os.makedirs(out_dir, exist_ok=True)

    for i, item in enumerate(MOTIVATIONS):
        top, bottom = PALETTES[i % len(PALETTES)]
        path = os.path.join(out_dir, item["photo"])
        make_card(path, item["text"], top, bottom)
        print("saved", path)
