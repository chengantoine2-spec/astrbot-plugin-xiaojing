# -*- coding: utf-8 -*-
"""小鲸的图片标注与简单绘图。

不依赖绘画模型：
- 简笔画：猫、鲸鱼、人、心、星、花、太阳、云、房子、树、蘑菇、笑脸
- 像素画：内置 16x16 模板，也接受自定义 grid
- 图片标注：圆圈、箭头、涂鸦、文字、半透明高亮
"""

from __future__ import annotations

import io
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance, ImageChops

SIZE = 640
BG = (250, 247, 240)
INK = (38, 42, 50)
FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"

COLORS = {
    "red": (230, 60, 60), "红": (230, 60, 60), "红色": (230, 60, 60),
    "yellow": (248, 196, 40), "黄": (248, 196, 40), "黄色": (248, 196, 40),
    "blue": (70, 140, 230), "蓝": (70, 140, 230), "蓝色": (70, 140, 230),
    "green": (80, 190, 120), "绿": (80, 190, 120), "绿色": (80, 190, 120),
    "pink": (240, 120, 170), "粉": (240, 120, 170), "粉色": (240, 120, 170),
    "orange": (250, 150, 60), "橙": (250, 150, 60), "橙色": (250, 150, 60),
    "white": (255, 255, 255), "白": (255, 255, 255), "白色": (255, 255, 255),
    "black": (30, 30, 30), "黑": (30, 30, 30), "黑色": (30, 30, 30),
}


def _font(size: int, bold: bool = False):
    for name in (("msyhbd.ttc" if bold else "msyh.ttc"), "msyh.ttc", "simhei.ttf"):
        try:
            return ImageFont.truetype(str(FONT_DIR / name), int(size))
        except Exception:
            continue
    return ImageFont.load_default()


