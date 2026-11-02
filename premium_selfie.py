# -*- coding: utf-8 -*-
"""精致自拍：把素材库里的场景/立绘裁成 3:4，叠加时间和活动。

不做生成式绘图，只做高质量排版；素材来源见 data/assets/library.json。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

W, H = 1080, 1440
FONT_DIR = Path(r"C:\Windows\Fonts")


def _font(size: int, bold: bool = False):
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    try:
        return ImageFont.truetype(str(FONT_DIR / name), int(size))
    except Exception:
        return ImageFont.load_default()


def _cover(im: Image.Image, size=(W, H)) -> Image.Image:
    im = im.convert("RGB")
    scale = max(size[0] / im.width, size[1] / im.height)
    nw, nh = max(size[0], int(im.width * scale + 1)), max(size[1], int(im.height * scale + 1))
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - size[0]) // 2
    top = (nh - size[1]) // 2
    return im.crop((left, top, left + size[0], top + size[1]))


def render_premium_selfie(activity: str, mood: str, asset_path: str | Path,
                          output_path: str | Path, now: str = "") -> Path:
    src = Path(asset_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    im = _cover(Image.open(src))
    im = ImageEnhance.Color(im).enhance(1.04)
    im = ImageEnhance.Contrast(im).enhance(1.02)
    im = im.convert("RGBA")

    # 顶部与底部渐变，保证文字可读
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(0, 180):
        a = int(120 * (1 - y / 180))
        od.line([(0, y), (W, y)], fill=(8, 12, 24, a))
    for y in range(930, H):
        a = int(190 * (y - 930) / (H - 930))
        od.line([(0, y), (W, y)], fill=(8, 12, 24, a))
    im = Image.alpha_composite(im, overlay)
    d = ImageDraw.Draw(im)

    # 顶部信息底衬，保证浅色场景也能读清
    d.rounded_rectangle([34, 24, 330, 108], radius=16, fill=(8, 12, 24, 150))
    d.rounded_rectangle([W - 132, 26, W - 34, 82], radius=14, fill=(8, 12, 24, 140))

    # 顶部信息
    d.text((48, 34), "小鲸的房间", font=_font(30, True), fill=(242, 246, 255))
    d.text((48, 76), "SELFIE", font=_font(17, True), fill=(150, 200, 255))
    if now:
        d.text((W - 48, 40), now, font=_font(26), fill=(232, 240, 252), anchor="ra")

    # 底部活动与心情
    d.rectangle([48, 1288, 128, 1294], fill=(110, 170, 255))
    d.text((48, 1310), f"在{activity}", font=_font(46, True), fill=(246, 249, 255))
    if mood:
        d.text((50, 1372), f"心情：{mood}", font=_font(22), fill=(188, 204, 230))

    # 轻微暗角
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(26):
        a = 3 + i // 4
        vd.rectangle([i, i, W - i, H - i], outline=(6, 10, 20, a))
    im = Image.alpha_composite(im, vig)

    im.convert("RGB").save(out, "PNG")
    return out
