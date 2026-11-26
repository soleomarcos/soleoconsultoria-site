#!/usr/bin/env python3
"""Boletim Empresarial Diário — gerador estático.

Uso:
  python3 _ferramentas/boletim.py <repo>          # gera tudo a partir de _boletim/edicoes/*.json
  python3 _ferramentas/boletim.py <repo> --qa     # só o QA de copy das edições

Entradas:
  _boletim/config.json            webapp_url do Apps Script (inscrição) e parâmetros fixos
  _boletim/edicoes/AAAA-MM-DD.json uma edição por dia (esquema em _boletim/README.md)

Saídas (publicadas):
  boletim/index.html              página da newsletter (inscrição + arquivo)
  boletim/<slug>/index.html       página de cada edição
  boletim/email/<slug>.html       versão e-mail (placeholders {{NOME}}, {{DESCADASTRO}})
  boletim/feed.json               JSON Feed lido pelo Apps Script de envio
  boletim/feed.xml                RSS 2.0
  sitemap.xml, robots.txt         atualizados de forma idempotente
  menu "Boletim" nas páginas pt-BR (idempotente, marcador data-nl-nav)
"""

import html, json, re, sys, unicodedata
from datetime import date, datetime
from pathlib import Path

SITE = "https://www.soleoconsultoria.com.br"
WA = "https://wa.me/5564992270765?text=Ol%C3%A1%2C%20Sol%C3%A9o!%20Li%20o%20Boletim%20Empresarial%20e%20gostaria%20de%20agendar%20um%20atendimento."
NOME = "Boletim Empresarial Diário"
DIAS = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]
MESES = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]
PROIBIDOS = re.compile(
    r"\b(ademicon|cons[óo]rcios?|d[íi]vidas?|processos?|execu[çc](?:ão|ao|ões|oes)|advogad[oa]s?|advocacia|oab)\b",
    re.I,
)
TRIB_CLS = {
    "STF": "stf",
    "STJ": "stj",
    "TST": "trab",
    "TRT": "trab",
    "TRF": "trf",
    "TJ": "tj",
    "CARF": "adm",
    "CVM": "adm",
    "CADE": "adm",
}

esc = lambda s: html.escape(str(s), quote=True)


def slugify(s, n=70):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n].rstrip("-")


def dt(d):
    return datetime.strptime(d, "%Y-%m-%d").date()


def br(d):
    return dt(d).strftime("%d/%m/%Y")


def extenso(d):
    x = dt(d)
    return f"{DIAS[x.weekday()]}, {x.day} de {MESES[x.month-1]} de {x.year}"


def trib_cls(t):
    t = t.upper()
    for k, v in TRIB_CLS.items():
        if t.startswith(k):
            return v
    return "adm"


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


# ---------------------------------------------------------------- base do site
def base_parts(repo):
    """Reaproveita head (ícones, estilos, GA4), header e footer de /artigos/."""
    h = (repo / "artigos/index.html").read_text()
    head = h[h.find("<head>") + 6 : h.find("</head>")]
    head = re.sub(r"<title>.*?</title>", "", head, flags=re.S)
    head = re.sub(
        r'<meta (?:name="(?:description|robots|twitter:[a-z]+)"|property="og:[a-z:]+")[^>]*>\s*',
        "",
        head,
    )
    head = re.sub(r'<link rel="(?:canonical|alternate)"[^>]*>\s*', "", head)
    head = re.sub(
        r'<script type="application/ld\+json">.*?</script>\s*', "", head, flags=re.S
    )
    head = head.replace("region:'artigos'", "region:'boletim'")
    header = re.search(r'<header class="top">.*?</header>', h, re.S).group(0)
    header = nav_patch_str(header)
    footer = re.search(r"<footer>.*?</footer>", h, re.S).group(0)
    return head, header, footer


def nav_patch_str(s):
    if "data-nl-nav" in s:
        return s
    return s.replace(
        f'<a href="{SITE}/artigos/">Artigos</a>',
        f'<a href="{SITE}/artigos/">Artigos</a><a href="{SITE}/boletim/" data-nl-nav>Boletim</a>',
        1,
    )


