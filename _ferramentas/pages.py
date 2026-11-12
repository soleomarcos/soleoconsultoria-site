#!/usr/bin/env python3
"""Capas e cards com imagem + pendências de contraste/toque nas páginas internas.
Uso: python3 pages.py <raiz-do-repo> <pasta-das-capas>
Idempotente (marcador id="cards-img").
"""

import re
import shutil
import sys
from pathlib import Path

ROOT, CAPAS = Path(sys.argv[1]), Path(sys.argv[2])
SITE = "https://www.soleoconsultoria.com.br"
IMG = "/img/capas"

# --- copia as capas para o repo
dst = ROOT / IMG.strip("/")
dst.mkdir(parents=True, exist_ok=True)
for f in CAPAS.iterdir():
    if f.suffix in (".webp", ".jpg"):
        shutil.copy(f, dst / f.name)
ALT = dict(l.split("\t", 1) for l in (CAPAS / "alts.tsv").read_text().splitlines())

CAT_CLASS = {
    "Reforma Tributária": "rt",
    "Preço e margem": "preco",
    "Contratos": "contratos",
    "Crédito": "credito",
    "Consultoria": "consult",
}
CAT_L10N = {
    "en": {
        "Reforma Tributária": "Tax reform",
        "Preço e margem": "Pricing",
        "Contratos": "Contracts",
        "Crédito": "Credit",
        "Consultoria": "Consulting",
    },
    "es": {
        "Reforma Tributária": "Reforma tributaria",
        "Preço e margem": "Precios",
        "Contratos": "Contratos",
        "Crédito": "Crédito",
        "Consultoria": "Consultoría",
    },
}
READ = {
    "pt-BR": "Ler guia",
    "pt-PT": "Ler guia",
    "en": "Read guide (in Portuguese)",
    "es": "Leer guía (en portugués)",
}
MIN = {
    "pt-BR": "min de leitura",
    "pt-PT": "min de leitura",
    "en": "min read",
    "es": "min de lectura",
}
TOOLS = {  # slug do caminho -> (capa, chave de rótulo)
    "simulador-cbs-ibs": ("simulador", "tool"),
    "cbs-ibs-simulator": ("simulador", "tool"),
    "glossario-reforma-tributaria": ("glossario", "gloss"),
    "brazil-tax-reform-consulting": ("servico", "svc"),
    "consultoria-reforma-tributaria-brasil": ("servico", "svc"),
}
TOOL_LBL = {
    "pt-BR": {"tool": "Ferramenta", "gloss": "Glossário", "svc": "Serviço"},
    "pt-PT": {"tool": "Ferramenta", "gloss": "Glossário", "svc": "Serviço"},
    "en": {"tool": "Tool", "gloss": "Glossary", "svc": "Service"},
    "es": {"tool": "Herramienta", "gloss": "Glosario", "svc": "Servicio"},
}
OPEN = {"pt-BR": "Abrir", "pt-PT": "Abrir", "en": "Open", "es": "Abrir"}


def img(slug, alt="", eager=False, sizes="(max-width:700px) 100vw, 380px"):
    load = (
        'fetchpriority="high" decoding="async"'
        if eager
        else 'loading="lazy" decoding="async"'
    )
    return (
        f'<img src="{IMG}/{slug}-640.webp" srcset="{IMG}/{slug}-640.webp 640w, {IMG}/{slug}.webp 1200w" '
        f'sizes="{sizes}" width="1200" height="630" alt="{alt}" {load}>'
    )


# --- dados dos artigos a partir do índice e de cada artigo
idx = (ROOT / "artigos/index.html").read_text(encoding="utf-8")
src_idx = idx if 'id="cards-img"' not in idx else __import__("subprocess").run(["git","-C",str(ROOT),"show","6e9898d:artigos/index.html"],capture_output=True,text=True,check=True).stdout
ART = {}
for href, title, cat, desc in re.findall(
    r'<a class="card" href="([^"]+)"><b>(.*?)</b><span>(.*?) · (.*?)</span></a>', src_idx
):
    slug = href.rstrip("/").split("/")[-1]
    page = (ROOT / f"artigos/{slug}/index.html").read_text(encoding="utf-8")
    mins = re.search(r"(\d+) min de leitura", page).group(1)
    ART[slug] = dict(href=href, title=title, cat=cat, desc=desc, mins=mins)
