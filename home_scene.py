# -*- coding: utf-8 -*-
"""小鲸的像素卧室：3/4 上帝视角，540x720 内部画布，2x 最近邻输出。

这个模块只负责“画”，不读写聊天状态。活动、心情、精力由 main.py 传入。
"""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 540, 720
SCALE = 2

# ---------------- 调色板 ----------------
OUTLINE = (24, 24, 40)
WALL = (38, 52, 86)
WALL_ALT = (45, 62, 100)
WAINSCOT = (70, 48, 42)
FLOOR = (122, 82, 58)
FLOOR_ALT = (136, 94, 66)
FLOOR_LINE = (92, 60, 42)
WOOD_LIGHT = (180, 128, 86)
WOOD_MID = (142, 96, 64)
WOOD_DARK = (92, 58, 40)
CREAM = (246, 234, 212)
CREAM_DARK = (220, 204, 180)
BLANKET = (52, 74, 120)
BLANKET_ALT = (68, 94, 148)
RUG = (196, 142, 96)
RUG_LIGHT = (226, 180, 130)
PILLOW = (252, 246, 230)
MOON = (255, 236, 170)
SEA = (36, 74, 104)
NIGHT_TOP = (18, 26, 52)
NIGHT_BOTTOM = (40, 60, 96)
SKIN = (255, 214, 190)
SKIN_SHADE = (230, 176, 150)
HAIR = (52, 82, 170)
HAIR_LIGHT = (78, 112, 210)
HAIR_DARK = (34, 54, 120)
DRESS = (34, 48, 82)
DRESS_LIGHT = (46, 64, 104)
APRON = (244, 238, 224)
TAIL = (44, 62, 104)
RED = (214, 72, 72)
YELLOW = (240, 196, 80)
GREEN = (88, 150, 96)
GREEN_DARK = (58, 108, 70)
CAT = (230, 160, 90)
CAT_DARK = (190, 118, 62)
SCREEN = (40, 70, 110)
SCREEN_LIGHT = (90, 160, 220)
SHADOW = (20, 24, 42, 90)
ACCENT = (240, 196, 120)
WHITE = (250, 248, 240)


FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def _font(size: int, bold: bool = False):
    path = FONT_DIR / ("msyhbd.ttc" if bold else "msyh.ttc")
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _text(d, xy, text, size=14, color=WHITE, bold=False, anchor="la"):
    d.text(xy, text, font=_font(size, bold), fill=color,
           stroke_width=2, stroke_fill=OUTLINE, anchor=anchor)