# ---------------------------------------------------------------- CSS / JS próprios
CSS = """<style id="nl-css">
:root{--navy2:#13295a;--ink2:#0b1220}
.nl-wrap{max-width:1140px;margin:0 auto;padding:0 20px}
.nl-hero{position:relative;overflow:hidden;background:radial-gradient(1200px 500px at 85% -10%,#1c3a78 0%,rgba(28,58,120,0) 60%),linear-gradient(160deg,#0b1d40 0%,#0a1733 70%,#08122a 100%);color:#fff;padding:56px 0 64px}
.nl-hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(200,159,84,.09) 1px,transparent 1px),linear-gradient(90deg,rgba(200,159,84,.09) 1px,transparent 1px);background-size:56px 56px;mask-image:radial-gradient(ellipse at 70% 30%,#000 0%,transparent 70%);-webkit-mask-image:radial-gradient(ellipse at 70% 30%,#000 0%,transparent 70%);animation:nlgrid 26s linear infinite}
.nl-hero:after{content:"";position:absolute;left:-30%;top:0;width:30%;height:2px;background:linear-gradient(90deg,transparent,#c89f54,transparent);animation:nlsweep 7s ease-in-out infinite}
@keyframes nlgrid{to{background-position:56px 56px,56px 56px}}
@keyframes nlsweep{0%{left:-30%}60%,100%{left:110%}}
.nl-hero .nl-wrap{position:relative;display:grid;grid-template-columns:1.15fr .85fr;gap:48px;align-items:center}
.nl-eyebrow{display:inline-flex;align-items:center;gap:10px;font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#e8d3a6;margin:0 0 14px}
.nl-dot{width:8px;height:8px;border-radius:50%;background:#c89f54;box-shadow:0 0 0 0 rgba(200,159,84,.6);animation:nlpulse 2.4s infinite}
@keyframes nlpulse{0%{box-shadow:0 0 0 0 rgba(200,159,84,.55)}70%{box-shadow:0 0 0 10px rgba(200,159,84,0)}100%{box-shadow:0 0 0 0 rgba(200,159,84,0)}}
.nl-hero h1{font-family:"Playfair Display",Georgia,serif;color:#fff;font-size:52px;line-height:1.08;margin:0 0 16px;letter-spacing:-.01em}
.nl-hero h1 em{font-style:normal;color:#e2c48a}
.nl-hero .sub{font-size:19px;line-height:1.6;color:#dbe3f0;margin:0 0 22px;max-width:560px}
.nl-pills{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.nl-pills li{font-size:14px;color:#e5e7eb;border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:6px 12px;background:rgba(255,255,255,.04)}
.nl-pills b{color:#fff}
.nl-card{background:#fff;color:var(--ink);border-radius:6px;padding:26px;box-shadow:0 30px 60px rgba(0,0,0,.35);border-top:4px solid #c89f54}
.nl-card h2{font-family:"Playfair Display",Georgia,serif;color:var(--navy);font-size:24px;margin:0 0 6px}
.nl-card p.s{margin:0 0 16px;font-size:15px;color:var(--muted)}
.nl-form label{display:block;font-size:14px;font-weight:600;color:var(--ink);margin:0 0 12px}
.nl-form input[type=email],.nl-form input[type=text]{display:block;width:100%;margin-top:6px;font:16px Inter,system-ui,sans-serif;padding:12px 14px;border:1px solid #cbd5e1;border-radius:4px;background:#fff;color:var(--ink)}
.nl-form input:focus{outline:2px solid #c89f54;outline-offset:1px;border-color:#c89f54}
.nl-form .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.nl-form .ck{display:flex;gap:10px;align-items:flex-start;font-weight:400;font-size:14px;color:var(--muted)}
.nl-form .ck input{margin-top:4px;width:18px;height:18px;flex:none}
.nl-form .hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.btn-gold{display:block;width:100%;border:0;cursor:pointer;background:#c89f54;color:#0b1d40;font:700 17px Inter,system-ui,sans-serif;padding:14px 20px;border-radius:4px;transition:background .2s,transform .2s}
.btn-gold:hover{background:#d8b26c}.btn-gold:active{transform:translateY(1px)}.btn-gold[disabled]{opacity:.6;cursor:wait}
.nl-msg{margin:12px 0 0;font-size:15px;min-height:1px}.nl-msg.ok{color:#14532d;background:#dcfce7;border-radius:4px;padding:12px 14px}.nl-msg.err{color:#7f1d1d;background:#fee2e2;border-radius:4px;padding:12px 14px}
.nl-ticker{background:#08122a;border-top:1px solid rgba(200,159,84,.35);border-bottom:1px solid rgba(200,159,84,.35);overflow:hidden;white-space:nowrap}
.nl-ticker .tr{display:inline-flex;gap:0;animation:nltick 40s linear infinite;padding:12px 0}
.nl-ticker span{font-size:13px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#cbd5e1;padding:0 22px;border-right:1px solid rgba(255,255,255,.12)}
.nl-ticker span b{color:#e2c48a}
@keyframes nltick{to{transform:translateX(-50%)}}
.nl-sec{padding:56px 0}.nl-sec h2.t{font-family:"Playfair Display",Georgia,serif;color:var(--navy);font-size:32px;margin:0 0 8px}.nl-sec p.st{color:var(--muted);margin:0 0 26px;max-width:720px}
.nl-feat{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.nl-feat div{background:#fff;border:1px solid var(--line);border-radius:6px;padding:22px}
.nl-feat .n{font-family:"Playfair Display",Georgia,serif;font-size:30px;color:#c89f54;line-height:1}
.nl-feat h3{font-family:"Playfair Display",Georgia,serif;color:var(--navy);font-size:20px;margin:10px 0 6px}
.nl-feat p{margin:0;font-size:15px;color:var(--muted)}
.nl-last{display:grid;grid-template-columns:1.2fr .8fr;gap:0;background:#0b1d40;border-radius:6px;overflow:hidden;text-decoration:none;color:#fff;transition:transform .2s,box-shadow .2s}
.nl-last:hover{transform:translateY(-3px);box-shadow:0 18px 40px rgba(11,29,64,.25)}
.nl-last .a{padding:30px 32px}.nl-last .k{font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#e2c48a}
.nl-last h3{font-family:"Playfair Display",Georgia,serif;font-size:28px;line-height:1.25;margin:10px 0;color:#fff}
.nl-last p{color:#dbe3f0;margin:0 0 14px}.nl-last .go{font-weight:700;color:#e2c48a}
.nl-last ul{list-style:none;margin:0;padding:26px 28px;background:#13295a;display:flex;flex-direction:column;gap:12px;justify-content:center}
.nl-last li{font-size:15px;color:#e5e7eb;display:flex;gap:10px;align-items:baseline}
.badge{display:inline-block;flex:none;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border-radius:999px;background:#e6ecf7;color:#0b1d40}
.badge.stf{background:#0b1d40;color:#fff;box-shadow:inset 0 0 0 1px #c89f54}.badge.stj{background:#dcf1ec;color:#0f3b3d}.badge.trab{background:#dff1e6;color:#1d5e40}.badge.trf{background:#ebe8fb;color:#3d3480}.badge.tj{background:#f6e1e8;color:#6b2740}.badge.adm{background:#f4ead6;color:#6b5122}
.nl-arch{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.nl-arch li{border-bottom:1px solid var(--line)}
.nl-arch a{display:grid;grid-template-columns:130px 1fr auto;gap:16px;align-items:baseline;padding:14px 4px;text-decoration:none;color:var(--ink)}
.nl-arch a:hover b{color:var(--gold-deep)}.nl-arch time{font-size:14px;color:var(--muted)}.nl-arch b{font-weight:600;color:var(--navy)}.nl-arch span{font-size:14px;color:var(--gold-deep);font-weight:700}
.nl-faq{max-width:760px}
.js .reveal{opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease}.js .reveal.in{opacity:1;transform:none}
.ed-kick{font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold-deep);margin:0 0 6px}
.ed-toc{background:#fff;border:1px solid var(--line);border-radius:6px;padding:16px 20px;margin:22px 0}
.ed-toc b{display:block;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.ed-toc ol{margin:0;padding-left:20px}.ed-toc li{padding:5px 0}.ed-toc a{display:inline;padding:0}
.radar{display:grid;gap:14px;margin:16px 0}
.nw{background:#fff;border:1px solid var(--line);border-left:4px solid #c89f54;border-radius:6px;padding:18px 20px}
.nw .top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:14px;color:var(--muted)}
.nw h3{font-family:"Playfair Display",Georgia,serif;color:var(--navy);font-size:21px;line-height:1.3;margin:8px 0 6px}
.nw p{margin:0 0 8px}.nw .imp{font-size:16px;background:var(--gold-soft);border-radius:4px;padding:10px 12px}
.nw .src a{font-size:14px;font-weight:600;display:inline-block;padding:8px 0}
.nl-inline{background:linear-gradient(160deg,#0b1d40,#13295a);color:#fff;border-radius:6px;padding:26px;margin:38px 0}
.nl-inline h2{color:#fff;margin:0 0 6px;font-size:24px}.nl-inline p{color:#dbe3f0;margin:0 0 16px}
.nl-inline .nl-form label{color:#fff}.nl-inline .nl-form .ck{color:#cbd5e1}.nl-inline .nl-form .ck a{color:#e2c48a}
.ed-nav{display:flex;justify-content:space-between;gap:16px;margin:30px 0;font-size:15px}.ed-nav a{display:inline-block;padding:10px 0;font-weight:600}
@media(max-width:900px){.nl-hero .nl-wrap{grid-template-columns:1fr;gap:30px}.nl-hero h1{font-size:40px}.nl-feat{grid-template-columns:1fr}.nl-last{grid-template-columns:1fr}}
@media(max-width:560px){.nl-hero{padding:36px 0 44px}.nl-hero h1{font-size:33px}.nl-hero .sub{font-size:17px}.nl-form .row{grid-template-columns:1fr}.nl-arch a{grid-template-columns:1fr;gap:2px}.nl-sec{padding:40px 0}.nl-sec h2.t{font-size:26px}.nl-card{padding:20px}.nl-last .a{padding:22px}.nl-last h3{font-size:23px}}
@media(max-width:620px){header.top nav{flex-wrap:nowrap!important}}
@media(prefers-reduced-motion:reduce){.nl-hero:before,.nl-hero:after,.nl-dot,.nl-ticker .tr{animation:none!important}.js .reveal{opacity:1;transform:none;transition:none}.nl-last,.btn-gold{transition:none}}
</style>"""