assert len(ART) == 13, len(ART)

SUB_CSS = """
<style id="cards-img">
:root{--wa:#1a7a43}
.btn{border-radius:4px;transition:background .2s}.btn:hover{background:#15693a}
.lead,.cta,.faq details,.card{border-radius:6px}
header.top nav a{display:inline-block;padding:10px 0}
.crumbs a,.meta a{display:inline-block;padding:10px 0}
footer a{display:inline-block;padding:10px 2px}
.cover{margin:4px 0 24px}.cover img{display:block;width:100%;height:auto;aspect-ratio:1200/630;border-radius:6px;background:#0b1d40;box-shadow:0 18px 40px rgba(11,29,64,.18)}
.card.ci{padding:0;overflow:hidden;display:flex;flex-direction:column;transition:transform .2s ease,box-shadow .2s ease,border-color .2s}
.card.ci:hover{transform:translateY(-4px);box-shadow:0 16px 34px rgba(11,29,64,.16);border-color:var(--gold)}
.card.ci img{display:block;width:100%;height:auto;aspect-ratio:1200/630;object-fit:cover;background:#0b1d40}
.card.ci .ct{display:flex;flex-direction:column;gap:8px;padding:16px 18px 18px;flex:1}
.card.ci b,.card.ci h2{display:block;margin:0;font-family:"Playfair Display",Georgia,serif;font-weight:600;font-size:20px;line-height:1.3;color:var(--navy)}
.card.ci .desc{font-size:15px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card.ci .rtime{margin-top:auto;font-size:14px;font-weight:700;color:var(--gold-deep)}
.card .chip{align-self:flex-start;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:4px 10px;border-radius:999px;background:#e6ecf7;color:#0b1d40}
.card .chip.preco{background:#dcf1ec;color:#0f3b3d}.card .chip.contratos{background:#f6e1e8;color:#6b2740}.card .chip.credito{background:#dff1e6;color:#1d5e40}.card .chip.consult{background:#ebe8fb;color:#3d3480}.card .chip.tool{background:#f4ead6;color:#6b5122}
main.idx{max-width:1140px}
body:has(main.idx) header.top .in{max-width:1100px}
.idx .cards{grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
.idx .cards .card.ci:first-child{grid-column:1/-1;flex-direction:row}
.idx .cards .card.ci:first-child img{width:58%;flex:none}
.idx .cards .card.ci:first-child .ct{justify-content:center;padding:28px 32px}
.idx .cards .card.ci:first-child h2{font-size:30px}
.idx .cards .card.ci:first-child .desc{font-size:17px;-webkit-line-clamp:4}
.rel .cards{grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:10px}
.rel .card.ci b{font-size:17px}
@media(max-width:900px){.idx .cards{grid-template-columns:repeat(2,minmax(0,1fr))}.idx .cards .card.ci:first-child{flex-direction:column}.idx .cards .card.ci:first-child img{width:100%}.idx .cards .card.ci:first-child h2{font-size:24px}.idx .cards .card.ci:first-child .ct{padding:16px 18px 18px}}
@media(max-width:620px){.idx .cards,.rel .cards{grid-template-columns:1fr}header.top .in{gap:6px}header.top nav{display:flex;gap:18px;width:100%;overflow-x:auto;white-space:nowrap;scrollbar-width:none}header.top nav a{margin-left:0;font-size:15px}header.top nav a:first-child{display:none}}
</style>
"""

