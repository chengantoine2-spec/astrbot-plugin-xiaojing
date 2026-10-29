# -*- coding: utf-8 -*-
"""小鲸日报（焦糖主题版）：日期/倒计时/黄历/民生/世界/IT/微博/B站/音乐 → PNG。"""

from __future__ import annotations

import asyncio
import base64
import html
import json
import os
import random
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
T2I = "https://t2i.soulter.top/text2img"
NEWSNOW = "https://newsnow.busiyi.world/api/s?id="
WINDIR = os.environ.get("WINDIR", r"C:\Windows")
FONT_PATH = str(Path(WINDIR) / "Fonts" / "msyh.ttc")
FONT_BOLD = str(Path(WINDIR) / "Fonts" / "msyhbd.ttc")
WHALE_BG = Path(__file__).resolve().parent / "data" / "assets" / "whale_bg.webp"

TZ = timezone(timedelta(hours=8))

QUOTES = (
    "把日子过成自己的节奏，慢一点也没关系。",
    "先把手边的事做好，远方自然会亮。",
    "风会记得一朵花的香。",
    "认真吃饭，好好睡觉，就是了不起的修行。",
    "不必急着抵达，路上的光也算数。",
    "心里有海的人，走到哪里都不算远。",
    "今天也要给自己留一点空白。",
    "生活不是赶路，是感受路。",
    "把复杂的事拆小，把普通的日子过厚。",
    "允许自己偶尔什么都不做。",
    "所有微小的坚持，都会在某天回响。",
    "太阳每天都是新的，烦恼也是可以过期的。",
    "与其等风来，不如追风去。",
    "把喜欢的事做久一点，就会变成光。",
    "世界很吵，记得听自己的声音。",
    "慢慢来，比较快。",
    "愿你今天遇到的风，都是温柔的。",
    "一日三餐，四季流转，皆是答案。",
    "不慌不忙，自有方向。",
    "把今天过好，就是对明天最好的准备。",
    "山川湖海，来日方长。",
    "心里种花，人生才不会荒芜。",
    "别急，好的东西都在路上。",
    "把每一件小事做完，日子就有了形状。",
    "生活给的糖，常常藏在细节里。",
    "看清生活的真相，依然热爱它。",
    "与其仰望，不如点亮自己。",
    "日子是自己的，不必活成别人的注脚。",
    "安静地努力，热烈地生活。",
    "愿你所行皆坦途，所遇皆温柔。",
)

TIPS_PATH = Path(__file__).resolve().parent / "data" / "report_tips.json"