JS = """<script id="nl-js">(function(){
var R=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
if(!R&&'IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px'});document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)})}else{document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in')})}
document.querySelectorAll('form[data-nl]').forEach(function(f){f.addEventListener('submit',function(ev){
 var url=f.getAttribute('action');if(!url||url.indexOf('script.google.com')<0)return;ev.preventDefault();
 var m=f.querySelector('.nl-msg'),b=f.querySelector('button'),em=f.email.value.trim();
 if(f.website&&f.website.value){return}
 b.disabled=true;m.className='nl-msg';m.textContent='Enviando…';
 fetch(url,{method:'POST',mode:'no-cors',body:new URLSearchParams(new FormData(f))}).then(function(){
  m.className='nl-msg ok';m.textContent='Pronto! Enviamos um link de confirmação para '+em+'. Confirme no seu e-mail para começar a receber.';f.reset();
  try{gtag('event','newsletter_signup',{origem:f.origem?f.origem.value:''});gtag('event','generate_lead',{method:'newsletter'})}catch(e){}
 }).catch(function(){m.className='nl-msg err';m.textContent='Não foi possível enviar agora. Tente de novo em instantes.'}).finally(function(){b.disabled=false});
})});
})();</script>"""


def form_html(cfg, origem, compact=False):
    url = esc(cfg.get("webapp_url", ""))
    extra = (
        ""
        if compact
        else (
            '<div class="row"><label>Nome<input type="text" name="nome" autocomplete="name"></label>'
            '<label>Empresa<input type="text" name="empresa" autocomplete="organization"></label></div>'
        )
    )
    return (
        f'<form class="nl-form" action="{url}" method="post" target="_blank" data-nl>'
        f'<label>E-mail corporativo<input type="email" name="email" required autocomplete="email" placeholder="voce@empresa.com.br"></label>'
        f"{extra}"
        '<input type="text" name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">'
        f'<input type="hidden" name="origem" value="{esc(origem)}">'
        f'<label class="ck"><input type="checkbox" name="aceite" value="sim" required><span>Quero receber o {NOME} e li a <a href="{SITE}/politica-de-privacidade/">Política de Privacidade</a>.</span></label>'
        '<button class="btn-gold" type="submit">Quero receber</button>'
        '<p class="nl-msg" role="status" aria-live="polite"></p></form>'
    )