HOME_CSS = """
<style id="gcards">
.gcards{list-style:none;margin:28px 0 0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
.gcards a{display:flex;flex-direction:column;height:100%;background:#fff;border:1px solid rgba(148,163,184,.35);border-radius:6px;overflow:hidden;text-decoration:none;color:inherit;transition:transform .2s ease,box-shadow .2s ease,border-color .2s}
.gcards a:hover{transform:translateY(-4px);box-shadow:0 16px 34px rgba(11,29,64,.16);border-color:var(--gold)}
.gcards img{display:block;width:100%;height:auto;aspect-ratio:1200/630;object-fit:cover;background:var(--navy)}
.gcards .ct{display:flex;flex-direction:column;gap:9px;padding:16px 18px 18px;flex:1}
.gcards b{font-family:"Playfair Display",Georgia,serif;font-weight:500;font-size:21px;line-height:1.28;color:var(--navy)}
.gcards .rtime{margin-top:auto;font-size:14px;font-weight:700;color:var(--gold-deep)}
.gcards .chip{align-self:flex-start;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:4px 10px;border-radius:999px;background:#e6ecf7;color:#0b1d40}
.gcards .chip.preco{background:#dcf1ec;color:#0f3b3d}.gcards .chip.contratos{background:#f6e1e8;color:#6b2740}.gcards .chip.credito{background:#dff1e6;color:#1d5e40}.gcards .chip.consult{background:#ebe8fb;color:#3d3480}.gcards .chip.tool{background:#f4ead6;color:#6b5122}
.gcards li:first-child{grid-column:span 2}
.gcards li:first-child a{flex-direction:row}
.gcards li:first-child img{width:56%;flex:none}
.gcards li:first-child .ct{justify-content:center;padding:26px 30px}
.gcards li:first-child b{font-size:30px}
@media(max-width:980px){.gcards{grid-template-columns:repeat(2,minmax(0,1fr))}.gcards li:first-child{grid-column:1/-1}}
@media(max-width:620px){.gcards{grid-template-columns:1fr}.gcards li:first-child a{flex-direction:column}.gcards li:first-child img{width:100%}.gcards li:first-child b{font-size:24px}.gcards li:first-child .ct{padding:16px 18px 18px}}
</style>
"""


def art_card(slug, lang="pt-BR", cls="card ci", desc=True, h="b"):
    a = ART[slug]
    cat = CAT_L10N.get(lang, {}).get(a["cat"], a["cat"])
    d = f'<span class="desc">{a["desc"]}</span>' if desc else ""
    return (
        f'<a class="{cls}" href="{a["href"]}">{img(slug)}<span class="ct">'
        f'<span class="chip {CAT_CLASS[a["cat"]]}">{cat}</span><{h}>{a["title"]}</{h}>{d}'
        f'<span class="rtime">{a["mins"]} {MIN[lang]} →</span></span></a>'
    )


def set_og(h, slug):
    url = f"{SITE}{IMG}/{slug}.jpg"
    h = re.sub(r'(<meta property="og:image" content=")[^"]*(")', rf"\g<1>{url}\2", h)
    h = re.sub(r'("image"\s*:\s*")[^"]*(")', rf"\g<1>{url}\2", h)
    if "og:image:width" not in h:
        h = h.replace(
            f'content="{url}">',
            f'content="{url}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
            1,
        )
    return h


def add_css(h, css):
    i = h.find("</style>") + len("</style>")
    return h[:i] + css + h[i:]


log = []
# --- índice de artigos
h = idx
if 'id="cards-img"' not in h:
    h = add_css(h, SUB_CSS)
    h = h.replace("<main>", '<main class="idx">', 1)
    m = re.search(r'<div class="cards" style="margin-top:22px">(.*?)</div>', h, re.S)
    slugs = [
        a.rstrip("/").split("/")[-1]
        for a in re.findall(r'<a class="card" href="([^"]+)"', m.group(1))
    ]
    h = (
        h[: m.start()]
        + '<div class="cards" style="margin-top:26px">'
        + "".join(art_card(s, h="h2") for s in slugs)
        + "</div>"
        + h[m.end() :]
    )
    (ROOT / "artigos/index.html").write_text(h, encoding="utf-8")
    log.append("artigos/index")