def _out(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


def to_jpeg(data: bytes, quality: int = 92) -> bytes:
    im = Image.open(io.BytesIO(data)).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def _p(x: float, y: float, w: int = SIZE, h: int = SIZE) -> tuple[int, int]:
    return int(x * w), int(y * h)


def _color(value, default=(230, 60, 60)):
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return tuple(int(v) for v in value[:3])
        except Exception:
            return default
    return COLORS.get(str(value or "").strip().lower(), default)


def _caption(d: ImageDraw.ImageDraw, text: str, color=INK) -> None:
    text = str(text or "").strip()
    if not text:
        return
    font = _font(30, bold=True)
    d.text((SIZE // 2, SIZE - 42), text[:24], font=font, fill=color, anchor="mm")


def _frame(d: ImageDraw.ImageDraw) -> None:
    d.rounded_rectangle([14, 14, SIZE - 14, SIZE - 14], radius=28,
                        outline=(225, 220, 208), width=3)


# ---------------- 简笔画 ----------------

def _cat(d: ImageDraw.ImageDraw, color=INK) -> None:
    w = 6
    d.ellipse([_p(0.30, 0.22), _p(0.70, 0.58)], outline=color, width=w)
    d.polygon([_p(0.30, 0.31), _p(0.23, 0.11), _p(0.41, 0.22)], outline=color, fill=BG)
    d.polygon([_p(0.70, 0.31), _p(0.77, 0.11), _p(0.59, 0.22)], outline=color, fill=BG)
    d.ellipse([_p(0.39, 0.35), _p(0.44, 0.42)], fill=color)
    d.ellipse([_p(0.56, 0.35), _p(0.61, 0.42)], fill=color)
    d.polygon([_p(0.47, 0.45), _p(0.53, 0.45), _p(0.50, 0.49)], fill=(220, 120, 120))
    d.arc([_p(0.45, 0.47), _p(0.50, 0.54)], 0, 180, fill=color, width=4)
    d.arc([_p(0.50, 0.47), _p(0.55, 0.54)], 0, 180, fill=color, width=4)
    for y in (0.45, 0.49, 0.53):
        d.line([_p(0.39, y), _p(0.25, y + 0.01)], fill=color, width=4)
        d.line([_p(0.61, y), _p(0.75, y + 0.01)], fill=color, width=4)
    d.arc([_p(0.35, 0.52), _p(0.65, 0.82)], 0, 180, fill=color, width=w)
    d.line([_p(0.35, 0.67), _p(0.35, 0.83)], fill=color, width=w)
    d.line([_p(0.65, 0.67), _p(0.65, 0.83)], fill=color, width=w)
    d.arc([_p(0.62, 0.56), _p(0.86, 0.82)], 270, 90, fill=color, width=w)
    d.ellipse([_p(0.38, 0.78), _p(0.46, 0.84)], outline=color, width=4)
    d.ellipse([_p(0.54, 0.78), _p(0.62, 0.84)], outline=color, width=4)


def _whale(d: ImageDraw.ImageDraw) -> None:
    line = (70, 130, 210)
    fill = (190, 225, 250)
    w = 6
    d.ellipse([_p(0.14, 0.34), _p(0.74, 0.66)], fill=fill, outline=line, width=w)
    d.polygon([_p(0.72, 0.46), _p(0.90, 0.33), _p(0.87, 0.51),
               _p(0.90, 0.67), _p(0.72, 0.56)], fill=fill, outline=line)
    d.ellipse([_p(0.25, 0.43), _p(0.29, 0.48)], fill=line)
    d.arc([_p(0.26, 0.47), _p(0.40, 0.57)], 10, 110, fill=line, width=4)
    d.arc([_p(0.40, 0.55), _p(0.55, 0.72)], 200, 340, fill=line, width=6)
    d.line([_p(0.42, 0.34), _p(0.39, 0.23)], fill=line, width=5)
    d.line([_p(0.39, 0.23), _p(0.32, 0.17)], fill=line, width=5)
    d.line([_p(0.39, 0.23), _p(0.46, 0.17)], fill=line, width=5)
    for cx, cy, r in ((0.20, 0.26, 0.018), (0.26, 0.20, 0.012), (0.16, 0.18, 0.010)):
        d.ellipse([_p(cx - r, cy - r), _p(cx + r, cy + r)], outline=line, width=3)


def _person(d: ImageDraw.ImageDraw, pose: str = "stand", color=INK) -> None:
    w = 6
    d.ellipse([_p(0.42, 0.12), _p(0.58, 0.28)], outline=color, width=w)
    d.line([_p(0.50, 0.28), _p(0.50, 0.62)], fill=color, width=w)
    if "wave" in str(pose).lower() or "挥" in str(pose):
        d.line([_p(0.50, 0.38), _p(0.62, 0.29)], fill=color, width=w)
        d.line([_p(0.62, 0.29), _p(0.67, 0.18)], fill=color, width=w)
    else:
        d.line([_p(0.50, 0.38), _p(0.35, 0.50)], fill=color, width=w)
        d.line([_p(0.50, 0.38), _p(0.65, 0.50)], fill=color, width=w)
    d.line([_p(0.50, 0.62), _p(0.39, 0.83)], fill=color, width=w)
    d.line([_p(0.50, 0.62), _p(0.61, 0.83)], fill=color, width=w)
    d.ellipse([_p(0.465, 0.18), _p(0.485, 0.20)], fill=color)
    d.ellipse([_p(0.515, 0.18), _p(0.535, 0.20)], fill=color)
    d.arc([_p(0.47, 0.20), _p(0.53, 0.255)], 0, 180, fill=color, width=3)


def _heart(d: ImageDraw.ImageDraw, color=(230, 80, 110)) -> None:
    d.ellipse([_p(0.20, 0.20), _p(0.50, 0.50)], fill=color)
    d.ellipse([_p(0.50, 0.20), _p(0.80, 0.50)], fill=color)
    d.polygon([_p(0.205, 0.37), _p(0.795, 0.37), _p(0.50, 0.82)], fill=color)


def _star(d: ImageDraw.ImageDraw, color=(248, 196, 40)) -> None:
    cx, cy, r = 0.50, 0.48, 0.30
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.43
        a = -math.pi / 2 + i * math.pi / 5
        pts.append(_p(cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color, outline=(200, 150, 20))


def _flower(d: ImageDraw.ImageDraw) -> None:
    cx, cy, r = 0.50, 0.44, 0.13
    for i in range(6):
        a = i * math.pi / 3
        px, py = cx + 0.19 * math.cos(a), cy + 0.19 * math.sin(a)
        d.ellipse([_p(px - r, py - r), _p(px + r, py + r)],
                  fill=(250, 180, 210), outline=(220, 130, 170), width=3)
    d.ellipse([_p(cx - 0.10, cy - 0.10), _p(cx + 0.10, cy + 0.10)],
              fill=(250, 210, 80), outline=(210, 160, 30), width=3)
    d.line([_p(0.50, 0.55), _p(0.50, 0.84)], fill=(90, 170, 100), width=7)
    d.arc([_p(0.50, 0.66), _p(0.64, 0.76)], 180, 300, fill=(90, 170, 100), width=6)


def _sun(d: ImageDraw.ImageDraw) -> None:
    cx, cy, r = 0.50, 0.46, 0.16
    d.ellipse([_p(cx - r, cy - r), _p(cx + r, cy + r)],
              fill=(255, 215, 70), outline=(230, 170, 30), width=4)
    for i in range(12):
        a = i * math.pi / 6
        x1, y1 = cx + (r + 0.04) * math.cos(a), cy + (r + 0.04) * math.sin(a)
        x2, y2 = cx + (r + 0.12) * math.cos(a), cy + (r + 0.12) * math.sin(a)
        d.line([_p(x1, y1), _p(x2, y2)], fill=(240, 180, 40), width=5)


def _cloud(d: ImageDraw.ImageDraw) -> None:
    color = (210, 230, 245)
    edge = (140, 180, 220)
    for box in ((0.20, 0.36, 0.48, 0.58), (0.34, 0.28, 0.62, 0.56),
                (0.48, 0.36, 0.76, 0.58), (0.30, 0.44, 0.70, 0.64)):
        d.ellipse([_p(box[0], box[1]), _p(box[2], box[3])], fill=color, outline=edge, width=3)
    d.rectangle([_p(0.28, 0.48), _p(0.70, 0.62)], fill=color)
    d.line([_p(0.30, 0.62), _p(0.68, 0.62)], fill=edge, width=3)


def _house(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([_p(0.24, 0.42), _p(0.76, 0.80)], fill=(250, 220, 180),
                outline=INK, width=5)
    d.polygon([_p(0.18, 0.44), _p(0.50, 0.18), _p(0.82, 0.44)],
              fill=(220, 110, 90), outline=INK)
    d.rectangle([_p(0.45, 0.60), _p(0.55, 0.80)], fill=(150, 100, 70), outline=INK, width=4)
    d.rectangle([_p(0.30, 0.50), _p(0.40, 0.58)], fill=(180, 220, 245), outline=INK, width=3)
    d.rectangle([_p(0.60, 0.50), _p(0.70, 0.58)], fill=(180, 220, 245), outline=INK, width=3)


def _tree(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([_p(0.46, 0.56), _p(0.54, 0.84)], fill=(150, 100, 70), outline=INK, width=3)
    for box, col in (((0.28, 0.20, 0.58, 0.50), (120, 190, 120)),
                     ((0.42, 0.16, 0.72, 0.48), (90, 170, 100)),
                     ((0.34, 0.34, 0.66, 0.62), (110, 180, 110))):
        d.ellipse([_p(box[0], box[1]), _p(box[2], box[3])], fill=col, outline=(60, 130, 80), width=3)


def _mushroom(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([_p(0.43, 0.50), _p(0.57, 0.80)], fill=(250, 235, 210),
                outline=INK, width=4)
    d.pieslice([_p(0.20, 0.24), _p(0.80, 0.62)], 180, 360, fill=(230, 90, 90),
               outline=INK, width=4)
    d.rectangle([_p(0.20, 0.43), _p(0.80, 0.50)], fill=(230, 90, 90))
    for cx, cy, r in ((0.36, 0.36, 0.035), (0.54, 0.31, 0.03), (0.64, 0.39, 0.025)):
        d.ellipse([_p(cx - r, cy - r), _p(cx + r, cy + r)], fill=(255, 245, 235))


def _smiley(d: ImageDraw.ImageDraw) -> None:
    d.ellipse([_p(0.20, 0.18), _p(0.80, 0.78)], fill=(255, 220, 90),
              outline=(220, 160, 30), width=5)
    d.ellipse([_p(0.36, 0.38), _p(0.42, 0.46)], fill=INK)
    d.ellipse([_p(0.58, 0.38), _p(0.64, 0.46)], fill=INK)
    d.arc([_p(0.34, 0.46), _p(0.66, 0.68)], 10, 170, fill=INK, width=5)


SUPPORTED_SUBJECTS = ("鲸", "猫", "人", "心", "星", "花", "太阳", "云",
                      "房", "屋", "树", "蘑菇", "笑", "脸", "自己", "女孩", "男孩")


def supports(subject: str) -> bool:
    s = str(subject or "")
    return any(k in s for k in SUPPORTED_SUBJECTS)


def draw_simple(style: str = "stick", subject: str = "猫", caption: str = "",
                pose: str = "stand", color=None) -> bytes:
    """画一张简单图，返回 PNG 字节。"""
    style = str(style or "stick").lower()
    subject = str(subject or "猫").strip()
    if style == "pixel" or "像素" in subject:
        return draw_pixel_art(subject, caption=caption)

    im = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(im)
    _frame(d)
    s = subject.lower()
    if "鲸" in subject:
        _whale(d)
    elif "猫" in subject:
        _cat(d, _color(color, INK))
    elif "人" in subject or "自己" in subject or "女孩" in subject or "男孩" in subject:
        _person(d, pose=pose, color=_color(color, INK))
    elif "心" in subject or "爱" in subject:
        _heart(d)
    elif "星" in subject:
        _star(d)
    elif "花" in subject:
        _flower(d)
    elif "太阳" in subject or "日" in subject:
        _sun(d)
    elif "云" in subject:
        _cloud(d)
    elif "房" in subject or "屋" in subject:
        _house(d)
    elif "树" in subject:
        _tree(d)
    elif "蘑菇" in subject:
        _mushroom(d)
    else:
        _smiley(d)
    _caption(d, caption)
    return _out(im)


# ---------------- 像素画 ----------------

PIXEL_TEMPLATES = {
    "heart": [
        "................",
        "................",
        "..RRR....RRR....",
        ".RRRRR..RRRRR...",
        "RRRRRRRRRRRRRR..",
        "RRRRRRRRRRRRRR..",
        "RRRRRRRRRRRRRR..",
        ".RRRRRRRRRRRR...",
        "..RRRRRRRRRR....",
        "...RRRRRRRR.....",
        "....RRRRRR......",
        ".....RRRR.......",
        "......RR........",
        "................",
        "................",
        "................",
    ],
    "cat": [
        "................",
        "..K..........K..",
        "..KK........KK..",
        "..KKKK....KKKK..",
        "..KKKKKKKKKKKK..",
        ".KKKKKKKKKKKKKK.",
        ".KKWWKKKKKKWWKK.",
        ".KKWBKKKKKKBWKK.",
        ".KKKKKKPPKKKKKK.",
        ".KKKKKKPPKKKKKK.",
        "..KKKKKKKKKKKK..",
        "..KKKKKKKKKKKK..",
        "...KKKKKKKKKK...",
        "....KKKKKKKK....",
        "................",
        "................",
    ],
    "whale": [
        "................",
        ".......BB.......",
        "......BBBB......",
        ".....BBBBBB.....",
        "....BBBBBBBB....",
        "...BBBBBBBBBB...",
        "..BBBBBBBBBBBB..",
        ".BBBBBBBBBBBBBB.",
        ".BBBBBBBBBBBBBB.",
        "..BBBBBBBBBBBB..",
        "...BBBBBBBBBB...",
        "....BBBBBBBB....",
        ".....BBBBBB.....",
        "................",
        "................",
        "................",
    ],
    "star": [
        "................",
        ".......YY.......",
        ".......YY.......",
        "......YYYY......",
        "......YYYY......",
        ".YYYYYYYYYYYYYY.",
        "..YYYYYYYYYYYY..",
        "...YYYYYYYYYY...",
        "....YYYYYYYY....",
        "...YYYYYYYYYY...",
        "..YYYYY..YYYYY..",
        "..YYY......YYY..",
        ".YY..........YY.",
        "................",
        "................",
        "................",
    ],
    "flower": [
        "................",
        "......PPPP......",
        "....PPPPPPPP....",
        "...PPPPPPPPPP...",
        "...PPPYYYYPPP...",
        "...PPPYYYYPPP...",
        "...PPPPPPPPPP...",
        "....PPPPPPPP....",
        "......PPPP......",
        ".......GG.......",
        ".......GG.......",
        "....GG.GG.......",
        "......GGG.......",
        ".......GG.......",
        "................",
        "................",
    ],
    "mushroom": [
        "................",
        "................",
        "....RRRRRRRR....",
        "..RRRRRRRRRRRR..",
        ".RRRWWRRRRWWRRR.",
        "RRRRWWRRRRWWRRRR",
        "RRRRRRRRRRRRRRRR",
        ".RRRRRRRRRRRRRR.",
        "..RRRRRRRRRRRR..",
        ".....WWWWWW.....",
        ".....WWWWWW.....",
        ".....WWWWWW.....",
        ".....WWWWWW.....",
        ".....WWWWWW.....",
        "................",
        "................",
    ],
    "smiley": [
        "................",
        "....YYYYYYYY....",
        "..YYYYYYYYYYYY..",
        ".YYYYYYYYYYYYYY.",
        ".YYYKKYYYYKKYYY.",
        ".YYYKKYYYYKKYYY.",
        ".YYYYYYYYYYYYYY.",
        ".YYYYYYYYYYYYYY.",
        ".YYYKYYYYYYKYYY.",
        ".YYYYKKKKKKYYYY.",
        "..YYYYYYYYYYYY..",
        "...YYYYYYYYYY...",
        "....YYYYYYYY....",
        "................",
        "................",
        "................",
    ],
}

PIXEL_PALETTE = {
    ".": None,
    "R": (230, 70, 90),
    "K": (40, 44, 52),
    "W": (255, 255, 255),
    "B": (80, 150, 230),
    "Y": (248, 196, 40),
    "G": (90, 180, 110),
    "P": (240, 140, 180),
}


def _pixel_subject(subject: str) -> str:
    s = str(subject or "").lower()
    if "心" in subject or "heart" in s or "爱" in subject:
        return "heart"
    if "猫" in subject or "cat" in s:
        return "cat"
    if "鲸" in subject or "whale" in s:
        return "whale"
    if "星" in subject or "star" in s:
        return "star"
    if "花" in subject or "flower" in s:
        return "flower"
    if "蘑菇" in subject or "mushroom" in s:
        return "mushroom"
    if "笑" in subject or "脸" in subject or "smiley" in s:
        return "smiley"
    return "heart"


def draw_pixel_art(subject: str = "heart", grid=None, palette=None,
                   caption: str = "", scale: int = 32) -> bytes:
    """16x16 像素画；也接受自定义 grid（字符串列表或二维数组）。"""
    if isinstance(grid, list) and grid:
        rows = []
        for row in grid:
            if isinstance(row, str):
                rows.append(row)
            elif isinstance(row, (list, tuple)):
                rows.append("".join(str(x) for x in row))
        if not rows:
            rows = PIXEL_TEMPLATES["heart"]
    else:
        rows = PIXEL_TEMPLATES.get(_pixel_subject(subject), PIXEL_TEMPLATES["heart"])

    h = len(rows)
    w = max(len(r) for r in rows)
    scale = max(8, min(48, int(scale or 32)))
    art_w, art_h = w * scale, h * scale
    canvas_w = max(art_w + 80, 480)
    canvas_h = art_h + 110
    im = Image.new("RGB", (canvas_w, canvas_h), BG)
    d = ImageDraw.Draw(im)
    ox = (canvas_w - art_w) // 2
    oy = 40
    pal = dict(PIXEL_PALETTE)
    if isinstance(palette, dict):
        for k, v in palette.items():
            try:
                pal[str(k)] = _color(v, (255, 255, 255))
            except Exception:
                continue
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            c = pal.get(ch)
            if not c:
                continue
            d.rectangle([ox + x * scale, oy + y * scale,
                         ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1], fill=c)
    # 像素网格
    for x in range(w + 1):
        d.line([(ox + x * scale, oy), (ox + x * scale, oy + art_h)],
               fill=(235, 230, 220), width=1)
    for y in range(h + 1):
        d.line([(ox, oy + y * scale), (ox + art_w, oy + y * scale)],
               fill=(235, 230, 220), width=1)
    d.rounded_rectangle([ox - 8, oy - 8, ox + art_w + 8, oy + art_h + 8],
                        radius=16, outline=(210, 200, 185), width=3)
    text = str(caption or "").strip()
    if text:
        d.text((canvas_w // 2, canvas_h - 38), text[:24], font=_font(30, True),
               fill=INK, anchor="mm")
    return _out(im)


# ---------------- 图片标注 ----------------

def _norm_box(op: dict, w: int, h: int) -> tuple[int, int, int, int]:
    box = op.get("box")
    if isinstance(box, (list, tuple)) and len(box) == 4:
        try:
            x1, y1, x2, y2 = [float(v) for v in box]
            return (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h))
        except Exception:
            pass
    center = op.get("center")
    if isinstance(center, (list, tuple)) and len(center) == 2:
        try:
            cx, cy = float(center[0]), float(center[1])
            r = float(op.get("radius", 0.15))
            return (int((cx - r) * w), int((cy - r) * h),
                    int((cx + r) * w), int((cy + r) * h))
        except Exception:
            pass
    pos = str(op.get("position") or op.get("target") or "center")
    table = {
        "左上": (0.16, 0.16, 0.44, 0.44), "top-left": (0.16, 0.16, 0.44, 0.44),
        "右上": (0.56, 0.16, 0.84, 0.44), "top-right": (0.56, 0.16, 0.84, 0.44),
        "左下": (0.16, 0.56, 0.44, 0.84), "bottom-left": (0.16, 0.56, 0.44, 0.84),
        "右下": (0.56, 0.56, 0.84, 0.84), "bottom-right": (0.56, 0.56, 0.84, 0.84),
        "左": (0.10, 0.34, 0.42, 0.66), "left": (0.10, 0.34, 0.42, 0.66),
        "右": (0.58, 0.34, 0.90, 0.66), "right": (0.58, 0.34, 0.90, 0.66),
        "上": (0.34, 0.10, 0.66, 0.42), "top": (0.34, 0.10, 0.66, 0.42),
        "下": (0.34, 0.58, 0.66, 0.90), "bottom": (0.34, 0.58, 0.66, 0.90),
        "中间": (0.34, 0.34, 0.66, 0.66), "中心": (0.34, 0.34, 0.66, 0.66),
        "center": (0.34, 0.34, 0.66, 0.66),
    }
    x1, y1, x2, y2 = table["center"]
    for key in sorted(table, key=len, reverse=True):
        if key in pos:
            x1, y1, x2, y2 = table[key]
            break
    return (int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h))


def _norm_point(value, default=(0.5, 0.5), w: int = 1, h: int = 1):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return int(float(value[0]) * w), int(float(value[1]) * h)
        except Exception:
            pass
    return int(default[0] * w), int(default[1] * h)


def _arrowhead(d: ImageDraw.ImageDraw, start, end, color, width: int) -> None:
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = max(16, width * 5)
    for a in (ang + math.pi * 0.82, ang - math.pi * 0.82):
        d.line([end, (end[0] + size * math.cos(a), end[1] + size * math.sin(a))],
               fill=color, width=width)


def annotate(data: bytes, ops: list[dict], max_size: int = 1280) -> bytes:
    """在图片上画圈、箭头、涂鸦、文字或高亮，返回 PNG 字节。"""
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    if max(im.size) > max_size:
        im.thumbnail((max_size, max_size), Image.LANCZOS)
    w, h = im.size
    for op in (ops or [])[:6]:
        if not isinstance(op, dict):
            continue
        kind = str(op.get("type") or "circle").lower()
        color = _color(op.get("color", "red"))
        width = max(3, int(op.get("width") or max(4, w // 160)))
        overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        if kind == "circle":
            box = _norm_box(op, w, h)
            d.ellipse(box, outline=color + (255,), width=width)
        elif kind in ("scribble", "doodle"):
            x1, y1, x2, y2 = _norm_box(op, w, h)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            rx, ry = max(8, (x2 - x1) / 2), max(8, (y2 - y1) / 2)
            pts = []
            for i in range(72):
                t = 2 * math.pi * i / 72
                r = 1 + 0.07 * math.sin(5 * t + 0.8)
                pts.append((cx + rx * r * math.cos(t), cy + ry * r * math.sin(t)))
            d.line(pts + [pts[0]], fill=color + (255,), width=width, joint="curve")
        elif kind == "arrow":
            start = _norm_point(op.get("from"), (0.18, 0.82), w, h)
            end = _norm_point(op.get("to"), (0.50, 0.50), w, h)
            d.line([start, end], fill=color + (255,), width=width)
            _arrowhead(d, start, end, color + (255,), width)
        elif kind == "line":
            start = _norm_point(op.get("from"), (0.2, 0.5), w, h)
            end = _norm_point(op.get("to"), (0.8, 0.5), w, h)
            d.line([start, end], fill=color + (255,), width=width)
        elif kind == "highlight":
            box = _norm_box(op, w, h)
            d.ellipse(box, fill=color + (70,))
        elif kind == "text":
            text = str(op.get("text") or op.get("label") or "").strip()
            if not text:
                continue
            x, y = _norm_point(op.get("at") or op.get("position"), (0.5, 0.16), w, h)
            size = max(18, int(float(op.get("size") or 0.06) * w))
            font = _font(size, bold=True)
            d.text((x, y), text[:30], font=font, fill=color + (255,),
                   stroke_width=max(2, width // 2), stroke_fill=(255, 255, 255, 235),
                   anchor="mm")
        im = Image.alpha_composite(im, overlay)
    return _out(im)



def _fit_square(im, size=512):
    im = ImageOps.exif_transpose(im).convert("RGB")
    return ImageOps.fit(im, (size, size), Image.LANCZOS, centering=(0.5, 0.42))


def _art_panel(art, caption="", grid_step=0):
    art = art.convert("RGB")
    canvas = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(canvas)
    _frame(d)
    scale = min(520 / art.width, 520 / art.height)
    w, h = int(art.width * scale), int(art.height * scale)
    art = art.resize((w, h), Image.NEAREST if grid_step else Image.LANCZOS)
    ox, oy = (SIZE - w) // 2, 40 + (520 - h) // 2
    if grid_step:
        grid = Image.new("RGBA", art.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(grid)
        for x in range(0, art.width, grid_step):
            gd.line([(x, 0), (x, art.height)], fill=(235, 230, 220, 90), width=1)
        for y in range(0, art.height, grid_step):
            gd.line([(0, y), (art.width, y)], fill=(235, 230, 220, 90), width=1)
        art = Image.alpha_composite(art.convert("RGBA"), grid).convert("RGB")
    canvas.paste(art, (ox, oy))
    d.rounded_rectangle([ox - 8, oy - 8, ox + w + 8, oy + h + 8],
                        radius=16, outline=(210, 200, 185), width=3)
    _caption(d, caption)
    return _out(canvas)


def from_reference(data: bytes, style: str = "outline", caption: str = "",
                   pixel_size: int = 32, colors: int = 8) -> bytes:
    """把参考图风格化：描边、铅笔、像素、海报、剪影。"""
    style = str(style or "outline").lower()
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im).convert("RGB")
    if style in ("pixel", "像素", "像素化", "像素风", "abstract", "抽象"):
        pixel_size = max(16, min(64, int(pixel_size or 32)))
        small = _fit_square(im, pixel_size)
        small = ImageEnhance.Contrast(small).enhance(1.12)
        small = ImageEnhance.Color(small).enhance(1.25)
        small = small.quantize(colors=max(4, min(16, int(colors or 8))), method=Image.MEDIANCUT).convert("RGB")
        art = small.resize((512, 512), Image.NEAREST)
        return _art_panel(art, caption, grid_step=max(8, 512 // pixel_size))
    if style in ("outline", "线稿", "描边", "简笔", "简笔画", "edge", "edges"):
        gray = ImageOps.grayscale(_fit_square(im, 640))
        gray = ImageOps.autocontrast(gray).filter(ImageFilter.MedianFilter(5))
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edges = ImageOps.invert(edges)
        edges = edges.point(lambda p: 0 if p < 200 else 255)
        edges = edges.filter(ImageFilter.MinFilter(3))
        return _art_panel(edges.convert("RGB"), caption)
    if style in ("sketch", "铅笔", "素描", "铅笔画"):
        gray = ImageOps.grayscale(_fit_square(im, 640))
        try:
            import numpy as np
            g = np.asarray(gray, dtype=np.float32)
            inv = 255.0 - g
            blur = np.asarray(
                Image.fromarray(inv.astype(np.uint8)).filter(ImageFilter.GaussianBlur(8)),
                dtype=np.float32,
            )
            out = np.clip(g * 255.0 / (255.0 - blur + 1.0), 0, 255).astype(np.uint8)
            sketch = Image.fromarray(out)
        except Exception:
            sketch = ImageOps.autocontrast(gray)
        return _art_panel(sketch.convert("RGB"), caption)
    if style in ("stencil", "剪影", "版画", "黑白", "黑白剪影"):
        gray = ImageOps.grayscale(_fit_square(im, 640))
        gray = ImageOps.autocontrast(gray).filter(ImageFilter.MedianFilter(5))
        bw = gray.point(lambda p: 0 if p < 110 else 255)
        return _art_panel(bw.convert("RGB"), caption)
    small = _fit_square(im, 512)
    small = ImageEnhance.Color(small).enhance(1.15)
    art = ImageOps.posterize(small, 3)
    return _art_panel(art, caption)