def page(head, header, footer, *, title, desc, canonical, og_type, ld, body, og_image):
    return (
        '<!doctype html>\n<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">\n'
        '<meta name="robots" content="index, follow, max-image-preview:large">'
        f'<link rel="canonical" href="{canonical}">\n'
        f'<link rel="alternate" type="application/rss+xml" title="{NOME}" href="{SITE}/boletim/feed.xml">\n'
        f'<meta property="og:type" content="{og_type}"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="Soléo Consultoria Empresarial">\n'
        f'<meta property="og:url" content="{canonical}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">\n'
        f'<meta property="og:image" content="{og_image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">\n'
        f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
        + head.strip()
        + "\n"
        + CSS
        + "\n<script>document.documentElement.classList.add('js')</script>"
        + "\n</head><body>\n"
        + header
        + "\n"
        + body
        + footer
        + "\n"
        + JS
        + "</body></html>\n"
    )


AD = (
    '<aside class="ad" aria-label="Publicidade"><small>Publicidade</small><ins class="adsbygoogle" style="display:block;text-align:center" '
    'data-ad-layout="in-article" data-ad-format="fluid" data-ad-client="ca-pub-5838065593754446" data-ad-slot="{slot}"></ins>'
    "<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></aside>"
)
ADS_JS = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5838065593754446" crossorigin="anonymous"></script>'
OG = f"{SITE}/img/capas/boletim.jpg"
PERSON = {
    "@type": "Person",
    "@id": f"{SITE}/sobre/#person",
    "name": "Marcos Soléo",
    "jobTitle": "Consultor empresarial",
    "url": f"{SITE}/sobre/",
}
ORG = {
    "@type": "Organization",
    "@id": f"{SITE}/#org",
    "name": "Soléo Consultoria Empresarial",
    "url": f"{SITE}/",
    "logo": f"{SITE}/favicon-192.png",
}


# ---------------------------------------------------------------- edições
def load(repo):
    eds = []
    for p in sorted((repo / "_boletim/edicoes").glob("*.json")):
        e = json.loads(p.read_text())
        e.setdefault("slug", f'{e["data"]}-{slugify(e["titulo"], 60)}')
        eds.append(e)
    eds.sort(key=lambda e: e["data"])
    for i, e in enumerate(eds, 1):
        e["n"] = i
    return eds


def words(e):
    t = " ".join(
        [e["artigo"]["lead"]]
        + [s["html"] for s in e["artigo"]["secoes"]]
        + [n["resumo"] + " " + n.get("impacto", "") for n in e["noticias"]]
    )
    return len(strip_tags(t).split())


def qa(e):
    blobs = [
        e["titulo"],
        e["descricao"],
        e["assunto"],
        e.get("preheader", ""),
        e["artigo"]["lead"],
    ]
    blobs += [s["h2"] + " " + s["html"] for s in e["artigo"]["secoes"]]
    blobs += [
        n["titulo"] + " " + n["resumo"] + " " + n.get("impacto", "")
        for n in e["noticias"]
    ]
    hits = sorted(
        {m.group(0).lower() for b in blobs for m in PROIBIDOS.finditer(strip_tags(b))}
    )
    erros = []
    if hits:
        erros.append("termos proibidos: " + ", ".join(hits))
    if not e["noticias"]:
        erros.append("sem notícias")
    for n in e["noticias"]:
        if not n.get("fonte", "").startswith("https://"):
            erros.append("notícia sem fonte https: " + n["titulo"][:50])
    return erros


def news_html(e, ad_slot):
    out, half = [], (len(e["noticias"]) + 1) // 2
    for i, n in enumerate(e["noticias"]):
        if i == half and len(e["noticias"]) > 2:
            out.append(AD.format(slot=ad_slot))
        imp = (
            f'<p class="imp"><b>Na prática:</b> {esc(n["impacto"])}</p>'
            if n.get("impacto")
            else ""
        )
        quando = f' · {br(n["data"])}' if n.get("data") else ""
        out.append(
            f'<article class="nw" id="n{i+1}"><div class="top"><span class="badge {trib_cls(n["tribunal"])}">{esc(n["tribunal"])}</span>'
            f'<span>{esc(n.get("tema", ""))}{quando}</span></div>'
            f'<h3>{esc(n["titulo"])}</h3><p>{esc(n["resumo"])}</p>{imp}'
            f'<p class="src"><a href="{esc(n["fonte"])}" target="_blank" rel="noopener">Fonte: {esc(n.get("fonte_nome", n["tribunal"]))} ↗</a></p></article>'
        )
    return '<div class="radar">' + "".join(out) + "</div>"


