#!/usr/bin/env python3
"""Aplica as correções de design/UX nas 4 homes (pt-BR, pt-PT, en, es).
Uso: python3 uxfix.py <raiz-do-repo>
Idempotente: não reaplica se o marcador ux-fix já existir.
"""

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
HOMES = ["index.html", "pt-pt/index.html", "en/index.html", "es/index.html"]

L10N = {
    "pt-BR": {
        "menu": "Abrir menu",
        "close": "Fechar menu",
        "tool": "Ferramenta",
        "fcontact": "Contato",
        "flinks": "Conteúdo",
    },
    "pt-PT": {
        "menu": "Abrir menu",
        "close": "Fechar menu",
        "tool": "Ferramenta",
        "fcontact": "Contacto",
        "flinks": "Conteúdo",
    },
    "en": {
        "menu": "Open menu",
        "close": "Close menu",
        "tool": "Tool",
        "fcontact": "Contact",
        "flinks": "Resources",
    },
    "es": {
        "menu": "Abrir menú",
        "close": "Cerrar menú",
        "tool": "Herramienta",
        "fcontact": "Contacto",
        "flinks": "Contenido",
    },
}

CSS = r"""
<style id="ux-fix">
/* ===== ux-fix 2026-11-11: correções da crítica de design ===== */
:root{--wa:#1a7a43;--wa-dark:#15693a;--r:4px}

/* 1. Movimento: reveal curto, conteúdo nunca some */
.rv{opacity:.6;transform:translateY(12px);transition:opacity .35s ease,transform .35s ease}
.rv.in{opacity:1;transform:none}
.d1{transition-delay:.06s}.d2{transition-delay:.12s}.d3{transition-delay:.18s}
.rot{min-width:0}

/* 2. Contraste (WCAG AA) */
.stage.par .tag,.stage.par .unit{color:var(--gold)}
section.dark .contract .eyebrow,.contract .eyebrow{color:var(--gold-deep)}
.free{color:#6b5122}
.btn.wa{background:var(--wa)}
.btn.wa:hover{background:var(--wa-dark);box-shadow:0 8px 20px rgba(21,105,58,.3)}
.fab{background:var(--wa)}

/* 3. Hierarquia de CTA: dourado = primário; WhatsApp = secundário com contorno */
.hero .btn.wa{background:transparent;color:var(--wa);border:2px solid var(--wa);padding:13px 24px}
.hero .btn.wa .wa-ico{fill:currentColor}
.hero .btn.wa:hover{background:var(--wa);color:#fff;box-shadow:none}
.cta .btn.wa,.tray .btn.wa{background:transparent;color:#fff;border:2px solid #3fbf74}
.cta .btn.wa{padding:13px 24px}
.cta .btn.wa:hover,.tray .btn.wa:hover{background:var(--wa);border-color:var(--wa);box-shadow:none}

/* 4. Consistência: um raio (4px) para botões e cartões; tipografia em escala 14/16/18 */
.btn,.guias-list li a,.share .why div,.sharebox,.contract,.fmt,.front,.pain .fa,.pain .ba{border-radius:var(--r)}
.sharebox .btn,.tray{border-radius:var(--r)}
.sub{font-size:18px}
.stage p,.stage ul,.pain .ba{font-size:16px}
.track{font-size:14px}
.pain .fa small,.contact em{font-size:14px}
.guias-list .guias-tools a{position:relative;padding-top:32px}
.guias-tools a::before{content:attr(data-tag);position:absolute;top:10px;left:16px;font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--gold-deep);font-weight:700}

/* 5. Painel da pauta escondido não vaza sombra nem recebe foco */
.tray{visibility:hidden;transition:transform .35s cubic-bezier(.2,.9,.3,1.2),visibility 0s linear .35s}
.tray.show{visibility:visible;transition:transform .35s cubic-bezier(.2,.9,.3,1.2),visibility 0s}
.tray .x{min-width:44px;min-height:44px;font-size:24px}

/* 6. Áreas de toque >= 44px */
.contact a{display:inline-block;padding:10px 0;min-height:44px}
.about a,.guias-all{display:inline-block;padding:10px 0}
footer a{display:inline-block;padding:11px 0;min-height:44px}

/* 7. Rodapé em colunas */
footer{font-size:14px;padding:36px 0 110px}
footer .wrap.fgrid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:28px;flex-direction:initial}
footer h4{margin:0 0 8px;font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--gold-deep);font-weight:700}
footer ul{list-style:none;margin:0;padding:0}
footer li{margin:0}
footer .fbrand p{margin:0 0 4px}
footer a{color:var(--navy);text-decoration:underline;text-underline-offset:3px}
footer a:hover{color:var(--gold-deep)}

/* 8. Menu: botão hambúrguer + CTA no header em telas <= 980px */
.menu-tog,.hdr-cta{display:none}
.menu-tog{width:44px;height:44px;border:1px solid rgba(255,255,255,.25);background:transparent;border-radius:var(--r);color:#fff;cursor:pointer;place-items:center;flex:none;padding:0}
.menu-tog span,.menu-tog span::before,.menu-tog span::after{display:block;width:20px;height:2px;background:currentColor;position:relative;transition:transform .2s,background .2s}
.menu-tog span::before,.menu-tog span::after{content:"";position:absolute;left:0}
.menu-tog span::before{top:-6px}.menu-tog span::after{top:6px}
header.top.menu-open .menu-tog span{background:transparent}
header.top.menu-open .menu-tog span::before{transform:translateY(6px) rotate(45deg)}
header.top.menu-open .menu-tog span::after{transform:translateY(-6px) rotate(-45deg)}
.hdr-right{display:flex;align-items:center;gap:10px}
@media (max-width:980px){
  .menu-tog{display:grid}
  .hdr-cta{display:inline-flex;margin-left:0}
  header.top nav{display:none;position:absolute;top:100%;left:0;right:0;flex-direction:column;align-items:stretch;background:var(--navy);padding:6px 24px 18px;border-bottom:3px solid var(--gold);box-shadow:0 18px 30px rgba(0,0,0,.25);max-height:calc(100vh - 70px);overflow:auto}
  header.top.menu-open nav{display:flex}
  header.top nav a.lk{display:block;margin:0;padding:13px 2px;font-size:16px;border-bottom:1px solid rgba(255,255,255,.08)}
  header.top nav a.lk::after{display:none}
  header.top nav .btn.small{margin:14px 0 0;justify-content:center;font-size:15px;padding:14px}
  /* selo do hero sai no mobile/tablet: o brasão já está no header */
  .hero .portrait{display:none}
  .hero{padding:48px 0 52px}
  footer .wrap.fgrid{grid-template-columns:1fr 1fr}
  footer .fbrand{grid-column:1/-1}
}
@media (max-width:560px){
  .wrap{padding:0 16px}
  header.top .wrap{height:60px}
  .brand{min-width:0;gap:8px}
  .brand img{width:34px;height:34px}
  .brand span{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .hdr-cta{display:none}
  .brand{padding:5px 0}
  .langbar a{min-height:36px;padding:8px 9px}
  header.top nav{padding:6px 16px 18px}
  html{scroll-padding-top:72px}
  .hero h1{font-size:36px}
  .lead{font-size:18px}
  .ctas .btn{width:100%;justify-content:center}
  .fab{width:50px;height:50px;right:14px;bottom:16px}
  .fab svg{width:26px;height:26px}
  .tray.show~.fab{bottom:84px}
  footer .wrap.fgrid{grid-template-columns:1fr}
  /* nenhum texto corrido abaixo de 14px */
  .stage .tag,.contact small{font-size:12.5px}
}

/* 9. Dificuldades: sem depender de hover em telas de toque */
@media (hover:none){
  #identifica .sub{display:none}
  .pain{height:auto;perspective:none;cursor:default}
  .pain .in{transform:none!important;transform-style:flat}
  .pain .fa,.pain .ba{position:static;backface-visibility:visible;transform:none}
  .pain .fa small{display:none}
  .pain .fa{border-bottom:0}
}

@media (prefers-reduced-motion:reduce){.rv{opacity:1;transform:none}}
</style>
"""