def pick_tip(default: str = "") -> str:
    """随机一句，避开最近 10 条，避免每天重复。"""
    try:
        used = json.loads(TIPS_PATH.read_text(encoding="utf-8"))
    except Exception:
        used = []
    pool = [q for q in QUOTES if q not in used[-10:]]
    if default and default not in used[-10:]:
        pool.append(default)
    tip = random.choice(pool or list(QUOTES))
    try:
        TIPS_PATH.parent.mkdir(parents=True, exist_ok=True)
        TIPS_PATH.write_text(json.dumps((used + [tip])[-40:], ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return tip

_whale_cache: str | None = None


def whale_data_uri() -> str:
    """鲸鱼娘立绘转 data URI（原有配色，只做整体透明度处理）。"""
    global _whale_cache
    if _whale_cache is not None:
        return _whale_cache
    try:
        _whale_cache = "data:image/webp;base64," + base64.b64encode(WHALE_BG.read_bytes()).decode()
    except Exception:
        _whale_cache = ""
    return _whale_cache


async def _json(url: str, timeout: int = 15, headers: dict | None = None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as s:
            async with s.get(url, headers=h) as r:
                if r.status != 200:
                    return None
                return await r.json(content_type=None)
    except Exception:
        return None


async def _text(url: str, timeout: int = 15) -> str:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as s:
            async with s.get(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}) as r:
                return await r.text(errors="ignore") if r.status == 200 else ""
    except Exception:
        return ""


async def fetch_sixty() -> dict:
    j = await _json("https://60s.viki.moe/v2/60s")
    d = (j or {}).get("data") or {}
    return {
        "news": [str(x).strip() for x in d.get("news") or []],
        "tip": str(d.get("tip") or "").strip(),
    }


async def fetch_quote() -> str:
    """每日一句：一言接口，每次实时随机。"""
    j = await _json(f"https://v1.hitokoto.cn/?c=d&c=i&c=k&encode=json&_={random.random()}", timeout=12)
    if isinstance(j, dict):
        text = str(j.get("hitokoto") or "").strip()
        src = str(j.get("from") or "").strip()
        if text:
            return text + (f"——《{src}》" if src else "")
    return ""


async def fetch_newsnow(sid: str, n: int = 6) -> list[str]:
    j = await _json(NEWSNOW + sid)
    items = (j or {}).get("items") or []
    return [str(x.get("title") or "").strip() for x in items[:n] if x.get("title")]


async def fetch_weibo(n: int = 6) -> list[str]:
    j = await _json("https://60s.viki.moe/v2/weibo")
    items = (j or {}).get("data") or []
    return [str(x.get("title") or "").strip() for x in items[:n] if x.get("title")]


async def _song_detail(s: dict) -> dict:
    sid = s.get("id")
    info = {
        "name": s.get("name"),
        "artists": "、".join(a.get("name", "") for a in (s.get("artists") or [])[:2]),
        "id": sid,
        "cover": "",
        "lyric": "",
        "comment": "",
    }
    ref = {"Referer": "https://music.163.com/"}
    d = await _json(f"https://music.163.com/api/song/detail?ids=[{sid}]", headers=ref)
    try:
        info["cover"] = ((((d or {}).get("songs") or [{}])[0].get("album") or {}).get("picUrl")) or ""
    except Exception:
        pass
    l = await _json(f"https://music.163.com/api/song/lyric?id={sid}&lv=1&kv=1&tv=-1", headers=ref)
    try:
        lrc = ((l or {}).get("lrc") or {}).get("lyric") or ""
        skip = ("作词", "作曲", "编曲", "制作", "混音", "吉他", "和声", "录音", "监制")
        lines = [re.sub(r"\[.*?\]", "", x).strip() for x in lrc.splitlines()]
        lines = [x for x in lines if x and not any(k in x for k in skip)]
        info["lyric"] = lines[0] if lines else ""
    except Exception:
        pass
    if not info["lyric"]:
        c = await _json(
            f"https://music.163.com/api/v1/resource/comments/R_SO_4_{sid}?limit=8&offset=0",
            headers=ref,
        )
        cmts = (c or {}).get("hotComments") or (c or {}).get("comments") or []
        bad_kw = ("版权", "求", "咋", "？", "?", "假", "盗")
        cands = [
            x
            for x in cmts
            if len(str(x.get("content") or "").strip()) >= 6
            and not any(k in str(x.get("content") or "") for k in bad_kw)
        ]
        if cands:
            info["comment"] = str(cands[0].get("content") or "").strip().replace("\n", " ")
    return info


async def fetch_music(keyword: str) -> dict:
    j = await _json(
        "https://music.163.com/api/search/get/web?s=" + keyword.replace(" ", "%20") + "&type=1&limit=8",
        headers={"Referer": "https://music.163.com/"},
    )
    songs = ((j or {}).get("result") or {}).get("songs") or []
    if not songs:
        return {}
    kw = [w for w in keyword.split() if w]

    def score(x):
        title = x.get("name") or ""
        artists = " ".join(a.get("name", "") for a in (x.get("artists") or []))
        th = sum(1 for w in kw if w in title)
        ah = sum(1 for w in kw if w in artists)
        bad = 4 if any(k in title for k in ("原唱", "翻唱", "cover", "Cover", "伴奏", "DJ", "女声", "钢琴", "版")) else 0
        return th + 3 * ah - bad + (1 if len(title) <= 6 else 0)

    best: dict = {}
    for s in sorted(songs, key=score, reverse=True)[:3]:
        info = await _song_detail(s)
        artists = info.get("artists") or ""
        title = info.get("name") or ""
        info["cover_note"] = "" if all(w in artists or w in title for w in kw) else "翻唱"
        if not best:
            best = info
        if info.get("lyric"):
            return info
    return best


def load_age_days() -> int:
    try:
        cfg = json.loads((Path(__file__).resolve().parent / "data" / "config.json").read_text(encoding="utf-8"))
        y, m, d = [int(x) for x in str(cfg.get("birthday") or "2026-10-27").split("-")]
        return max(0, (datetime.now(TZ).date() - date(y, m, d)).days)
    except Exception:
        return 0


def load_diary() -> str:
    """取最近一篇日记的最后一段，作为日报里的一句话。"""
    d = Path(__file__).resolve().parent / "data" / "diary"
    try:
        files = sorted(d.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        return ""
    for fp in files[:2]:
        try:
            txt = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        blocks = [b.strip() for b in txt.split("## ") if b.strip()]
        if not blocks:
            continue
        body = blocks[-1]
        body = re.sub(r"^\d{2}:\d{2}\s*", "", body)
        body = " ".join(line.strip() for line in body.splitlines() if line.strip())
        if body:
            return body[:180]
    return ""


def almanac_info() -> dict:
    """农历、宜忌、下一个节气。"""
    out = {"lunar": "", "yi": [], "ji": [], "jieqi": "", "jieqi_date": "", "jieqi_days": 0}
    try:
        from lunar_python import Solar

        today = datetime.now(TZ)
        solar = Solar.fromYmd(today.year, today.month, today.day)
        lunar = solar.getLunar()
        out["lunar"] = "农历" + lunar.getMonthInChinese() + "月" + lunar.getDayInChinese()
        out["yi"] = [x for x in (lunar.getDayYi() or []) if x][:6]
        out["ji"] = [x for x in (lunar.getDayJi() or []) if x][:6]
        nj = lunar.getNextJieQi()
        if nj:
            out["jieqi"] = nj.getName()
            d = nj.getSolar()
            out["jieqi_date"] = f"{d.getYear()}-{d.getMonth():02d}-{d.getDay():02d}"
            out["jieqi_days"] = (date(d.getYear(), d.getMonth(), d.getDay()) - today.date()).days
    except Exception:
        pass
    return out


async def next_holiday() -> dict:
    out = {"name": "", "date": "", "days": 0}
    today = datetime.now(TZ).date()
    cands = []
    for y in (today.year, today.year + 1):
        j = await _json(f"https://timor.tech/api/holiday/year/{y}")
        holiday = (j or {}).get("holiday") or {}
        for _, v in holiday.items():
            if not isinstance(v, dict) or not v.get("holiday"):
                continue
            name = str(v.get("name") or "")
            d = str(v.get("date") or "")
            if not name or not d or name in ("周末",):
                continue
            try:
                dd = date.fromisoformat(d)
            except Exception:
                continue
            if dd >= today:
                cands.append((dd, name, d))
        if cands:
            break
    if not cands:
        nm = date(today.year + 1, 1, 1)
        cands.append((nm, "元旦", nm.isoformat()))
    cands.sort()
    dd, name, d = cands[0]
    out.update({"name": name, "date": d, "days": (dd - today).days})
    return out


def weekend_days() -> int:
    today = datetime.now(TZ).date()
    return (5 - today.weekday()) % 7


def _esc(s) -> str:
    return html.escape(str(s or ""))


def _items_html(items: list[str], limit: int = 6) -> str:
    if not items:
        return '<div class="muted">暂时没有内容。</div>'
    return "".join(
        f'<li><span class="idx">{i+1:02d}</span><span>{_esc(x)}</span></li>' for i, x in enumerate(items[:limit])
    )


def render_html(data: dict) -> str:
    now = datetime.now(TZ)
    weekday = "一二三四五六日"[now.weekday()]
    a = data["almanac"]
    hol = data["holiday"]
    yi = "".join(f'<span class="tag ok">{_esc(x)}</span>' for x in a["yi"]) or '<span class="muted">—</span>'
    ji = "".join(f'<span class="tag no">{_esc(x)}</span>' for x in a["ji"]) or '<span class="muted">—</span>'

    diary = str(data.get("diary") or "").strip()
    diary_block = (
        f'<section class="card diary"><h2><i>🐋</i>小鲸的日记</h2>'
        f'<div class="diarytext">{_esc(diary)}</div></section>'
        if diary else ""
    )
    up = "".join(
        f'<div class="row"><b>{_esc(k)}</b><span class="ver">{_esc(v)}</span></div>' for k, v in data["updates"]
    )
    up_block = (
        f'<section class="card"><h2><i>🐋</i>我自己的动态</h2>{up}</section>' if up else ""
    )

    hol_txt = f'{_esc(hol["name"])} · {hol["days"]} 天后' if hol["name"] else "暂无数据"
    hol_sub = _esc(hol["date"]) if hol["date"] else ""
    jq_txt = f'{_esc(a["jieqi"])} · {a["jieqi_days"]} 天后' if a["jieqi"] else "暂无数据"
    jq_sub = _esc(a["jieqi_date"])
    tip = str(data.get("tip") or "").strip()
    tip_block = f'<div class="tip">🌤 {_esc(tip)}</div>' if tip else ""
    bg = whale_data_uri()
    bg_html = f'<img class="bgchar" src="{bg}">' if bg else ""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}
body{{margin:0;width:1080px;color:#4a2f16;font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;
background:linear-gradient(180deg,#fdf6e8 0%,#f8e8cc 45%,#f3dcb6 100%);}}
.page{{position:relative;overflow:hidden;width:1080px}}
.bgchar{{position:absolute;right:-56px;bottom:-30px;height:3040px;opacity:.34;z-index:0;pointer-events:none}}
.wrap{{position:relative;z-index:1;padding:60px 56px 44px}}
.top{{display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2px solid #e2bd8d;padding-bottom:24px}}
h1{{margin:0;font-size:62px;letter-spacing:2px;font-weight:800;color:#8a4a12}}
.sub{{margin-top:8px;color:#a57a4d;font-size:25px}}
.pill{{padding:10px 24px;border-radius:999px;font-size:24px;color:#fff8ec;background:linear-gradient(135deg,#d08a3e,#a95f1c);font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:26px 0 6px}}
.mini{{background:rgba(255,250,240,.80);border:1px solid #e8c99b;border-radius:20px;padding:20px 18px;box-shadow:0 10px 24px rgba(150,100,50,.10)}}
.mini .k{{font-size:21px;color:#a57a4d}}
.mini .v{{font-size:30px;font-weight:800;color:#8a4a12;margin-top:8px}}
.mini .s{{font-size:20px;color:#b08a60;margin-top:6px}}
.card{{background:rgba(255,250,240,.80);border:1px solid #e8c99b;border-radius:22px;padding:26px 28px;margin:20px 0;box-shadow:0 12px 30px rgba(150,100,50,.10)}}
h2{{margin:0 0 16px;font-size:29px;display:flex;align-items:center;gap:12px;color:#8a4a12}}
h2 i{{font-style:normal;font-size:26px}}
ul{{list-style:none;margin:0;padding:0}}
li{{display:flex;gap:14px;font-size:25px;line-height:1.6;margin:12px 0;color:#54351c}}
.idx{{flex:0 0 50px;height:32px;border-radius:9px;background:#f5dcb8;color:#a95f1c;
font-size:19px;display:flex;align-items:center;justify-content:center;font-weight:800;margin-top:6px}}
.row{{display:flex;justify-content:space-between;gap:16px;font-size:24px;padding:9px 0;border-bottom:1px dashed #ecd3ad}}
.row:last-child{{border-bottom:none}}
.ver{{color:#b06a24;font-size:21px}}
.tag{{display:inline-block;padding:6px 14px;border-radius:999px;font-size:21px;margin:0 8px 8px 0}}
.ok{{background:#eaf3e2;color:#4f6b32;border:1px solid #cfdfba}}
.no{{background:#fbe6e0;color:#9a4a35;border:1px solid #efc9bd}}
.muted{{color:#b08a60;font-size:22px}}
.diarytext{{font-size:23px;line-height:1.7;color:#6b4423}}
.foot{{margin-top:30px;color:#a8784a;font-size:20px;text-align:center;background:rgba(253,246,232,.72);border-radius:12px;padding:10px 14px}}
.tip{{background:#f7e3c0;border-left:6px solid #c9853c;border-radius:14px;padding:16px 20px;
font-size:23px;color:#7a4a1d;margin:16px 0 4px;line-height:1.5}}
</style></head><body><div class="page">
{bg_html}
<div class="wrap">
<div class="top"><div><h1>小鲸日报</h1>
<div class="sub">{now.strftime('%Y-%m-%d')} 周{weekday} · {data['period']} · 出报 {now.strftime('%H:%M')} · {_esc(a['lunar'])} · 出生第 {data.get('age_days', 0)} 天</div></div>
<div class="pill">{_esc(data['period'])}</div></div>

<div class="grid">
  <div class="mini"><div class="k">距周末</div><div class="v">{data['weekend']} 天</div><div class="s">周六见</div></div>
  <div class="mini"><div class="k">下一个假期</div><div class="v">{hol_txt}</div><div class="s">{hol_sub}</div></div>
  <div class="mini"><div class="k">下一个节气</div><div class="v">{jq_txt}</div><div class="s">{jq_sub}</div></div>
</div>
{tip_block}

<section class="card"><h2><i>📅</i>今日黄历</h2>
<div style="font-size:22px;color:#a57a4d;margin-bottom:10px">宜</div>{yi}
<div style="font-size:22px;color:#a57a4d;margin:14px 0 10px">忌</div>{ji}</section>

<section class="card"><h2><i>🏙</i>国内民生</h2><ul>{_items_html(data['civic'])}</ul></section>
<section class="card"><h2><i>🌍</i>世界大新闻</h2><ul>{_items_html(data['world'])}</ul></section>
<section class="card"><h2><i>💻</i>IT 新闻</h2><ul>{_items_html(data['it'])}</ul></section>
<section class="card"><h2><i>🔥</i>微博热点</h2><ul>{_items_html(data['weibo'])}</ul></section>
<section class="card"><h2><i>📺</i>B站热点</h2><ul>{_items_html(data['bili'])}</ul></section>
{diary_block}
{up_block}
<div class="foot">由小鲸整理 · 60s / 参考消息 / IT之家 / 微博 / B站 / 网易云</div>
</div></div></body></html>"""


async def _render(tmpl: str, out: Path) -> bool:
    payload = {"tmpl": tmpl, "json": True, "tmpldata": {},
               "options": {"full_page": True, "type": "png", "quality": 92}}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=90)) as s:
            async with s.post(f"{T2I}/generate", json=payload) as r:
                if r.status != 200:
                    return False
                j = await r.json(content_type=None)
            rid = ((j or {}).get("data") or {}).get("id")
            if not rid:
                return False
            async with s.get(f"{T2I}/{rid}") as ir:
                if ir.status != 200:
                    return False
                out.write_bytes(await ir.read())
        return out.stat().st_size > 5000
    except Exception:
        return False


def _pil_fallback(data: dict, out: Path) -> None:
    W, H = 1080, 2100
    img = Image.new("RGB", (W, H), (253, 246, 232))
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(FONT_BOLD, 56)
    fh = ImageFont.truetype(FONT_BOLD, 34)
    f = ImageFont.truetype(FONT_PATH, 28)
    d.text((56, 70), "小鲸日报", font=fb, fill=(138, 74, 18))
    d.text((56, 140), f"{datetime.now(TZ).strftime('%Y-%m-%d')} · {data['period']}", font=f, fill=(165, 122, 77))
    y = 210
    for title, key in (("国内民生", "civic"), ("世界大新闻", "world"), ("IT 新闻", "it")):
        d.text((56, y), title, font=fh, fill=(138, 74, 18)); y += 56
        for item in data[key][:5]:
            for i in range(0, min(len(item), 100), 30):
                d.text((70, y), item[i:i + 30], font=f, fill=(84, 53, 28)); y += 38
            y += 6
        y += 24
    img.save(out, "PNG")


async def build_daily_png(out_dir: Path, period: str = "早报") -> Path:
    sixty, world, it, weibo, bili, hol, quote = await asyncio.gather(
        fetch_sixty(),
        fetch_newsnow("cankaoxiaoxi"),
        fetch_newsnow("ithome"),
        fetch_weibo(),
        fetch_newsnow("bilibili"),
        next_holiday(),
        fetch_quote(),
    )
    civic = sixty.get("news") or []
    updates = []
    for name, repo in (("DeepSeek", "deepseek-ai/DeepSeek-V3"), ("AstrBot", "AstrBotDevs/AstrBot")):
        j = await _json(f"https://api.github.com/repos/{repo}/releases?per_page=1", timeout=12)
        if isinstance(j, list) and j:
            tag = j[0].get("tag_name") or ""
            when = (j[0].get("published_at") or "")[:10]
            if not (tag.startswith("v1.0.0") or (when and when < "2025-10-01")):
                updates.append((name, f"{tag} · {when}"))
                continue
        c = await _json(f"https://api.github.com/repos/{repo}/commits?per_page=1", timeout=12)
        if isinstance(c, list) and c:
            when = (((c[0].get("commit") or {}).get("author") or {}).get("date") or "")[:10]
            fresh = (datetime.now(TZ).date() - timedelta(days=90)).isoformat()
            if when and when >= fresh:
                updates.append((name, f"最近提交 · {when}"))

    data = {
        "period": period,
        "tip": quote or str(sixty.get("tip") or ""),
        "civic": civic[:5],
        "world": world[:5],
        "it": it[:5],
        "weibo": weibo[:5],
        "bili": bili[:5],
        "holiday": hol,
        "almanac": almanac_info(),
        "weekend": weekend_days(),
        "diary": load_diary(),
        "age_days": load_age_days(),
        "updates": updates,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(TZ)
    fp = out_dir / f"daily_{now.strftime('%Y%m%d_%H%M')}_{'am' if period == '早报' else 'pm'}.png"
    tmpl = render_html(data)
    for attempt in range(3):
        if await _render(tmpl, fp):
            return fp
        await asyncio.sleep(2)
    _pil_fallback(data, fp)
    return fp