def edition_page(e, prev, nxt, cfg, parts):
    head, header, footer = parts
    url = f"{SITE}/boletim/{e['slug']}/"
    mins = max(3, round(words(e) / 200))
    secs = e["artigo"]["secoes"]
    body_secs = []
    for i, s in enumerate(secs):
        body_secs.append(f'<h2 id="s{i+1}">{esc(s["h2"])}</h2>{s["html"]}')
        if i == 1:
            body_secs.append(AD.format(slot="2386684593"))
    toc = "".join(
        f'<li><a href="#s{i+1}">{esc(s["h2"])}</a></li>' for i, s in enumerate(secs)
    )
    toc += f'<li><a href="#radar">Radar dos tribunais ({len(e["noticias"])} decisões)</a></li>'
    fontes = "".join(
        f'<li><a href="{esc(f["url"])}" target="_blank" rel="noopener">{esc(f["nome"])}</a></li>'
        for f in e.get("fontes", [])
    )
    nav = (
        '<nav class="ed-nav" aria-label="Edições">'
        + (
            f'<a href="{SITE}/boletim/{prev["slug"]}/">← Edição anterior</a>'
            if prev
            else "<span></span>"
        )
        + f'<a href="{SITE}/boletim/">Todas as edições →</a>'
        + "</nav>"
    )
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "NewsArticle",
                "@id": url + "#article",
                "headline": e["titulo"][:110],
                "description": e["descricao"],
                "datePublished": e["data"] + "T07:00:00-03:00",
                "dateModified": e.get("atualizado", e["data"]) + "T07:00:00-03:00",
                "inLanguage": "pt-BR",
                "mainEntityOfPage": url,
                "image": [OG],
                "author": PERSON,
                "publisher": ORG,
                "isPartOf": {
                    "@type": "Periodical",
                    "name": NOME,
                    "url": f"{SITE}/boletim/",
                },
                "articleSection": e.get("tema", "Direito empresarial"),
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Início",
                        "item": f"{SITE}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Boletim",
                        "item": f"{SITE}/boletim/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": br(e["data"]),
                        "item": url,
                    },
                ],
            },
        ],
    }
    body = (
        f'<main><nav class="crumbs"><a href="{SITE}/">Início</a> › <a href="{SITE}/boletim/">Boletim</a> › {br(e["data"])}</nav><article>'
        f'<p class="ed-kick">{NOME} · Edição nº {e["n"]} · {extenso(e["data"])}</p>'
        f'<h1>{esc(e["titulo"])}</h1>'
        f'<p class="meta">Por <a href="{SITE}/sobre/">Marcos Soléo</a>, consultor empresarial · Publicado em {br(e["data"])} · {mins} min de leitura</p>'
        f'<p class="lead">{esc(e["artigo"]["lead"])}</p>'
        f'<nav class="ed-toc" aria-label="Nesta edição"><b>Nesta edição</b><ol>{toc}</ol></nav>'
        + "".join(body_secs)
        + f'<h2 id="radar">Radar dos tribunais</h2><p>Decisões e julgamentos de STF, STJ, TST, TRFs, TJs e TRTs com efeito para empresas, resumidos a partir das fontes oficiais.</p>'
        + news_html(e, "6022356477")
        + f'<section class="nl-inline" aria-labelledby="nlin"><h2 id="nlin">Receba a próxima edição no seu e-mail</h2><p>Todo dia às 7h: um artigo de direito empresarial e o radar dos tribunais. Gratuito; cancele quando quiser.</p>{form_html(cfg, "edicao-" + e["data"], compact=True)}</section>'
        + (
            f'<section class="src"><h2>Fontes</h2><ul>{fontes}</ul><p class="note">Conteúdo informativo elaborado a partir das fontes oficiais citadas, em {br(e["data"])}.</p></section>'
            if fontes
            else ""
        )
        + f'<div class="cta"><h2>Quer avaliar o efeito na sua empresa?</h2><p>Triagem de 5 minutos pelo WhatsApp, sem custo e sem compromisso.</p><a class="btn" href="{WA}" target="_blank" rel="noopener">Agendar triagem pelo WhatsApp</a></div>'
        + nav
        + "</article></main>"
    )
    return page(
        head + ADS_JS,
        header,
        footer,
        title=f'{e["titulo"]} | {NOME}',
        desc=e["descricao"],
        canonical=url,
        og_type="article",
        ld=ld,
        body=body,
        og_image=OG,
    )