JS = r"""
<script id="ux-fix-js">
(()=>{const hd=document.querySelector('header.top');const tg=hd&&hd.querySelector('.menu-tog');if(!tg)return;
const nav=hd.querySelector('nav');const L=tg.dataset;
const set=o=>{hd.classList.toggle('menu-open',o);tg.setAttribute('aria-expanded',o);tg.setAttribute('aria-label',o?L.close:L.open)};
tg.addEventListener('click',()=>set(!hd.classList.contains('menu-open')));
nav.addEventListener('click',e=>{if(e.target.closest('a'))set(false)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&hd.classList.contains('menu-open')){set(false);tg.focus()}});
document.addEventListener('click',e=>{if(!hd.contains(e.target))set(false)});
matchMedia('(min-width:981px)').addEventListener('change',m=>{if(m.matches)set(false)});})();
</script>
"""


def build_footer(inner: str, t: dict) -> str:
    parts = [p.strip() for p in re.split(r"\s·\s", re.sub(r"\s+", " ", inner).strip())]
    info, contacts, links = [], [], []
    for p in parts:
        if p.startswith("<a"):
            links.append(re.sub(r'\sstyle="[^"]*"', "", p))
        elif "@" in p and " " not in p:
            contacts.append(f'<a href="mailto:{p}">{p}</a>')
        elif p.startswith("WhatsApp") and "(64)" in p:
            contacts.append(f'<a href="#" data-wa>{p}</a>')
        elif p.startswith("WhatsApp") and "(43)" in p:
            num = re.sub(r"\D", "", p)
            contacts.append(
                f'<a href="https://wa.me/55{num}" target="_blank" rel="noopener">{p}</a>'
            )
        else:
            info.append(p)
    li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)
    return (
        '<footer>\n      <div class="wrap fgrid">\n'
        f'        <div class="fbrand">{"".join(f"<p>{x}</p>" for x in info)}</div>\n'
        f'        <div><h4>{t["fcontact"]}</h4><ul>{li(contacts)}</ul></div>\n'
        f'        <div><h4>{t["flinks"]}</h4><ul>{li(links)}</ul></div>\n'
        "      </div>\n    </footer>"
    )


