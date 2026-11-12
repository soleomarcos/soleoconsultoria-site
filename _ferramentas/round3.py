#!/usr/bin/env python3
"""Rodada 3: home compacta no celular, idioma dos cards EN/ES, capas no sitemap.
Uso: python3 round3.py <raiz-do-repo>   (idempotente)
"""

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
SITE = "https://www.soleoconsultoria.com.br"

MOB = """
<style id="mob-compact">
/* Home no celular: menos rolagem sem tirar conteúdo */
@media (max-width:620px){
  section{padding:48px 0}
  h2{font-size:28px}
  .formats,.pains,.reg,.share .why{display:flex!important;grid-template-columns:none;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;margin-right:-16px;padding:2px 16px 12px 0;scrollbar-width:none;-webkit-overflow-scrolling:touch}
  .formats::-webkit-scrollbar,.pains::-webkit-scrollbar,.reg::-webkit-scrollbar,.share .why::-webkit-scrollbar{display:none}
  .formats>*,.pains>*,.reg>*,.share .why>*{flex:0 0 84%;scroll-snap-align:start;margin:0}
  .gcards li:nth-child(n+5){display:none}
  .gcards{gap:16px}
  .share>*,.feature>*,.wrap>*{min-width:0}
}
</style>
"""

log = []
for f in ["index.html", "pt-pt/index.html", "en/index.html", "es/index.html"]:
    p = ROOT / f
    h = p.read_text(encoding="utf-8")
    if 'id="mob-compact"' not in h:
        i = h.find('<style id="gcards">')
        assert i > 0, f
        j = h.find("</style>", i) + len("</style>")
        h = h[:j] + MOB + h[j:]
        log.append(f"{f}:mob")
    # idioma: lang="pt-BR" só no título (o rótulo "Read guide" é EN/ES)
    h, n = re.subn(
        r'(<li><a href="[^"]+") lang="pt-BR">(.*?)<b>', r'\1>\2<b lang="pt-BR">', h
    )
    if n:
        log.append(f"{f}:lang{n}")
    p.write_text(h, encoding="utf-8")

# sitemap: capas como image:image
sm = ROOT / "sitemap.xml"
s = sm.read_text(encoding="utf-8")
if "xmlns:image" not in s:
    s = s.replace(
        'xmlns:xhtml="http://www.w3.org/1999/xhtml"',
        'xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"',
        1,
    )
MAP = {
    "/simulador-cbs-ibs/": "simulador",
    "/en/cbs-ibs-simulator/": "simulador",
    "/es/simulador-cbs-ibs/": "simulador",
    "/glossario-reforma-tributaria/": "glossario",
    "/en/brazil-tax-reform-consulting/": "servico",
    "/es/consultoria-reforma-tributaria-brasil/": "servico",
}


def add_img(m):
    block = m.group(0)
    if "<image:image>" in block:
        return block
    loc = re.search(r"<loc>([^<]+)</loc>", block).group(1)
    path = loc.replace(SITE, "")
    slug = None
    if path.startswith("/artigos/") and path != "/artigos/":
        slug = path.strip("/").split("/")[-1]
    elif path in MAP:
        slug = MAP[path]
    if not slug or not (ROOT / f"img/capas/{slug}.jpg").exists():
        return block
    tag = f"\n    <image:image><image:loc>{SITE}/img/capas/{slug}.jpg</image:loc></image:image>"
    return block.replace("</loc>", "</loc>" + tag, 1)


s, n = re.subn(r"<url>.*?</url>", add_img, s, flags=re.S)
sm.write_text(s, encoding="utf-8")
log.append(f"sitemap:{s.count('<image:image>')} imagens")
print(log)