def index_page(eds, cfg, parts):
    head, header, footer = parts
    url = f"{SITE}/boletim/"
    last = eds[-1] if eds else None
    desc = "Newsletter gratuita: todo dia às 7h, um artigo de direito empresarial e o radar de STF, STJ, TST, TRFs, TJs e TRTs explicado para empresas."
    tick = "".join(
        f"<span><b>{a}</b> {b}</span>"
        for a, b in [
            ("STF", "repercussão geral"),
            ("STJ", "recursos repetitivos"),
            ("TST", "relações de trabalho"),
            ("TRF", "tributos federais"),
            ("TJ", "contratos e sociedades"),
            ("TRT", "passivo trabalhista"),
            ("CARF", "contencioso administrativo"),
            ("CVM", "mercado de capitais"),
        ]
    )
    lastcard = ""
    if last:
        lis = "".join(
            f'<li><span class="badge {trib_cls(n["tribunal"])}">{esc(n["tribunal"])}</span>{esc(n["titulo"])}</li>'
            for n in last["noticias"][:4]
        )
        lastcard = (
            f'<section class="nl-sec" style="padding-top:0"><div class="nl-wrap reveal"><h2 class="t">Edição de hoje</h2><p class="st">Leia no site a edição mais recente, publicada em {extenso(last["data"])}.</p>'
            f'<a class="nl-last" href="{url}{last["slug"]}/"><div class="a"><span class="k">Edição nº {last["n"]} · {br(last["data"])}</span><h3>{esc(last["titulo"])}</h3>'
            f'<p>{esc(last["descricao"])}</p><span class="go">Ler a edição →</span></div><ul>{lis}</ul></a></div></section>'
        )
    arch = "".join(
        f'<li><a href="{url}{e["slug"]}/"><time datetime="{e["data"]}">{br(e["data"])}</time><b>{esc(e["titulo"])}</b><span>Nº {e["n"]}</span></a></li>'
        for e in reversed(eds)
    )
    faq = [
        ("Quanto custa?", "Nada. O boletim é gratuito."),
        (
            "Quando chega?",
            "Todos os dias, por volta das 7h (horário de Brasília), inclusive fins de semana com o resumo dos temas da semana.",
        ),
        (
            "O que vem em cada edição?",
            "Um artigo curto sobre um tema de direito empresarial em evidência e o radar das decisões de STF, STJ, TST, TRFs, TJs e TRTs que afetam empresas, cada uma com o efeito prático e o link da fonte oficial.",
        ),
        ("Como cancelo?", "Todo e-mail traz um link de cancelamento com um clique."),
    ]
    faq_html = "".join(
        f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq
    )
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": url + "#page",
                "url": url,
                "name": NOME,
                "description": desc,
                "inLanguage": "pt-BR",
                "publisher": ORG,
                "hasPart": [
                    {
                        "@type": "NewsArticle",
                        "headline": e["titulo"][:110],
                        "url": f"{url}{e['slug']}/",
                        "datePublished": e["data"],
                    }
                    for e in reversed(eds[-20:])
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in faq
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Início",
                        "item": f"{SITE}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Boletim",
                        "item": url,
                    },
                ],
            },
        ],
    }
    body = (
        '<section class="nl-hero"><div class="nl-wrap"><div>'
        '<p class="nl-eyebrow"><span class="nl-dot" aria-hidden="true"></span>Newsletter gratuita · todo dia às 7h</p>'
        f'<h1>{NOME.replace("Diário", "<em>Diário</em>")}</h1>'
        '<p class="sub">Um artigo de direito empresarial e o radar de STF, STJ, TST, TRFs, TJs e TRTs, explicados para quem decide na empresa. Leitura de 5 minutos.</p>'
        '<ul class="nl-pills"><li><b>Artigo</b> do dia</li><li><b>Radar</b> dos tribunais</li><li><b>Efeito prático</b> para a empresa</li><li>Fonte oficial em cada nota</li></ul>'
        '</div><div class="nl-card" id="inscrever"><h2>Inscreva-se</h2><p class="s">Confirme pelo link que chega no seu e-mail. Cancele com um clique.</p>'
        + form_html(cfg, "boletim-landing")
        + "</div></div></section>"
        f'<div class="nl-ticker" aria-hidden="true"><div class="tr">{tick}{tick}</div></div>'
        '<main class="idx" style="max-width:none;padding:0">'
        '<section class="nl-sec"><div class="nl-wrap"><h2 class="t reveal">O que chega na sua caixa</h2><p class="st reveal">Cada edição tem três partes, sempre na mesma ordem, para você ler em poucos minutos.</p>'
        '<div class="nl-feat"><div class="reveal"><span class="n">01</span><h3>Artigo do dia</h3><p>Um tema de direito empresarial em evidência: sociedades, contratos, tributos, recuperação de empresas, relações de trabalho, mercado de capitais.</p></div>'
        '<div class="reveal"><span class="n">02</span><h3>Radar dos tribunais</h3><p>As decisões mais recentes de STF, STJ, TST, TRFs, TJs e TRTs que mexem com empresas, resumidas em linguagem direta.</p></div>'
        '<div class="reveal"><span class="n">03</span><h3>Efeito prático</h3><p>Para cada decisão, o que muda na rotina da empresa e o link da fonte oficial para conferir.</p></div></div></div></section>'
        + lastcard
        + f'<section class="nl-sec" style="padding-top:0"><div class="nl-wrap"><h2 class="t reveal">Todas as edições</h2><p class="st reveal">Arquivo completo, da mais recente para a mais antiga. Também disponível em <a href="{url}feed.xml">RSS</a>.</p><ul class="nl-arch reveal">{arch}</ul></div></section>'
        f'<section class="nl-sec" style="padding-top:0"><div class="nl-wrap"><div class="faq nl-faq"><h2 class="t">Perguntas frequentes</h2>{faq_html}</div></div></section>'
        f'<section class="nl-sec" style="padding-top:0"><div class="nl-wrap"><div class="cta" style="max-width:760px"><h2>Quer avaliar um tema com a sua empresa?</h2><p>Triagem de 5 minutos pelo WhatsApp, sem custo e sem compromisso.</p><a class="btn" href="{WA}" target="_blank" rel="noopener">Agendar triagem pelo WhatsApp</a></div></div></section>'
        "</main>"
    )
    return page(
        head,
        header,
        footer,
        title=f"{NOME}: direito empresarial e tribunais | Soléo",
        desc=desc,
        canonical=url,
        og_type="website",
        ld=ld,
        body=body,
        og_image=OG,
    )