def patch(path: Path) -> list:
    h = path.read_text(encoding="utf-8")
    if 'id="ux-fix"' in h:
        return ["já aplicado"]
    log = []
    lang = re.search(r'<html lang="([^"]+)"', h).group(1)
    t = L10N[lang]

    # CSS depois do <style> principal (o primeiro </style> do <head>)
    i = h.find("</style>") + len("</style>")
    h = h[:i] + CSS + h[i:]
    log.append("css")

    # Header: CTA visível no tablet + botão de menu
    cta = re.search(r'<a class="btn small" href="#" data-form>([^<]*)</a>', h).group(1)
    tog = (
        f'<div class="hdr-right"><a class="btn small hdr-cta" href="#" data-form>{cta}</a>'
        f'<button class="menu-tog" type="button" aria-expanded="false" aria-controls="site-nav" '
        f'aria-label="{t["menu"]}" data-open="{t["menu"]}" data-close="{t["close"]}"><span></span></button></div>\n        <nav id="site-nav">'
    )
    h, n = re.subn(r"<nav>", tog, h, count=1)
    assert n == 1
    log.append("menu")
    # o </nav> precisa fechar dentro de .hdr-right? Não: nav fica dentro de .hdr-right
    h = h.replace(
        '</nav>\n      </div>\n      <div class="progress"',
        '</nav></div>\n      </div>\n      <div class="progress"',
        1,
    )
    assert "</nav></div>" in h, "estrutura do header mudou"

    # H1 fixo (sem rotação)
    h, n = re.subn(
        r"if\(!matchMedia\('\(prefers-reduced-motion: reduce\)'\)\.matches\)setInterval\(",
        "if(0)setInterval(",
        h,
    )
    assert n == 1
    log.append("h1-fixo")

    # Contadores: valor final direto
    h, n = re.subn(r'data-count="(\d+)">0<', r'data-count="\1">\1<', h)
    log.append(f"contadores:{n}")
    h, n = re.subn(
        r"const t=setInterval\(\(\)=>\{c=Math\.min\(to,c\+st\);n\.textContent=c;if\(c>=to\)clearInterval\(t\)\},30\)",
        "n.textContent=to",
        h,
    )
    assert n == 1

    # Rótulo "Ferramenta" nos cards de ferramenta
    tags = {
        "tool": t["tool"],
        "gloss": {
            "pt-BR": "Glossário",
            "pt-PT": "Glossário",
            "en": "Glossary",
            "es": "Glosario",
        }[lang],
        "svc": {
            "pt-BR": "Serviço",
            "pt-PT": "Serviço",
            "en": "Service",
            "es": "Servicio",
        }[lang],
    }

    def tag(m):
        href = m.group(1)
        k = "tool" if "simula" in href else ("gloss" if "glossario" in href else "svc")
        return f'<li class="guias-tools"><a data-tag="{tags[k]}" href="{href}"'

    h, n = re.subn(r'<li class="guias-tools"><a href="([^"]+)"', tag, h)
    log.append(f"tools:{n}")

    # Rodapé em colunas
    m = re.search(
        r"<footer>\s*<div class=\"wrap\">\s*<span\s*>(.*?)</span\s*>\s*</div>\s*</footer>",
        h,
        re.S,
    )
    h = h[: m.start()] + build_footer(m.group(1), t) + h[m.end() :]
    log.append("footer")

    # JS do menu antes de </body>
    i = h.rfind("</body>")
    h = h[:i] + JS + h[i:]
    path.write_text(h, encoding="utf-8")
    return log


for f in HOMES:
    print(f, patch(ROOT / f))
