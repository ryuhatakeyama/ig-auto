"""content/queue/*.json のスライドを 1080x1350 の JPEG にする。
出力先: docs/img/<日付>/01.jpg ...（GitHub Pages で公開される）"""
import json, sys, html, pathlib, asyncio
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAND = "畠山龍｜建設会社の採用SNS"
OR, INK, PAPER = "#FF5A1F", "#16161A", "#F3F0E8"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&display=swap');
*{{box-sizing:border-box}} body{{margin:0}}
.s{{width:1080px;height:1350px;display:flex;flex-direction:column;font-family:'Noto Sans JP',sans-serif}}
.paper{{background-color:{PAPER};color:{INK};background-image:linear-gradient(rgba(22,22,26,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(22,22,26,.07) 1px,transparent 1px);background-size:54px 54px}}
.ink{{background:{INK};color:{PAPER}}}
.st{{background-image:repeating-linear-gradient(-45deg,{OR} 0 28px,{INK} 28px 56px)}}
.std{{background-image:repeating-linear-gradient(-45deg,{OR} 0 28px,{PAPER} 28px 56px)}}
.hd{{display:flex;justify-content:space-between;padding:52px 72px 0;font-size:26px;font-weight:700;letter-spacing:.04em}}
.bd{{flex-grow:1;display:flex;flex-direction:column;justify-content:center;gap:52px;padding:0 72px}}
h1{{margin:0;font-weight:900;letter-spacing:.02em;line-height:1.32}}
p{{margin:0;line-height:1.6}}
.or{{color:{OR}}} .hl{{background:{OR};color:{INK};padding:0 12px}}
.tag{{align-self:flex-start;background:{OR};color:{INK};font-weight:900;font-size:30px;padding:10px 24px;letter-spacing:.06em}}
.nl{{display:flex;flex-direction:column}}
.nl div{{display:flex;align-items:center;gap:32px;padding:28px 0;border-top:3px solid currentColor}}
.nl div:last-child{{border-bottom:3px solid currentColor}}
.nl b{{font-weight:900;font-size:64px;color:{OR};min-width:110px}} .nl span{{font-size:44px;font-weight:900;line-height:1.4}}
.box{{display:flex;flex-direction:column;gap:20px;background:#fff;color:{INK};border:4px solid {INK};padding:40px 44px}}
.box em{{font-style:normal;align-self:flex-start;background:{INK};color:{PAPER};font-size:30px;font-weight:900;padding:8px 20px}}
.box span{{font-size:44px;font-weight:900;line-height:1.5}}
.ck{{display:flex;flex-direction:column;gap:36px}}
.ck div{{display:flex;align-items:center;gap:28px;font-size:46px;font-weight:900}}
.ck i{{width:64px;height:64px;border:5px solid {PAPER};background:{INK};display:flex;align-items:center;justify-content:center}}
.mini{{font-size:29px;font-weight:700;line-height:1.6;padding:24px 32px;border:3px solid currentColor}}
"""
CHECK = f'<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="{OR}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12l5 5L20 6"/></svg>'

def t(s):
    """改行は「\\n」、強調は [[オレンジ文字]] と {{オレンジ背景}}"""
    s = html.escape(s).replace("\n", "<br>")
    s = s.replace("[[", '<span class="or">').replace("]]", "</span>")
    s = s.replace("{{", '<span class="hl">').replace("}}", "</span>")
    return s

def body(sl):
    k = sl["type"]
    if k == "cover":
        return f'<h1 style="font-size:{sl.get("size",110)}px">{t(sl["title"])}</h1><p style="font-size:46px;font-weight:900">{t(sl.get("sub",""))}</p>'
    if k == "list":
        rows = "".join(f"<div><b>{i:02d}</b><span>{t(x)}</span></div>" for i, x in enumerate(sl["items"], 1))
        return f'<div class="tag">{t(sl.get("tag",""))}</div><h1 style="font-size:{sl.get("size",84)}px">{t(sl["title"])}</h1><div class="nl">{rows}</div>'
    if k == "point":
        return (f'<div class="tag">{t(sl["tag"])}</div><h1 style="font-size:{sl.get("size",84)}px">{t(sl["title"])}</h1>'
                f'<p style="font-size:42px;font-weight:700">{t(sl["why"])}</p>'
                f'<div class="box"><em>{t(sl.get("label","対策"))}</em><span>{t(sl["how"])}</span></div>')
    if k == "big":
        return (f'<div class="tag">{t(sl.get("tag",""))}</div><p style="font-size:44px;font-weight:700">{t(sl.get("pre",""))}</p>'
                f'<h1 style="font-size:{sl.get("size",100)}px">{t(sl["title"])}</h1><p style="font-size:44px;font-weight:700">{t(sl.get("post",""))}</p>')
    if k == "summary":
        cks = "".join(f"<div><i>{CHECK}</i>{t(x)}</div>" for x in sl.get("checks", []))
        cta = sl.get("cta", "保存して見返してください。\n自社のアカウントの診断はDMで「診断」と送ってください。")
        return f'<div class="tag">{t(sl.get("tag","まとめ"))}</div><h1 style="font-size:{sl.get("size",84)}px">{t(sl["title"])}</h1><div class="ck">{cks}</div><p class="mini">{t(cta)}</p>'
    raise ValueError(k)

DARK = {"cover", "summary"}
def page(sl, n, total):
    dark = sl.get("dark", sl["type"] in DARK)
    top = '<div class="std" style="height:28px"></div>' if dark else ""
    bot = "std" if dark else "st"
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="s {"ink" if dark else "paper"}">{top}<div class="hd"><span>{BRAND}</span><span>{n:02d} / {total:02d}</span></div>'
            f'<div class="bd">{body(sl)}</div><div class="{bot}" style="height:44px"></div></div></body></html>')

async def render(paths):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(**({"executable_path": sys.argv[-1]} if sys.argv[-1].endswith("chrome") else {}))
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for f in paths:
            post = json.loads(f.read_text())
            out = ROOT / "docs" / "img" / post["date"]; out.mkdir(parents=True, exist_ok=True)
            n = len(post["slides"])
            for i, sl in enumerate(post["slides"], 1):
                await pg.set_content(page(sl, i, n), wait_until="networkidle")
                await pg.evaluate("document.fonts.ready")
                over = await pg.evaluate("document.querySelector('.bd').scrollHeight > document.querySelector('.bd').clientHeight + 2 || [...document.querySelectorAll('.bd *')].some(e=>e.scrollWidth>e.clientWidth+2)")
                if over: print(f"⚠ はみ出し: {post['date']} {i}枚目")
                await pg.screenshot(path=str(out / f"{i:02d}.jpg"), type="jpeg", quality=92)
            print("rendered", post["date"], n)
        await b.close()

if __name__ == "__main__":
    files = sorted((ROOT / "content" / "queue").glob("*.json"))
    asyncio.run(render(files))