# ---------------------------------------------------------------- e-mail
def email_html(e):
    url = f"{SITE}/boletim/{e['slug']}/?utm_source=boletim&utm_medium=email&utm_campaign=boletim_{e['data']}"
    news = ""
    for i, n in enumerate(e["noticias"]):
        imp = (
            f'<p style="margin:6px 0 0;font:15px/1.55 Arial,sans-serif;color:#5b4a26;background:#f4ead6;padding:8px 10px;border-radius:4px"><b>Na prática:</b> {esc(n["impacto"])}</p>'
            if n.get("impacto")
            else ""
        )
        news += (
            f'<tr><td style="padding:16px 0;border-top:1px solid #e5e7eb">'
            f'<span style="display:inline-block;font:700 11px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;background:#0b1d40;color:#ffffff;padding:3px 8px;border-radius:999px">{esc(n["tribunal"])}</span>'
            f'<h3 style="margin:8px 0 4px;font:bold 18px/1.35 Georgia,serif;color:#0b1d40">{esc(n["titulo"])}</h3>'
            f'<p style="margin:0;font:15px/1.6 Arial,sans-serif;color:#1f2937">{esc(n["resumo"])}</p>{imp}'
            f'<p style="margin:8px 0 0;font:13px Arial,sans-serif"><a href="{esc(n["fonte"])}" style="color:#86662c">Fonte oficial</a> · <a href="{url}#n{i+1}" style="color:#86662c">Ler no site</a></p></td></tr>'
        )
    secs = e["artigo"]["secoes"][:1]
    first = strip_tags(secs[0]["html"])[:420].rsplit(" ", 1)[0] + "…" if secs else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light"><meta name="robots" content="noindex"><title>{esc(e["assunto"])}</title></head>
