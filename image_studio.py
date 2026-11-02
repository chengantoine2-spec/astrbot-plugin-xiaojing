# -*- coding: utf-8 -*-
"""小鲸鱼的长期图片工坊。

- 语录卡：小鲸鱼说 + 角色立绘 + 文字气泡
- 表情包：图片/角色表情 + 上下字幕
- 成就卡：标题 + 副标题 + 角色 + 金色装饰
- 改图加字：在用户图上加字幕/标题

模板登记在 data/assets/image_templates.json，可长期增删；
渲染只依赖 Pillow，不需要图像生成模型。
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_PATH = DATA_DIR / "assets" / "image_templates.json"
FONT_DIR = Path(r"C:\Windows\Fonts")

DEFAULT_TEMPLATES = {
    "version": 1,
    "default": "quote",
    "templates": [
        {
            "id": "quote",
            "name": "小鲸鱼说",
            "kind": "quote",
            "when": "观点、总结、台词",
            "character": "assets/community/q_c49_halfbody.jpg",
            "accent": "#6EA8FF",
            "bubble": "#F7F3EA",
            "text": "#1B2540",
            "keywords": ["语录", "说", "quote", "定制图", "做张图"],
        },
        {
            "id": "meme",
            "name": "表情包字幕",
            "kind": "meme",
            "when": "情绪、吐槽、反应",
            "character": "assets/community/q_c12_smile.jpg",
            "keywords": ["表情包", "meme", "梗图", "配字"],
        },
        {
            "id": "achievement",
            "name": "成就卡",
            "kind": "achievement",
            "when": "里程碑、完成",
            "character": "assets/community/q_c50_heart.jpg",
            "accent": "#F0C46A",
            "keywords": ["成就", "达成", "里程碑"],
        },
        {
            "id": "edit",
            "name": "改图加字",
            "kind": "edit_text",
            "when": "给现有图加字",
            "keywords": ["改图", "加字", "字幕"],
        },
    ],
}


def _font(size: int, bold: bool = False):
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    try:
        return ImageFont.truetype(str(FONT_DIR / name), int(size))
    except Exception:
        return ImageFont.load_default()


def _hex(value, default):
    try:
        s = str(value or "").strip().lstrip("#")
        if len(s) == 6:
            return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        pass
    return default


def _load_templates() -> dict:
    try:
        if TEMPLATES_PATH.exists():
            data = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("templates"), list) and data["templates"]:
                return data
    except Exception:
        pass
    return DEFAULT_TEMPLATES


def templates() -> list[dict]:
    return [t for t in (_load_templates().get("templates") or []) if isinstance(t, dict)]


def pick_template(name: str = "") -> dict:
    items = templates()
    key = str(name or "").strip().lower()
    if key:
        for t in items:
            if str(t.get("id") or "").lower() == key or str(t.get("name") or "").lower() == key:
                return t
        for t in items:
            if key in [str(k).lower() for k in (t.get("keywords") or [])]:
                return t
    default = str(_load_templates().get("default") or "quote")
    for t in items:
        if str(t.get("id") or "") == default:
            return t
    return items[0] if items else DEFAULT_TEMPLATES["templates"][0]


def _asset_path(rel: str) -> Path | None:
    rel = str(rel or "").strip()
    if not rel:
        return None
    fp = (DATA_DIR / rel).resolve()
    try:
        fp.relative_to(DATA_DIR.resolve())
    except Exception:
        return None
    return fp if fp.exists() else None


def _cover(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    scale = max(size[0] / im.width, size[1] / im.height)
    nw, nh = max(size[0], int(im.width * scale + 1)), max(size[1], int(im.height * scale + 1))
    im = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - size[0]) // 2, (nh - size[1]) // 2
    return im.crop((left, top, left + size[0], top + size[1]))


def _contain(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail(size, Image.LANCZOS)
    return im


def _trim_light(im: Image.Image) -> Image.Image:
    """裁掉近白背景的空白边，让 Q 版角色在卡片里更大。"""
    im = ImageOps.exif_transpose(im).convert("RGB")
    mask = im.convert("L").point(lambda p: 255 if p < 242 else 0)
    bbox = mask.getbbox()
    return im.crop(bbox) if bbox else im


def _gradient(size: tuple[int, int], top, bottom) -> Image.Image:
    w, h = size
    im = Image.new("RGB", size, top)
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return im.convert("RGBA")


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    text = str(text or "").replace("\r", "").strip()
    if not text:
        return []
    lines: list[str] = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            if draw.textlength(trial, font=font) <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines


def _fit_text(draw, text, max_width, max_height, start=52, min_size=28, bold=True):
    for size in range(start, min_size - 1, -2):
        font = _font(size, bold)
        lines = _wrap(draw, text, font, max_width)
        line_h = int(size * 1.35)
        if len(lines) * line_h <= max_height:
            return font, lines, line_h
    font = _font(min_size, bold)
    return font, _wrap(draw, text, font, max_width), int(min_size * 1.35)


def _stroke_text(draw, xy, text, font, fill, stroke, width=6, anchor="la"):
    draw.text(xy, text, font=font, fill=fill, stroke_width=width,
              stroke_fill=stroke, anchor=anchor)


def _quote(tpl: dict, text: str, source: bytes | None = None) -> Image.Image:
    W, H = 1080, 720
    accent = _hex(tpl.get("accent"), (110, 168, 255))
    bubble = _hex(tpl.get("bubble"), (247, 243, 234))
    ink = _hex(tpl.get("text"), (27, 37, 64))
    im = _gradient((W, H), (14, 24, 50), (30, 42, 80))
    d = ImageDraw.Draw(im)

    # 背景装饰
    for x, y, r, a in ((80, 90, 160, 18), (980, 60, 120, 14), (900, 640, 220, 10)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=accent + (a,))

    d.text((64, 52), "小鲸鱼说", font=_font(34, True), fill=accent + (255,))
    d.rectangle([64, 104, 180, 109], fill=accent + (255,))

    # 气泡
    d.rounded_rectangle([56, 136, 716, 648], radius=34, fill=bubble + (255,))
    d.polygon([(690, 540), (760, 580), (690, 610)], fill=bubble + (255,))
    d.text((84, 148), "“", font=_font(120, True), fill=accent + (255,))
    font, lines, line_h = _fit_text(d, text, 560, 330, start=44, min_size=28, bold=False)
    total = len(lines[:7]) * line_h
    y = 268 + max(0, (330 - total) // 2)
    for line in lines[:7]:
        d.text((92, y), line, font=font, fill=ink + (255,))
        y += line_h
    d.text((92, 586), "—— 小鲸鱼", font=_font(26, True), fill=(90, 105, 135, 255))

    # 角色卡
    d.rounded_rectangle([740, 128, 1032, 656], radius=30,
                        fill=(245, 242, 235, 255), outline=accent + (220,), width=3)
    path = _asset_path(str(tpl.get("character") or ""))
    if path:
        try:
            ch = _contain(_trim_light(Image.open(path)), (270, 400))
            im.alpha_composite(ch.convert("RGBA"), (886 - ch.width // 2, 190))
        except Exception:
            pass
    d.text((886, 592), "DeepSeekChan", font=_font(22, True), fill=(70, 90, 130, 255), anchor="ma")
    d.text((886, 624), "小鲸鱼", font=_font(18), fill=(120, 132, 155, 255), anchor="ma")

    # 边框
    d.rounded_rectangle([20, 20, W - 21, H - 21], radius=26,
                        outline=accent + (90,), width=2)
    return im.convert("RGB")


def _meme(tpl: dict, text: str, source: bytes | None = None) -> Image.Image:
    W = H = 1080
    if source:
        src = Image.open(io.BytesIO(source))
        im = _cover(src, (W, H)).convert("RGBA")
    else:
        im = Image.new("RGBA", (W, H), (247, 243, 234, 255))
        path = _asset_path(str(tpl.get("character") or ""))
        if path:
            try:
                ch = _contain(_trim_light(Image.open(path)), (920, 920))
                im.alpha_composite(ch.convert("RGBA"), ((W - ch.width) // 2, (H - ch.height) // 2))
            except Exception:
                pass
    d = ImageDraw.Draw(im)
    parts = [p.strip() for p in str(text or "").split("|", 1)]
    top = parts[0] if len(parts) > 1 else ""
    bottom = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
    for label, is_top in ((top, True), (bottom, False)):
        if not label:
            continue
        font, lines, line_h = _fit_text(d, label, 940, 230, start=74, min_size=42, bold=True)
        total = len(lines) * line_h
        y = 34 if is_top else H - 34 - total
        for line in lines[:3]:
            _stroke_text(d, (W // 2, y), line, font, (255, 255, 255, 255),
                         (10, 12, 20, 255), width=9, anchor="ma")
            y += line_h
    return im.convert("RGB")


def _achievement(tpl: dict, text: str, source: bytes | None = None) -> Image.Image:
    W, H = 1080, 720
    accent = _hex(tpl.get("accent"), (240, 196, 106))
    im = _gradient((W, H), (16, 26, 52), (34, 32, 58))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([26, 26, W - 27, H - 27], radius=26,
                        outline=accent + (220,), width=4)
    d.text((60, 48), "ACHIEVEMENT", font=_font(20, True), fill=accent + (230,))
    d.text((60, 84), "成就解锁", font=_font(54, True), fill=(248, 246, 240, 255))

    parts = [p.strip() for p in str(text or "").split("|", 1)]
    title = parts[0] or "又完成一件事"
    sub = parts[1] if len(parts) > 1 else "小鲸鱼把它记下来了。"
    font, lines, line_h = _fit_text(d, title, 600, 120, start=44, min_size=28, bold=True)
    y = 220
    for line in lines[:2]:
        d.text((60, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h
    d.text((60, y + 14), sub, font=_font(24), fill=(190, 200, 220, 255))

    # 角色
    path = _asset_path(str(tpl.get("character") or ""))
    if path:
        try:
            ch = _contain(_trim_light(Image.open(path)), (380, 380))
            im.alpha_composite(ch.convert("RGBA"), (720, 180))
        except Exception:
            pass

    # 金色纸屑
    import random as _random
    rnd = _random.Random(7)
    for _ in range(34):
        x, y = rnd.randint(40, W - 40), rnd.randint(60, H - 60)
        r = rnd.choice((3, 4, 5, 7))
        d.rectangle([x, y, x + r, y + r * 2], fill=accent + (rnd.choice((90, 140, 200)),))
    return im.convert("RGB")


def _edit_text(tpl: dict, text: str, source: bytes | None = None,
               options: dict | None = None) -> Image.Image:
    if not source:
        return _quote(tpl, text, source)
    W = H = 1080
    im = _cover(Image.open(io.BytesIO(source)), (W, H)).convert("RGBA")
    options = options or {}
    filt = str(options.get("filter") or "").lower()
    if filt in ("gray", "黑白"):
        im = ImageOps.grayscale(im).convert("RGBA")
    elif filt in ("warm", "暖色"):
        overlay = Image.new("RGBA", (W, H), (255, 180, 80, 28))
        im = Image.alpha_composite(im, overlay)

    # 底部渐变
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H - 360, H):
        a = int(190 * (y - (H - 360)) / 360)
        gd.line([(0, y), (W, y)], fill=(8, 10, 18, a))
    im = Image.alpha_composite(im, grad)
    d = ImageDraw.Draw(im)
    parts = [p.strip() for p in str(text or "").split("|", 1)]
    top = parts[0] if len(parts) > 1 else ""
    bottom = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
    for label, is_top in ((top, True), (bottom, False)):
        if not label:
            continue
        font, lines, line_h = _fit_text(d, label, 920, 260, start=68, min_size=38, bold=True)
        total = len(lines) * line_h
        y = 40 if is_top else H - 60 - total
        for line in lines[:3]:
            _stroke_text(d, (W // 2, y), line, font, (255, 255, 255, 255),
                         (10, 12, 20, 255), width=9, anchor="ma")
            y += line_h
    return im.convert("RGB")


def render(template_id: str = "quote", text: str = "",
           source: bytes | None = None, options: dict | None = None) -> bytes:
    tpl = pick_template(template_id)
    kind = str(tpl.get("kind") or "quote")
    if kind == "meme":
        im = _meme(tpl, text, source)
    elif kind == "achievement":
        im = _achievement(tpl, text, source)
    elif kind == "edit_text":
        im = _edit_text(tpl, text, source, options)
    else:
        im = _quote(tpl, text, source)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()