# --- cada artigo: capa no topo, og:image, Leia também com cards
for slug, a in ART.items():
    p = ROOT / f"artigos/{slug}/index.html"
    h = p.read_text(encoding="utf-8")
    if 'id="cards-img"' in h:
        continue
    h = add_css(h, SUB_CSS)
    h = set_og(h, slug)
    fig = f'<figure class="cover">{img(slug, ALT[slug], eager=True, sizes="(max-width:800px) 100vw, 720px")}</figure>'
    h, n = re.subn(
        r'(<p class="meta">.*?</p>)',
        r"\1" + fig.replace("\\", "\\\\"),
        h,
        count=1,
        flags=re.S,
    )
    assert n == 1, slug
    m = re.search(
        r'<section class="rel"><h2>(.*?)</h2><ul>(.*?)</ul></section>', h, re.S
    )
    rel = [
        x.rstrip("/").split("/")[-1] for x in re.findall(r'href="([^"]+)"', m.group(2))
    ]
    cards = "".join(art_card(r, desc=False) for r in rel if r in ART)
    h = (
        h[: m.start()]
        + f'<section class="rel"><h2>{m.group(1)}</h2><div class="cards">{cards}</div></section>'
        + h[m.end() :]
    )
    p.write_text(h, encoding="utf-8")
    log.append(slug)

# --- ferramentas/serviço/glossário/privacidade: og:image + pendências
for f in [
    "simulador-cbs-ibs",
    "en/cbs-ibs-simulator",
    "es/simulador-cbs-ibs",
    "glossario-reforma-tributaria",
    "en/brazil-tax-reform-consulting",
    "es/consultoria-reforma-tributaria-brasil",
    "politica-de-privacidade",
    "sobre",
    "exemplo-de-parecer",
]:
    p = ROOT / f / "index.html"
    h = p.read_text(encoding="utf-8")
    if 'id="cards-img"' in h:
        continue
    h = add_css(h, SUB_CSS)
    key = f.split("/")[-1]
    if key in TOOLS:
        h = set_og(h, TOOLS[key][0])
    p.write_text(h, encoding="utf-8")
    log.append(f)

# --- homes: seção Guias com cards ilustrados
for f in ["index.html", "pt-pt/index.html", "en/index.html", "es/index.html"]:
    p = ROOT / f
    h = p.read_text(encoding="utf-8")
    if 'id="gcards"' in h:
        continue
    lang = re.search(r'<html lang="([^"]+)"', h).group(1)
    m = re.search(r'<ul class="guias-list">(.*?)</ul>', h, re.S)
    items = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", m.group(1), re.S):
        href = re.search(r'href="([^"]+)"', li).group(1)
        title = re.sub(r"<[^>]+>", "", li).strip()
        key = href.rstrip("/").split("/")[-1]
        if key in ART:
            a = ART[key]
            cat = CAT_L10N.get(lang, {}).get(a["cat"], a["cat"])
            lattr = ' lang="pt-BR"' if lang not in ("pt-BR", "pt-PT") else ""
            items.append(
                f'<li><a href="{href}"{lattr}>{img(key, sizes="(max-width:620px) 100vw, (max-width:980px) 50vw, 380px")}<span class="ct">'
                f'<span class="chip {CAT_CLASS[a["cat"]]}">{cat}</span><b>{a["title"]}</b>'
                f'<span class="rtime">{READ[lang]} · {a["mins"]} {MIN[lang]} →</span></span></a></li>'
            )
        else:
            cover, k = TOOLS[key]
            items.append(
                f'<li><a href="{href}">{img(cover, sizes="(max-width:620px) 100vw, (max-width:980px) 50vw, 380px")}<span class="ct">'
                f'<span class="chip tool">{TOOL_LBL[lang][k]}</span><b>{title}</b>'
                f'<span class="rtime">{OPEN[lang]} →</span></span></a></li>'
            )
    h = h[: m.start()] + '<ul class="gcards">' + "".join(items) + "</ul>" + h[m.end() :]
    h = add_css(h, HOME_CSS)
    p.write_text(h, encoding="utf-8")
    log.append(f)

print(len(log), log)