def _blend(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_room(d):
    d.rectangle([0, 0, W, H], fill=WALL)
    for x in range(0, W, 36):
        d.rectangle([x, 0, x + 18, 300], fill=WALL_ALT)
    d.rectangle([0, 270, W, 300], fill=WAINSCOT)
    for x in range(0, W, 54):
        d.rectangle([x + 8, 276, x + 46, 294], fill=WOOD_MID, outline=OUTLINE)
    d.rectangle([0, 298, W, 306], fill=WOOD_LIGHT, outline=OUTLINE)
    d.rectangle([0, 306, W, H], fill=FLOOR)
    for y in range(306, H, 26):
        d.rectangle([0, y, W, y + 2], fill=FLOOR_LINE)
        off = 0 if (y // 26) % 2 == 0 else 45
        for x in range(-60 + off, W, 90):
            d.line([x, y, x, y + 26], fill=FLOOR_LINE)


def draw_window(d, night=True):
    x, y, w, h = 55, 62, 170, 190
    d.rectangle([x - 8, y - 8, x + w + 8, y + h + 8], fill=WOOD_LIGHT, outline=OUTLINE)
    if night:
        for i in range(h):
            d.line([x, y + i, x + w, y + i], fill=_blend(NIGHT_TOP, NIGHT_BOTTOM, i / h))
        for sx, sy in ((20, 25), (48, 52), (78, 20), (112, 44), (142, 28), (30, 78), (128, 82), (92, 68)):
            d.rectangle([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=MOON)
        d.ellipse([x + w - 52, y + 20, x + w - 18, y + 54], fill=MOON, outline=OUTLINE)
        sea = SEA
    else:
        for i in range(h):
            d.line([x, y + i, x + w, y + i], fill=_blend((116, 176, 228), (176, 214, 242), i / h))
        d.ellipse([x + w - 54, y + 20, x + w - 18, y + 56], fill=(255, 224, 140), outline=OUTLINE)
        for cx, cy, r in ((x + 24, y + 42, 16), (x + 44, y + 36, 20), (x + 66, y + 44, 14)):
            d.ellipse([cx - r, cy - r // 2, cx + r, cy + r // 2], fill=(250, 250, 245), outline=OUTLINE)
        sea = (72, 144, 184)
    # sea
    d.rectangle([x, y + h - 56, x + w, y + h], fill=sea)
    for i in range(4):
        d.line([x + 4, y + h - 48 + i * 11, x + w - 4, y + h - 48 + i * 11],
               fill=(60, 108, 140) if night else (110, 180, 214))
    # frame
    d.rectangle([x, y, x + w, y + h], outline=WOOD_LIGHT, width=5)
    d.line([x + w // 2, y, x + w // 2, y + h], fill=WOOD_LIGHT, width=4)
    d.line([x, y + h // 2, x + w, y + h // 2], fill=WOOD_LIGHT, width=4)
    # curtains
    d.polygon([(x - 16, y - 12), (x + 10, y - 12), (x + 28, y + h + 12), (x - 4, y + h + 12)],
              fill=BLANKET, outline=OUTLINE)
    d.polygon([(x + w - 10, y - 12), (x + w + 16, y - 12), (x + w + 4, y + h + 12), (x + w - 28, y + h + 12)],
              fill=BLANKET, outline=OUTLINE)
    d.rectangle([x - 16, y - 14, x - 4, y + h + 12], fill=BLANKET_ALT)


def draw_bed(d):
    x, y, w, h = 24, 330, 210, 205
    d.ellipse([x + 8, y + h - 8, x + w + 8, y + h + 18], fill=(20, 24, 42, 110))
    d.rectangle([x - 4, y - 38, x + w + 4, y + 10], fill=WOOD_DARK, outline=OUTLINE)
    for i in range(5):
        d.rectangle([x + 8 + i * 40, y - 34, x + 12 + i * 40, y + 6], fill=WOOD_MID)
    d.rectangle([x, y, x + w, y + h], fill=CREAM_DARK, outline=OUTLINE)
    # sheet fold at the head
    d.rectangle([x + 6, y + 46, x + w - 6, y + 62], fill=PILLOW, outline=OUTLINE)
    d.rectangle([x + 6, y + 62, x + w - 6, y + h - 6], fill=BLANKET, outline=OUTLINE)
    for i in range(3):
        d.rectangle([x + 14, y + 76 + i * 30, x + w - 14, y + 84 + i * 30], fill=BLANKET_ALT)
    # folded throw at the foot
    d.rectangle([x + 8, y + h - 34, x + w - 8, y + h - 10], fill=BLANKET_ALT, outline=OUTLINE)
    d.rectangle([x + 14, y + h - 30, x + w - 14, y + h - 24], fill=CREAM)
    d.rounded_rectangle([x + 14, y + 12, x + 88, y + 54], radius=9, fill=PILLOW, outline=OUTLINE)
    d.rounded_rectangle([x + 94, y + 14, x + 150, y + 50], radius=8, fill=PILLOW, outline=OUTLINE)
    # whale plush on pillow
    d.ellipse([x + 158, y + 24, x + 192, y + 46], fill=HAIR_LIGHT, outline=OUTLINE)
    d.polygon([(x + 184, y + 26), (x + 198, y + 32), (x + 184, y + 38)], fill=HAIR_LIGHT, outline=OUTLINE)
    d.rectangle([x + 166, y + 32, x + 170, y + 36], fill=OUTLINE)
    d.rectangle([x + 176, y + 32, x + 180, y + 36], fill=OUTLINE)


def draw_rug(d):
    x, y, w, h = 150, 520, 250, 150
    d.ellipse([x, y, x + w, y + h], fill=RUG, outline=OUTLINE)
    d.ellipse([x + 12, y + 12, x + w - 12, y + h - 12], outline=RUG_LIGHT, width=3)
    d.ellipse([x + 28, y + 26, x + w - 28, y + h - 26], outline=RUG_LIGHT, width=2)
    for i in range(0, w, 12):
        d.line([x + i, y + h, x + i, y + h + 8], fill=RUG_LIGHT)


def draw_desk(d):
    x, y, w, h = 306, 336, 204, 110
    d.ellipse([x + 10, y + h - 6, x + w - 4, y + h + 20], fill=(20, 24, 42, 110))
    d.polygon([(x, y + 24), (x + w, y + 24), (x + w - 12, y + 4), (x + 12, y + 4)],
              fill=WOOD_LIGHT, outline=OUTLINE)
    d.rectangle([x + 10, y + 24, x + w - 10, y + 86], fill=WOOD_MID, outline=OUTLINE)
    d.rectangle([x + 18, y + 86, x + 30, y + 120], fill=WOOD_DARK, outline=OUTLINE)
    d.rectangle([x + w - 30, y + 86, x + w - 18, y + 120], fill=WOOD_DARK, outline=OUTLINE)
    # monitor
    d.rectangle([x + 46, y - 64, x + 154, y + 10], fill=OUTLINE)
    d.rectangle([x + 52, y - 58, x + 148, y + 4], fill=SCREEN)
    d.rectangle([x + 60, y - 50, x + 140, y - 14], fill=SCREEN_LIGHT)
    for i in range(3):
        d.rectangle([x + 68, y - 42 + i * 8, x + 128 - i * 10, y - 39 + i * 8], fill=SCREEN)
    d.rectangle([x + 86, y + 10, x + 114, y + 18], fill=WOOD_DARK)
    # keyboard + mouse
    d.rectangle([x + 64, y + 38, x + 146, y + 56], fill=OUTLINE)
    for i in range(6):
        d.rectangle([x + 70 + i * 12, y + 43, x + 76 + i * 12, y + 50], fill=CREAM_DARK)
    d.ellipse([x + 158, y + 40, x + 174, y + 56], fill=OUTLINE)
    # lamp
    d.rectangle([x + 172, y - 34, x + 184, y + 24], fill=WOOD_DARK)
    d.polygon([(x + 166, y - 34), (x + 190, y - 34), (x + 182, y - 48), (x + 174, y - 48)],
              fill=YELLOW, outline=OUTLINE)
    # papers
    d.rectangle([x + 22, y + 40, x + 48, y + 54], fill=CREAM, outline=OUTLINE)
    d.rectangle([x + 26, y + 44, x + 44, y + 46], fill=WOOD_MID)


def draw_shelf(d):
    x, y, w, h = 430, 96, 92, 204
    d.rectangle([x, y, x + w, y + h], fill=WOOD_DARK, outline=OUTLINE)
    for i in range(4):
        sy = y + 14 + i * 46
        d.rectangle([x + 8, sy, x + w - 8, sy + 5], fill=WOOD_LIGHT)
        bx = x + 12
        colors = (RED, BLANKET_ALT, YELLOW, GREEN, CREAM_DARK, HAIR_LIGHT)
        for j in range(5):
            bw = 8 + (j * 3) % 7
            bh = 20 + (j * 5) % 12
            d.rectangle([bx, sy - bh, bx + bw, sy - 1], fill=colors[(i + j) % len(colors)], outline=OUTLINE)
            bx += bw + 2
    d.rectangle([x + 14, y - 10, x + 38, y + 2], fill=GREEN, outline=OUTLINE)
    d.rectangle([x + 40, y - 6, x + 58, y + 2], fill=CREAM, outline=OUTLINE)


def draw_plant(d):
    x, y = 18, 236
    d.polygon([(x, y + 52), (x + 44, y + 52), (x + 36, y + 92), (x + 8, y + 92)],
              fill=WOOD_MID, outline=OUTLINE)
    d.rectangle([x + 4, y + 48, x + 40, y + 54], fill=WOOD_LIGHT, outline=OUTLINE)
    for dx, dy, r in ((8, 20, 16), (24, 8, 14), (36, 22, 15), (18, 30, 13)):
        d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=GREEN, outline=OUTLINE)
    d.line([x + 22, y + 48, x + 22, y + 20], fill=GREEN_DARK, width=3)


def draw_chair(d, x=270, y=404):
    d.ellipse([x - 30, y + 34, x + 30, y + 48], fill=(20, 24, 42, 100))
    # back
    d.rectangle([x - 22, y - 18, x + 22, y + 4], fill=WOOD_DARK, outline=OUTLINE)
    d.rectangle([x - 18, y - 14, x + 18, y + 0], fill=WOOD_MID)
    # seat, wider than the character so it reads as a chair
    d.rectangle([x - 28, y + 10, x + 28, y + 22], fill=WOOD_LIGHT, outline=OUTLINE)
    d.rectangle([x - 24, y + 14, x + 24, y + 18], fill=CREAM_DARK)
    # legs
    d.rectangle([x - 26, y + 22, x - 19, y + 48], fill=WOOD_DARK, outline=OUTLINE)
    d.rectangle([x + 19, y + 22, x + 26, y + 48], fill=WOOD_DARK, outline=OUTLINE)


def draw_posters(d):
    # whale poster
    d.rectangle([248, 86, 326, 174], fill=CREAM, outline=OUTLINE)
    d.rectangle([254, 92, 320, 168], fill=BLANKET, outline=OUTLINE)
    d.ellipse([270, 112, 304, 136], fill=HAIR_LIGHT, outline=OUTLINE)
    d.polygon([(298, 114), (314, 120), (298, 128)], fill=HAIR_LIGHT, outline=OUTLINE)
    d.rectangle([278, 120, 282, 124], fill=OUTLINE)
    d.rectangle([290, 120, 294, 124], fill=OUTLINE)
    # controller poster
    d.rectangle([340, 104, 404, 164], fill=CREAM, outline=OUTLINE)
    d.rectangle([346, 110, 398, 158], fill=(228, 180, 120), outline=OUTLINE)
    d.rectangle([356, 128, 388, 142], fill=(40, 40, 54), outline=OUTLINE)
    d.rectangle([360, 132, 366, 138], fill=RED)
    d.rectangle([378, 132, 384, 138], fill=HAIR_LIGHT)


def draw_cat(d, x=330, y=600):
    d.ellipse([x, y + 8, x + 46, y + 30], fill=CAT, outline=OUTLINE)
    d.ellipse([x + 28, y, x + 50, y + 22], fill=CAT, outline=OUTLINE)
    d.polygon([(x + 30, y + 4), (x + 34, y - 6), (x + 39, y + 4)], fill=CAT, outline=OUTLINE)
    d.polygon([(x + 42, y + 4), (x + 47, y - 6), (x + 51, y + 4)], fill=CAT, outline=OUTLINE)
    d.rectangle([x + 34, y + 9, x + 37, y + 12], fill=OUTLINE)
    d.rectangle([x + 43, y + 9, x + 46, y + 12], fill=OUTLINE)
    d.line([x + 46, y + 22, x + 58, y + 14], fill=CAT_DARK, width=3)
    d.line([x + 4, y + 22, x - 6, y + 16], fill=CAT_DARK, width=3)


def _shadow(d, x, y, w):
    d.ellipse([x - w // 2, y - 6, x + w // 2, y + 6], fill=(20, 24, 42, 100))


def draw_chibi(d, cx, top, pose="stand", prop="", mood="开心", flip=False):
    """画一个约 46x64 的 3/4 视角小鲸鱼。cx 是中心，top 是头顶。"""
    s = -1 if flip else 1
    # tail behind
    d.polygon([(cx + 14 * s, top + 38), (cx + 34 * s, top + 34), (cx + 42 * s, top + 48),
               (cx + 30 * s, top + 52), (cx + 38 * s, top + 60), (cx + 22 * s, top + 56)],
              fill=TAIL, outline=OUTLINE)
    # legs
    if pose == "sit":
        d.rectangle([cx - 14, top + 52, cx - 2, top + 62], fill=SKIN, outline=OUTLINE)
        d.rectangle([cx + 2, top + 52, cx + 14, top + 62], fill=SKIN, outline=OUTLINE)
        d.rectangle([cx - 16, top + 60, cx - 1, top + 64], fill=DRESS, outline=OUTLINE)
        d.rectangle([cx + 1, top + 60, cx + 16, top + 64], fill=DRESS, outline=OUTLINE)
        body_top = top + 30
        head_top = top + 2
    else:
        d.rectangle([cx - 12, top + 50, cx - 2, top + 64], fill=SKIN, outline=OUTLINE)
        d.rectangle([cx + 2, top + 50, cx + 12, top + 64], fill=SKIN, outline=OUTLINE)
        d.rectangle([cx - 15, top + 61, cx - 1, top + 66], fill=DRESS, outline=OUTLINE)
        d.rectangle([cx + 1, top + 61, cx + 15, top + 66], fill=DRESS, outline=OUTLINE)
        body_top = top + 26
        head_top = top
    _shadow(d, cx, top + 64, 44)
    # body
    d.polygon([(cx - 16, body_top), (cx + 16, body_top), (cx + 20, top + 56),
               (cx - 20, top + 56)], fill=DRESS, outline=OUTLINE)
    d.polygon([(cx - 11, body_top + 4), (cx + 11, body_top + 4), (cx + 14, top + 52),
               (cx - 14, top + 52)], fill=APRON, outline=OUTLINE)
    d.rectangle([cx - 5, body_top + 12, cx + 5, body_top + 20], fill=APRON, outline=OUTLINE)
    # whale emblem
    d.ellipse([cx - 5, body_top + 28, cx + 5, body_top + 34], fill=HAIR_LIGHT, outline=OUTLINE)
    # arms
    d.rectangle([cx - 22, body_top + 5, cx - 15, body_top + 22], fill=DRESS_LIGHT, outline=OUTLINE)
    d.rectangle([cx + 15, body_top + 5, cx + 22, body_top + 22], fill=DRESS_LIGHT, outline=OUTLINE)
    d.ellipse([cx - 24, body_top + 20, cx - 14, body_top + 28], fill=SKIN, outline=OUTLINE)
    d.ellipse([cx + 14, body_top + 20, cx + 24, body_top + 28], fill=SKIN, outline=OUTLINE)
    # head
    d.ellipse([cx - 22, head_top, cx + 22, head_top + 40], fill=SKIN, outline=OUTLINE)
    # hair cap
    d.ellipse([cx - 24, head_top - 4, cx + 24, head_top + 28], fill=HAIR, outline=OUTLINE)
    d.ellipse([cx - 18, head_top - 1, cx + 16, head_top + 12], fill=HAIR_LIGHT)
    # long hair sides
    d.polygon([(cx - 24, head_top + 10), (cx - 16, head_top + 10), (cx - 18, head_top + 46),
               (cx - 28, head_top + 38)], fill=HAIR, outline=OUTLINE)
    d.polygon([(cx + 16, head_top + 10), (cx + 24, head_top + 10), (cx + 28, head_top + 38),
               (cx + 18, head_top + 46)], fill=HAIR, outline=OUTLINE)
    # whale ears
    d.polygon([(cx - 26, head_top + 12), (cx - 38, head_top + 8), (cx - 30, head_top + 24)],
              fill=HAIR_DARK, outline=OUTLINE)
    d.polygon([(cx + 26, head_top + 12), (cx + 38, head_top + 8), (cx + 30, head_top + 24)],
              fill=HAIR_DARK, outline=OUTLINE)
    # ahoge
    d.line([cx + 2, head_top - 6, cx + 8, head_top - 14, cx + 14, head_top - 8],
           fill=HAIR_LIGHT, width=3)
    # face
    eye_y = head_top + 22
    d.ellipse([cx - 13, eye_y - 5, cx - 5, eye_y + 3], fill=WHITE, outline=OUTLINE)
    d.ellipse([cx + 5, eye_y - 5, cx + 13, eye_y + 3], fill=WHITE, outline=OUTLINE)
    d.ellipse([cx - 10, eye_y - 2, cx - 7, eye_y + 2], fill=HAIR_DARK)
    d.ellipse([cx + 7, eye_y - 2, cx + 10, eye_y + 2], fill=HAIR_DARK)
    # blush
    d.rectangle([cx - 17, eye_y + 6, cx - 12, eye_y + 8], fill=(240, 150, 150))
    d.rectangle([cx + 12, eye_y + 6, cx + 17, eye_y + 8], fill=(240, 150, 150))
    # mouth
    if mood in ("困", "低落"):
        d.line([cx - 3, eye_y + 10, cx + 3, eye_y + 10], fill=OUTLINE, width=2)
    else:
        d.arc([cx - 5, eye_y + 7, cx + 5, eye_y + 15], 0, 180, fill=OUTLINE, width=2)
    # prop
    if prop == "controller":
        d.rectangle([cx - 12, body_top + 24, cx + 12, body_top + 34], fill=(40, 40, 54), outline=OUTLINE)
        d.rectangle([cx - 8, body_top + 27, cx - 4, body_top + 31], fill=RED)
        d.rectangle([cx + 4, body_top + 27, cx + 8, body_top + 31], fill=HAIR_LIGHT)
    elif prop == "book":
        d.polygon([(cx - 14, body_top + 22), (cx + 2, body_top + 18), (cx + 14, body_top + 24),
                   (cx - 2, body_top + 30)], fill=BLANKET_ALT, outline=OUTLINE)
        d.line([cx - 2, body_top + 22, cx - 2, body_top + 30], fill=CREAM, width=1)
    elif prop == "cola":
        d.rectangle([cx + 12, body_top + 18, cx + 24, body_top + 34], fill=RED, outline=OUTLINE)
        d.rectangle([cx + 12, body_top + 22, cx + 24, body_top + 25], fill=CREAM)
        d.rectangle([cx + 15, body_top + 14, cx + 21, body_top + 18], fill=CREAM_DARK, outline=OUTLINE)
    elif prop == "notebook":
        d.rectangle([cx - 10, body_top + 23, cx + 10, body_top + 33], fill=CREAM, outline=OUTLINE)
        for i in range(2):
            d.line([cx - 6, body_top + 26 + i * 3, cx + 6, body_top + 26 + i * 3], fill=WOOD_MID)


def draw_sleeping(d):
    # 头露在枕头上，身体盖在毯子里
    x, y = 24, 330
    d.ellipse([x + 18, y + 16, x + 68, y + 58], fill=SKIN, outline=OUTLINE)
    d.ellipse([x + 14, y + 10, x + 72, y + 42], fill=HAIR, outline=OUTLINE)
    d.polygon([(x + 18, y + 24), (x + 6, y + 18), (x + 14, y + 36)], fill=HAIR_DARK, outline=OUTLINE)
    d.rectangle([x + 30, y + 34, x + 34, y + 38], fill=OUTLINE)
    d.rectangle([x + 44, y + 34, x + 48, y + 38], fill=OUTLINE)
    d.arc([x + 34, y + 38, x + 44, y + 44], 0, 180, fill=OUTLINE, width=2)
    # blanket lump
    d.ellipse([x + 70, y + 52, x + 190, y + 130], fill=BLANKET, outline=OUTLINE)
    d.rectangle([x + 80, y + 62, x + 180, y + 80], fill=BLANKET_ALT)
    # tail hanging
    d.polygon([(x + 180, y + 100), (x + 208, y + 96), (x + 214, y + 112),
               (x + 196, y + 118), (x + 204, y + 128), (x + 184, y + 120)],
              fill=TAIL, outline=OUTLINE)


def draw_hud(img, d, activity, mood, now, portrait_path):
    # top bar
    d.rectangle([0, 0, W, 46], fill=(14, 22, 40))
    d.rectangle([0, 44, W, 46], fill=ACCENT)
    _text(d, (16, 11), "小鲸的房间", 16, WHITE, True)
    _text(d, (W - 16, 12), now, 14, CREAM, False, "ra")
    # activity pill
    d.rounded_rectangle([14, H - 58, 250, H - 16], radius=14, fill=(14, 22, 40), outline=ACCENT, width=2)
    d.ellipse([26, H - 40, 34, H - 32], fill=ACCENT)
    _text(d, (42, H - 48), f"在{activity}", 14, WHITE)

    # portrait
    size = 104
    px, py = W - size - 18, H - size - 30
    d.ellipse([px - 6, py - 6, px + size + 6, py + size + 6], fill=CREAM, outline=OUTLINE, width=2)
    d.ellipse([px - 2, py - 2, px + size + 2, py + size + 2], fill=BLANKET, outline=OUTLINE)
    try:
        src = Image.open(portrait_path).convert("RGBA")
        crop = src.crop((330, 80, 730, 480)).resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
        img.paste(crop, (px, py), mask)
    except Exception:
        d.ellipse([px, py, px + size, py + size], fill=SKIN, outline=OUTLINE)
    d.ellipse([px - 2, py - 2, px + size + 2, py + size + 2], outline=ACCENT, width=2)
    _text(d, (px + size // 2, py - 18), "SELFIE", 10, CREAM, True, "ma")


def draw_lighting(img, night=True):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    if night:
        # warm lamp glow
        for r, a in ((52, 12), (36, 18), (22, 26), (12, 34)):
            od.ellipse([494 - r, 286 - r, 494 + r, 286 + r], fill=(255, 196, 110, a))
        # cool window light
        for r, a in ((112, 10), (78, 14), (46, 18)):
            od.ellipse([140 - r, 180 - r, 140 + r, 180 + r], fill=(120, 180, 255, a))
    else:
        # daylight wash + window sunbeam
        od.rectangle([0, 0, W, H], fill=(255, 244, 214, 16))
        od.polygon([(70, 250), (230, 250), (390, H), (180, H)], fill=(255, 244, 200, 20))
    # vignette
    for i in range(18):
        a = 4 + i // 3
        od.rectangle([i, i, W - i, H - i], outline=(8, 10, 22, a))
    return Image.alpha_composite(img, overlay)


def render_home_scene(activity="打游戏", mood="开心", energy=70,
                      portrait_path=None, output_path=None, now=None):
    if now is None:
        now = datetime.now().strftime("%H:%M")
    try:
        hour = int(str(now).split(":")[0])
    except Exception:
        hour = 12
    night = hour < 6 or hour >= 18
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    draw_room(d)
    draw_window(d, night)
    draw_shelf(d)
    draw_posters(d)
    draw_bed(d)
    draw_rug(d)
    draw_desk(d)
    draw_plant(d)

    act = activity or "发呆"
    if act in ("睡觉", "趴床"):
        draw_sleeping(d)
    elif act in ("写日记", "整理书桌"):
        draw_chair(d, 270, 404)
        draw_chibi(d, 270, 370, "sit", "notebook" if act == "写日记" else "", mood)
    elif act == "喝可乐":
        draw_chibi(d, 128, 408, "sit", "cola", mood)
    elif act == "看书":
        draw_chibi(d, 270, 536, "sit", "book", mood)
    elif act == "撸猫":
        draw_chibi(d, 236, 538, "sit", "", mood)
        draw_cat(d, 278, 608)
    else:
        draw_chibi(d, 270, 538, "sit", "controller", mood)
        draw_cat(d, 336, 604)

    img = draw_lighting(img, night)
    d = ImageDraw.Draw(img)
    draw_hud(img, d, act, mood, now, portrait_path)

    out = Path(output_path) if output_path else Path("home_scene.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST).save(out, "PNG")
    return out