<body style="margin:0;padding:0;background:#efe9dc">
<div style="display:none;max-height:0;overflow:hidden">{esc(e.get("preheader", e["descricao"]))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#efe9dc"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#ffffff;border-radius:6px;overflow:hidden">
<tr><td bgcolor="#0b1d40" style="background:#0b1d40;border-bottom:4px solid #c89f54;padding:22px 28px">
<p style="margin:0;font:700 12px Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#e2c48a">{NOME}</p>
<p style="margin:6px 0 0;font:15px Arial,sans-serif;color:#dbe3f0">Edição nº {e["n"]} · {extenso(e["data"])}</p></td></tr>
<tr><td style="padding:26px 28px 8px">
<p style="margin:0 0 14px;font:15px/1.6 Arial,sans-serif;color:#1f2937">Olá{{{{NOME}}}},</p>
<p style="margin:0;font:700 12px Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#86662c">Artigo do dia</p>
<h1 style="margin:6px 0 10px;font:bold 26px/1.25 Georgia,serif;color:#0b1d40">{esc(e["titulo"])}</h1>
<p style="margin:0 0 12px;font:16px/1.6 Arial,sans-serif;color:#1f2937;background:#f4ead6;border-left:4px solid #c89f54;padding:12px 14px">{esc(e["artigo"]["lead"])}</p>
<p style="margin:0 0 18px;font:15px/1.65 Arial,sans-serif;color:#374151">{esc(first)}</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td bgcolor="#c89f54" style="border-radius:4px"><a href="{url}" style="display:inline-block;padding:13px 22px;font:bold 16px Arial,sans-serif;color:#0b1d40;text-decoration:none">Ler a análise completa →</a></td></tr></table>
</td></tr>
<tr><td style="padding:22px 28px 6px"><p style="margin:0 0 4px;font:700 12px Arial,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#86662c">Radar dos tribunais</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{news}</table></td></tr>
<tr><td style="padding:10px 28px 26px"><p style="margin:0;font:15px/1.6 Arial,sans-serif;color:#1f2937">Quer avaliar o efeito de algum desses temas na sua empresa? <a href="{WA}" style="color:#86662c;font-weight:bold">Agende uma triagem de 5 minutos pelo WhatsApp</a>, sem custo.</p>
<p style="margin:18px 0 0;font:15px/1.5 Georgia,serif;color:#0b1d40"><b>Marcos Soléo</b><br><span style="font:14px Arial,sans-serif;color:#4b5563">Consultor empresarial · Soléo Consultoria Empresarial<br><a href="{SITE}/" style="color:#86662c">soleoconsultoria.com.br</a></span></p></td></tr>
<tr><td bgcolor="#0b1220" style="background:#0b1220;padding:18px 28px"><p style="margin:0;font:12px/1.6 Arial,sans-serif;color:#cbd5e1">Você recebe este boletim porque se inscreveu em soleoconsultoria.com.br/boletim. Soléo Consultoria Empresarial · CNPJ 68.804.940/0001-77.<br><a href="{{{{DESCADASTRO}}}}" style="color:#e2c48a">Cancelar inscrição</a> · <a href="{SITE}/boletim/" style="color:#e2c48a">Edições anteriores</a></p></td></tr>
</table></td></tr></table></body></html>
"""


def email_text(e):
    url = f"{SITE}/boletim/{e['slug']}/"
    t = [
        f"{NOME} · Edição nº {e['n']} · {br(e['data'])}",
        "",
        e["titulo"],
        "",
        e["artigo"]["lead"],
        "",
        f"Ler a análise completa: {url}",
        "",
        "RADAR DOS TRIBUNAIS",
    ]
    for n in e["noticias"]:
        t += [
            "",
            f"[{n['tribunal']}] {n['titulo']}",
            n["resumo"],
            f"Fonte: {n['fonte']}",
        ]
    t += [
        "",
        "Marcos Soléo · Consultor empresarial · soleoconsultoria.com.br",
        "",
        "Cancelar inscrição: {{DESCADASTRO}}",
    ]
    return "\n".join(t)


# ---------------------------------------------------------------- feeds / sitemap / robots / menu
def feeds(repo, eds):
    items = []
    for e in reversed(eds[-30:]):
        items.append(
            {
                "id": e["slug"],
                "url": f"{SITE}/boletim/{e['slug']}/",
                "title": e["titulo"],
                "summary": e["descricao"],
                "date_published": e["data"] + "T07:00:00-03:00",
                "_soleo": {
                    "data": e["data"],
                    "n": e["n"],
                    "assunto": e["assunto"],
                    "preheader": e.get("preheader", ""),
                    "email_url": f"{SITE}/boletim/email/{e['slug']}.html",
                    "texto_url": f"{SITE}/boletim/email/{e['slug']}.txt",
                },
            }
        )
    jf = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": NOME,
        "home_page_url": f"{SITE}/boletim/",
        "feed_url": f"{SITE}/boletim/feed.json",
        "language": "pt-BR",
        "authors": [{"name": "Marcos Soléo", "url": f"{SITE}/sobre/"}],
        "items": items,
    }
    (repo / "boletim/feed.json").write_text(
        json.dumps(jf, ensure_ascii=False, indent=1) + "\n"
    )
    rss = "".join(
        f"<item><title>{esc(e['titulo'])}</title><link>{SITE}/boletim/{e['slug']}/</link><guid isPermaLink=\"true\">{SITE}/boletim/{e['slug']}/</guid>"
        f"<pubDate>{dt(e['data']).strftime('%a, %d %b %Y')} 07:00:00 -0300</pubDate><description>{esc(e['descricao'])}</description></item>"
        for e in reversed(eds[-30:])
    )
    (repo / "boletim/feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{NOME} · Soléo Consultoria Empresarial</title>'
        f"<link>{SITE}/boletim/</link><description>Direito empresarial e radar dos tribunais, todo dia às 7h.</description><language>pt-br</language>{rss}</channel></rss>\n"
    )


def sitemap(repo, eds):
    p = repo / "sitemap.xml"
    s = p.read_text()
    s = re.sub(
        r"\s*<url>\s*<loc>" + re.escape(SITE) + r"/boletim/[^<]*</loc>.*?</url>",
        "",
        s,
        flags=re.S,
    )
    today = eds[-1]["data"] if eds else date.today().isoformat()
    add = [(f"{SITE}/boletim/", today, "daily", "0.8")] + [
        (
            f"{SITE}/boletim/{e['slug']}/",
            e.get("atualizado", e["data"]),
            "monthly",
            "0.6",
        )
        for e in reversed(eds)
    ]
    block = "".join(
        f"\n  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n    <changefreq>{c}</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        for u, d, c, pr in add
    )
    s = s.replace("\n</urlset>", block + "\n</urlset>")
    p.write_text(s)


def robots(repo):
    p = repo / "robots.txt"
    s = p.read_text()
    if "/boletim/email/" not in s:
        s = s.replace("Allow: /\n", "Allow: /\nDisallow: /boletim/email/\n", 1)
        p.write_text(s)


def nav_all(repo):
    """Link "Boletim" no menu das páginas pt-BR internas e da home. Idempotente."""
    changed = []
    # Só a home e /artigos/: cada pasta extra vira um commit no upload pela web.
    # Para estender às demais páginas, passe --menu-completo.
    alvos = [repo / "artigos/index.html"]
    if "--menu-completo" in sys.argv:
        alvos += [
            *repo.glob("artigos/*/index.html"),
            repo / "simulador-cbs-ibs/index.html",
            repo / "glossario-reforma-tributaria/index.html",
            repo / "sobre/index.html",
            repo / "exemplo-de-parecer/index.html",
            repo / "politica-de-privacidade/index.html",
        ]
    for f in alvos:
        if not f.exists():
            continue
        s = f.read_text()
        n = nav_patch_str(s)
        if 'id="nl-nav"' not in n:
            n = n.replace("</head>", '<style id="nl-nav">@media(max-width:620px){header.top nav{flex-wrap:nowrap!important}}</style></head>', 1)
        if n != s:
            f.write_text(n)
            changed.append(str(f.relative_to(repo)))
    home = repo / "index.html"
    s = home.read_text()
    if "data-nl-nav" not in s:
        n = s.replace(
            '<a class="lk" href="#guias">Artigos</a>',
            '<a class="lk" href="#guias">Artigos</a>\n          <a class="lk" href="/boletim/" data-nl-nav>Boletim</a>',
            1,
        )
        if n != s:
            home.write_text(n)
            changed.append("index.html")
    return changed


def main():
    repo = Path(sys.argv[1]).resolve()
    cfg = json.loads((repo / "_boletim/config.json").read_text())
    eds = load(repo)
    bad = {e["data"]: qa(e) for e in eds if qa(e)}
    if "--qa" in sys.argv or bad:
        for d, errs in bad.items():
            print(f"QA {d}: " + "; ".join(errs))
        if bad:
            sys.exit(1)
        print(f"QA ok: {len(eds)} edições, 0 termos proibidos")
        return
    parts = base_parts(repo)
    (repo / "boletim/email").mkdir(parents=True, exist_ok=True)
    for i, e in enumerate(eds):
        d = repo / "boletim" / e["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            edition_page(
                e,
                eds[i - 1] if i else None,
                eds[i + 1] if i + 1 < len(eds) else None,
                cfg,
                parts,
            )
        )
        (repo / "boletim/email" / f"{e['slug']}.html").write_text(email_html(e))
        (repo / "boletim/email" / f"{e['slug']}.txt").write_text(email_text(e))
    (repo / "boletim/index.html").write_text(index_page(eds, cfg, parts))
    feeds(repo, eds)
    sitemap(repo, eds)
    robots(repo)
    ch = nav_all(repo)
    print(
        f"ok: {len(eds)} edições · última {eds[-1]['slug'] if eds else '-'} · menu atualizado em {len(ch)} arquivos"
    )


if __name__ == "__main__":
    main()
