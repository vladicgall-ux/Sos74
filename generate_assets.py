from PIL import Image, ImageDraw, ImageFont, ImageFilter

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------- Colors ----------
ORANGE_1 = (255, 106, 0)
ORANGE_2 = (211, 30, 30)
DARK = (30, 20, 18)
WHITE = (255, 255, 255)
CREAM = (255, 236, 214)


def vertical_gradient(size, top, bottom):
    w, h = size
    base = Image.new("RGB", size, top)
    top_arr = Image.new("RGB", (1, h), top)
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        grad.putpixel((0, y), (r, g, b))
    return grad.resize(size)


def draw_padlock(draw, cx, cy, scale, color, shackle_color=None):
    shackle_color = shackle_color or color
    body_w = 92 * scale
    body_h = 74 * scale
    body_top = cy - body_h * 0.15
    body = [cx - body_w / 2, body_top, cx + body_w / 2, body_top + body_h]
    draw.rounded_rectangle(body, radius=14 * scale, fill=color)

    # shackle (arc)
    shackle_r = 42 * scale
    shackle_w = 14 * scale
    box = [cx - shackle_r, body_top - shackle_r * 1.55, cx + shackle_r, body_top + shackle_r * 0.55]
    draw.arc(box, start=180, end=360, fill=shackle_color, width=int(shackle_w))

    # keyhole
    kh_r = 9 * scale
    kh_cx, kh_cy = cx, body_top + body_h * 0.38
    draw.ellipse([kh_cx - kh_r, kh_cy - kh_r, kh_cx + kh_r, kh_cy + kh_r], fill=DARK)
    draw.polygon(
        [
            (kh_cx - kh_r * 0.55, kh_cy + kh_r * 0.3),
            (kh_cx + kh_r * 0.55, kh_cy + kh_r * 0.3),
            (kh_cx + kh_r * 0.9, kh_cy + kh_r * 2.4),
            (kh_cx - kh_r * 0.9, kh_cy + kh_r * 2.4),
        ],
        fill=DARK,
    )


def make_icon(path, size=512):
    img = vertical_gradient((size, size), ORANGE_1, ORANGE_2)
    img = img.filter(ImageFilter.GaussianBlur(0))
    draw = ImageDraw.Draw(img)

    # subtle inner glow circle
    pad = int(size * 0.04)
    draw.ellipse([pad, pad, size - pad, size - pad], outline=(255, 255, 255, 60), width=6)

    draw_padlock(draw, size / 2, size * 0.38, scale=size / 260, color=WHITE)

    font_big = ImageFont.truetype(BOLD, int(size * 0.155))
    text = "SOS74"
    bbox = draw.textbbox((0, 0), text, font=font_big)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((size / 2 - tw / 2, size * 0.775 - th / 2 - bbox[1]), text, font=font_big, fill=WHITE)

    img.save(path, "PNG")


def make_banner(path, w=1280, h=640):
    img = vertical_gradient((w, h), ORANGE_1, ORANGE_2)
    draw = ImageDraw.Draw(img)

    # decorative diagonal stripe
    stripe = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(stripe)
    sdraw.polygon([(w * 0.62, 0), (w, 0), (w * 0.78, h), (w * 0.46, h)], fill=(255, 255, 255, 22))
    img.paste(Image.alpha_composite(img.convert("RGBA"), stripe).convert("RGB"), (0, 0))
    draw = ImageDraw.Draw(img)

    draw_padlock(draw, w * 0.15, h * 0.5, scale=h / 300, color=WHITE)

    text_x = w * 0.34
    font_title = ImageFont.truetype(BOLD, int(h * 0.12))
    font_sub = ImageFont.truetype(BOLD, int(h * 0.042))

    title = "SOS74"
    tb = draw.textbbox((0, 0), title, font=font_title)
    draw.text((text_x, h * 0.28 - (tb[3] - tb[1]) / 2), title, font=font_title, fill=WHITE)

    subtitle = "Экстренное вскрытие замков"
    draw.text((text_x, h * 0.28 + int(h * 0.12) * 0.65), subtitle, font=font_sub, fill=CREAM)

    subtitle1b = "в Челябинске"
    draw.text((text_x, h * 0.28 + int(h * 0.12) * 0.65 + int(h * 0.065)), subtitle1b, font=font_sub, fill=CREAM)

    subtitle2 = "sos74.ru  •  Свердловский пр-т, 39"
    draw.text(
        (text_x, h * 0.28 + int(h * 0.12) * 0.65 + int(h * 0.065) * 2 + int(h * 0.02)),
        subtitle2, font=font_sub, fill=CREAM,
    )

    img.save(path, "PNG")


if __name__ == "__main__":
    make_icon("/home/claude/lockbot/assets/icon_sos74.png")
    make_banner("/home/claude/lockbot/assets/banner_sos74.png")
    print("done")
