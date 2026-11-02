# -*- coding: utf-8 -*-
"""小鲸鱼的图片编辑套件：裁剪、滤镜、拼图、局部模糊、双图对比。"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

FONT_DIR = Path(r"C:\Windows\Fonts")
W, H = 1080, 1080


def _font(size: int, bold: bool = False):
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    try:
        return ImageFont.truetype(str(FONT_DIR / name), int(size))
    except Exception:
        return ImageFont.load_default()


def _open(data: bytes) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")


def _out(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _cover(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / im.width, size[1] / im.height)
    nw, nh = max(size[0], int(im.width * scale + 1)), max(size[1], int(im.height * scale + 1))
    im = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - size[0]) // 2, (nh - size[1]) // 2
    return im.crop((left, top, left + size[0], top + size[1]))


def _rounded(im: Image.Image, radius: int = 24) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1],
                                           radius=radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def crop(data: bytes, aspect: str = "1:1") -> bytes:
    im = _open(data)
    ratios = {"1:1": 1.0, "16:9": 16 / 9, "9:16": 9 / 16,
              "4:3": 4 / 3, "3:4": 3 / 4, "3:2": 3 / 2, "2:3": 2 / 3}
    ratio = ratios.get(str(aspect or "").strip(), 1.0)
    w, h = im.size
    if w / h > ratio:
        nw = int(h * ratio)
        box = ((w - nw) // 2, 0, (w + nw) // 2, h)
    else:
        nh = int(w / ratio)
        box = (0, (h - nh) // 2, w, (h + nh) // 2)
    return _out(im.crop(box))


def filter_image(data: bytes, name: str = "warm") -> bytes:
    im = _open(data)
    key = str(name or "").strip().lower()
    if key in ("gray", "黑白", "灰度"):
        im = ImageOps.grayscale(im).convert("RGB")
    elif key in ("warm", "暖色", "暖"):
        im = ImageEnhance.Color(im).enhance(1.12)
        overlay = Image.new("RGBA", im.size, (255, 150, 60, 28))
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    elif key in ("cool", "冷色", "冷"):
        overlay = Image.new("RGBA", im.size, (60, 140, 255, 30))
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    elif key in ("blur", "模糊"):
        im = im.filter(ImageFilter.GaussianBlur(7))
    elif key in ("sharpen", "锐化"):
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))
    elif key in ("vintage", "复古"):
        im = ImageOps.autocontrast(im)
        im = ImageEnhance.Color(im).enhance(0.72)
        overlay = Image.new("RGBA", im.size, (180, 120, 60, 34))
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    elif key in ("contrast", "高对比"):
        im = ImageEnhance.Contrast(im).enhance(1.35)
    else:
        im = ImageEnhance.Color(im).enhance(1.08)
    return _out(im)


def blur_region(data: bytes, position: str = "center", strength: int = 14) -> bytes:
    im = _open(data).convert("RGBA")
    w, h = im.size
    pos = str(position or "center").lower()
    if "左" in pos or pos == "left":
        box = (0, int(h * 0.15), int(w * 0.45), int(h * 0.85))
    elif "右" in pos or pos == "right":
        box = (int(w * 0.55), int(h * 0.15), w, int(h * 0.85))
    elif "上" in pos or pos == "top":
        box = (int(w * 0.15), 0, int(w * 0.85), int(h * 0.45))
    elif "下" in pos or pos == "bottom":
        box = (int(w * 0.15), int(h * 0.55), int(w * 0.85), h)
    else:
        box = (int(w * 0.22), int(h * 0.22), int(w * 0.78), int(h * 0.78))
    region = im.crop(box).filter(ImageFilter.GaussianBlur(max(4, int(strength))))
    mask = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, mask.width - 1, mask.height - 1], radius=28, fill=255)
    im.paste(region, box[:2], mask)
    return _out(im)


def collage(images: list[bytes], labels: list[str] | None = None) -> bytes:
    items = [_open(x) for x in images[:4]]
    if not items:
        raise ValueError("no images")
    cols = 2 if len(items) > 1 else 1
    rows = (len(items) + cols - 1) // cols
    pad, gap, label_h = 28, 18, 44
    cell_w = (W - pad * 2 - gap * (cols - 1)) // cols
    cell_h = (H - pad * 2 - gap * (rows - 1) - label_h * rows) // rows
    canvas = Image.new("RGB", (W, H), (247, 243, 234))
    d = ImageDraw.Draw(canvas)
    for i, im in enumerate(items):
        col, row = i % cols, i // cols
        x = pad + col * (cell_w + gap)
        y = pad + row * (cell_h + gap + label_h)
        panel = _rounded(_cover(im, (cell_w, cell_h)), 22)
        canvas.paste(panel, (x, y), panel)
        label = (labels[i] if labels and i < len(labels) else chr(65 + i))
        d.text((x + cell_w // 2, y + cell_h + 6), str(label)[:20],
               font=_font(24, True), fill=(40, 52, 78), anchor="ma")
    return _out(canvas)


def compare_images(a: bytes, b: bytes, labels=("A", "B"), title: str = "对比") -> bytes:
    canvas = Image.new("RGB", (W, 720), (18, 28, 54))
    d = ImageDraw.Draw(canvas)
    d.text((48, 30), str(title)[:24], font=_font(34, True), fill=(240, 244, 252))
    panel_w, panel_h = 480, 560
    for i, (data, label) in enumerate(((a, labels[0]), (b, labels[1]))):
        x = 48 + i * (panel_w + 24)
        y = 112
        im = _rounded(_cover(_open(data), (panel_w, panel_h)), 22)
        canvas.paste(im, (x, y), im)
        d.text((x + panel_w // 2, y + panel_h + 14), str(label)[:20],
               font=_font(24, True), fill=(150, 200, 255), anchor="ma")
    canvas.save(io.BytesIO(), "PNG")
    return _out(canvas)
