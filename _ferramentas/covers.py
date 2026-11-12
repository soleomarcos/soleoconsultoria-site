#!/usr/bin/env python3
"""Gera as capas ilustradas (SVG -> PNG via Chrome -> WebP/JPG).
Uso: python3 covers.py <pasta-saida>
"""

import asyncio
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1200, 630
GOLD, GOLD_L, CREAM, WHITE = "#c89f54", "#e2c48a", "#f4ead6", "#ffffff"
INK = "#0b1d40"

# fundo por categoria: (cor 1, cor 2, cor de destaque secundária)
BG = {
    "rt": ("#0b1d40", "#173a73", "#7fb3ff"),
    "rt2": ("#0e2a4f", "#1d4f7a", "#8fd3ff"),
    "preco": ("#0f3b3d", "#1a6061", "#7ee0c8"),
    "contratos": ("#3d1424", "#6b2740", "#f2a7bd"),
    "credito": ("#0f3524", "#1d5e40", "#8fe3b3"),
    "consult": ("#231d4a", "#3d3480", "#b9adff"),
    "tool": ("#1a2233", "#2e3b57", "#ffd98a"),
}


def frame(cat, body):
    c1, c2, acc = BG[cat]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
 <radialGradient id="glow" cx=".62" cy=".45" r=".55"><stop offset="0" stop-color="{GOLD}" stop-opacity=".35"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.6" fill="#fff" opacity=".07"/></pattern>
 <filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#000" flood-opacity=".35"/></filter>
 <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GOLD_L}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
 <linearGradient id="cream" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="{CREAM}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#dots)"/>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<circle cx="1080" cy="80" r="190" fill="none" stroke="{GOLD}" stroke-opacity=".18" stroke-width="2"/>
<circle cx="110" cy="560" r="150" fill="none" stroke="{acc}" stroke-opacity=".15" stroke-width="2"/>
<g font-family="Inter, Arial, sans-serif" style="--acc:{acc}">{body.replace('ACC', acc)}</g>
</svg>"""


def coin(x, y, r, label, fill="url(#gold)", txt=INK, fs=None):
    fs = fs or int(r * 0.55)
    return (
        f'<g filter="url(#sh)"><circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'
        f'<circle cx="{x}" cy="{y}" r="{r*0.84}" fill="none" stroke="{txt}" stroke-opacity=".25" stroke-width="3"/>'
        f'<text x="{x}" y="{y + fs*0.36}" text-anchor="middle" font-size="{fs}" font-weight="800" fill="{txt}">{label}</text></g>'
    )


def arrow(x1, y1, x2, y2, color=GOLD, w=8):
    import math

    a = math.atan2(y2 - y1, x2 - x1)
    hx, hy = x2 - 26 * math.cos(a), y2 - 26 * math.sin(a)
    p1 = (hx + 16 * math.sin(a), hy - 16 * math.cos(a))
    p2 = (hx - 16 * math.sin(a), hy + 16 * math.cos(a))
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{hx}" y2="{hy}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
        f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>'
    )


def store(x, y, s=1.0, awn=GOLD):
    # loja: telhado com toldo listrado
    w, h = 220 * s, 170 * s
    stripes = "".join(
        f'<rect x="{x + i*w/6:.1f}" y="{y}" width="{w/6:.1f}" height="{42*s:.1f}" fill="{awn if i % 2 == 0 else CREAM}"/>'
        for i in range(6)
    )
    scallops = "".join(
        f'<circle cx="{x + w/12 + i*w/6:.1f}" cy="{y + 42*s:.1f}" r="{w/12:.1f}" fill="{awn if i % 2 == 0 else CREAM}"/>'
        for i in range(6)
    )
    return (
        f'<g filter="url(#sh)"><rect x="{x}" y="{y + 30*s}" width="{w}" height="{h}" rx="6" fill="url(#cream)"/>'
        f"{stripes}{scallops}"
        f'<rect x="{x + 24*s}" y="{y + 95*s}" width="{70*s}" height="{105*s}" rx="4" fill="{INK}" opacity=".85"/>'
        f'<rect x="{x + 116*s}" y="{y + 95*s}" width="{80*s}" height="{55*s}" rx="4" fill="ACC" opacity=".55"/></g>'
    )


def gov(x, y, s=1.0, fill="url(#gold)"):
    # prédio com colunas (fisco)
    w = 230 * s
    cols = "".join(
        f'<rect x="{x + 22*s + i*48*s:.1f}" y="{y + 70*s:.1f}" width="{22*s:.1f}" height="{110*s:.1f}" fill="{fill}"/>'
        for i in range(4)
    )
    return (
        f'<g filter="url(#sh)"><polygon points="{x},{y + 60*s} {x + w/2},{y} {x + w},{y + 60*s}" fill="{fill}"/>'
        f'<rect x="{x}" y="{y + 58*s}" width="{w}" height="{14*s}" fill="{CREAM}"/>{cols}'
        f'<rect x="{x - 10*s}" y="{y + 180*s}" width="{w + 20*s}" height="{18*s}" fill="{CREAM}"/>'
        f'<rect x="{x - 22*s}" y="{y + 198*s}" width="{w + 44*s}" height="{16*s}" fill="{fill}"/></g>'
    )


def doc(x, y, w, h, lines=6, fill="url(#cream)"):
    ls = "".join(
        f'<rect x="{x + 30}" y="{y + 50 + i*34}" width="{(w - 60) * (0.55 if i % 3 == 2 else 0.9):.0f}" height="12" rx="6" fill="{INK}" opacity=".18"/>'
        for i in range(lines)
    )
    return f'<g filter="url(#sh)"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}"/>{ls}</g>'


S = {}

# 1 CBS e IBS: o que são
S["cbs-e-ibs-o-que-sao-e-diferencas"] = (
    "rt",
    "Tributos atuais PIS, Cofins, IPI, ICMS e ISS sendo substituídos por CBS e IBS",
    "".join(
        f'<g opacity=".9"><rect x="250" y="{120 + i*82}" width="210" height="62" rx="31" fill="#fff" opacity=".16"/>'
        f'<text x="355" y="{161 + i*82}" text-anchor="middle" font-size="28" font-weight="700" fill="#fff" opacity=".9">{t}</text>'
        f'<line x1="282" y1="{151 + i*82}" x2="428" y2="{151 + i*82}" stroke="{GOLD}" stroke-width="4" opacity=".9"/></g>'
        for i, t in enumerate(["PIS", "COFINS", "IPI", "ICMS", "ISS"])
    )
    + arrow(500, 315, 610, 315, w=10)
    + coin(770, 250, 118, "CBS")
    + coin(900, 400, 118, "IBS", fill="url(#cream)"),
)

# 2 Alíquota 2026/2027
S["aliquota-cbs-ibs-2026-2027"] = (
    "rt2",
    "Medidor de alíquota com os anos 2026 e 2027",
    f"""
<g filter="url(#sh)"><path d="M380 430 A220 220 0 0 1 820 430" fill="none" stroke="#fff" stroke-opacity=".15" stroke-width="46"/>
<path d="M380 430 A220 220 0 0 1 690 225" fill="none" stroke="url(#gold)" stroke-width="46" stroke-linecap="round"/></g>
<line x1="600" y1="430" x2="705" y2="280" stroke="{CREAM}" stroke-width="12" stroke-linecap="round"/>
<circle cx="600" cy="430" r="26" fill="{CREAM}"/><circle cx="600" cy="430" r="10" fill="{INK}"/>
<text x="600" y="530" text-anchor="middle" font-size="88" font-weight="800" fill="#fff">%</text>
<g filter="url(#sh)"><rect x="140" y="170" width="170" height="190" rx="14" fill="url(#cream)"/><rect x="140" y="170" width="170" height="52" rx="14" fill="{GOLD}"/><rect x="140" y="205" width="170" height="17" fill="{GOLD}"/>
<text x="225" y="300" text-anchor="middle" font-size="46" font-weight="800" fill="{INK}">2026</text></g>
<g filter="url(#sh)"><rect x="890" y="150" width="170" height="190" rx="14" fill="url(#cream)"/><rect x="890" y="150" width="170" height="52" rx="14" fill="ACC"/><rect x="890" y="185" width="170" height="17" fill="ACC"/>
<text x="975" y="280" text-anchor="middle" font-size="46" font-weight="800" fill="{INK}">2027</text></g>""",
)

# 3 Split payment
S["split-payment-reforma-tributaria-quando-comeca"] = (
    "rt",
    "Pagamento dividido: parte segue para a empresa e parte segue direto para o fisco",
    f"""
<g filter="url(#sh)"><rect x="150" y="190" width="250" height="160" rx="18" fill="url(#gold)"/><rect x="150" y="225" width="250" height="34" fill="{INK}" opacity=".7"/>
<rect x="178" y="290" width="60" height="40" rx="6" fill="{CREAM}"/><rect x="300" y="300" width="72" height="12" rx="6" fill="{INK}" opacity=".4"/></g>
<path d="M410 270 C 520 270, 540 160, 660 150" fill="none" stroke="{CREAM}" stroke-width="10" stroke-dasharray="2 22" stroke-linecap="round"/>
<path d="M410 300 C 520 300, 540 430, 660 440" fill="none" stroke="{GOLD}" stroke-width="10" stroke-dasharray="2 22" stroke-linecap="round"/>
{coin(530, 205, 30, "R$", fs=22)}{coin(540, 385, 30, "%", fill="url(#cream)", fs=26)}
{store(690, 40, 0.95)}{gov(700, 340, 0.92)}""",
)

# 4 Simples Nacional
S["reforma-tributaria-simples-nacional-o-que-muda"] = (
    "rt2",
    "Pequena loja diante de uma bifurcação entre dois regimes",
    f"""
{store(160, 170, 1.15, awn="ACC")}
<path d="M520 560 C 600 470, 640 420, 700 390" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="70"/>
<path d="M700 390 C 760 350, 860 300, 1000 290" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="56"/>
<path d="M700 390 C 780 420, 880 470, 1010 470" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="56"/>
<rect x="700" y="130" width="14" height="260" fill="{CREAM}"/>
<g filter="url(#sh)"><polygon points="720,140 900,140 930,175 900,210 720,210" fill="url(#gold)"/><text x="815" y="188" text-anchor="middle" font-size="34" font-weight="800" fill="{INK}">A</text>
<polygon points="694,240 520,240 490,275 520,310 694,310" fill="url(#cream)"/><text x="595" y="288" text-anchor="middle" font-size="34" font-weight="800" fill="{INK}">B</text></g>""",
)

# 5 Cronograma 2026-2033
bars = ""
for i in range(8):
    x = 200 + i * 105
    up = 40 + i * 34
    down = 300 - i * 36
    bars += (
        f'<rect x="{x}" y="{430 - down}" width="34" height="{down}" rx="6" fill="#fff" opacity=".22"/>'
        f'<rect x="{x + 40}" y="{430 - up}" width="34" height="{up}" rx="6" fill="url(#gold)"/>'
        f'<circle cx="{x + 37}" cy="470" r="11" fill="{CREAM if i in (0, 7) else GOLD}"/>'
        f'<text x="{x + 37}" y="520" text-anchor="middle" font-size="26" font-weight="700" fill="#fff" opacity="{1 if i in (0, 7) else .6}">{2026 + i}</text>'
    )
S["cronograma-reforma-tributaria-2026-2033"] = (
    "rt",
    "Linha do tempo de 2026 a 2033 com tributos antigos diminuindo e CBS e IBS crescendo",
    f'<line x1="200" y1="470" x2="1000" y2="470" stroke="#fff" stroke-opacity=".35" stroke-width="5"/>'
    + bars,
)

# 6 Precificar
keys = "".join(
    f'<rect x="{770 + (i % 3)*58}" y="{300 + (i // 3)*52}" width="46" height="40" rx="8" fill="{CREAM if i != 8 else GOLD}" opacity="{.95 if i != 8 else 1}"/>'
    for i in range(9)
)
S["como-precificar-com-cbs-e-ibs"] = (
    "preco",
    "Etiqueta de preço com percentual ao lado de uma calculadora",
    f"""
<g filter="url(#sh)" transform="rotate(-14 420 320)"><path d="M230 230 L520 230 L620 320 L520 410 L230 410 Z" fill="url(#cream)"/>
<circle cx="535" cy="320" r="18" fill="ACC"/><text x="370" y="350" text-anchor="middle" font-size="96" font-weight="800" fill="{INK}">R$</text></g>
<path d="M560 250 C 640 160, 700 170, 740 150" fill="none" stroke="{GOLD}" stroke-width="5"/>
<g filter="url(#sh)"><rect x="745" y="170" width="210" height="330" rx="22" fill="{INK}"/><rect x="770" y="195" width="160" height="80" rx="8" fill="ACC" opacity=".85"/>
<text x="915" y="252" text-anchor="end" font-size="40" font-weight="800" fill="{INK}">%</text>{keys}</g>""",
)

# 7 Contratos
S["contratos-longo-prazo-reforma-tributaria-clausulas"] = (
    "contratos",
    "Contrato com assinatura, selo e caneta, ao lado de um relógio",
    f"""
{doc(300, 90, 380, 460, lines=8)}
<path d="M340 470 c 30 -40, 50 30, 80 -10 s 40 30, 70 -20 s 30 20, 60 0" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
<g filter="url(#sh)"><circle cx="610" cy="470" r="52" fill="url(#gold)"/><circle cx="610" cy="470" r="36" fill="none" stroke="{INK}" stroke-opacity=".35" stroke-width="4"/>
<path d="M590 470 l14 14 l26 -30" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></g>
<g filter="url(#sh)" transform="rotate(38 760 330)"><rect x="740" y="140" width="40" height="300" rx="20" fill="url(#gold)"/><polygon points="740,440 780,440 760,500" fill="{CREAM}"/></g>
<g filter="url(#sh)"><circle cx="920" cy="230" r="95" fill="url(#cream)"/><circle cx="920" cy="230" r="80" fill="none" stroke="ACC" stroke-width="6"/>
<line x1="920" y1="230" x2="920" y2="170" stroke="{INK}" stroke-width="9" stroke-linecap="round"/><line x1="920" y1="230" x2="965" y2="255" stroke="{INK}" stroke-width="9" stroke-linecap="round"/></g>""",
)


# 8 Crédito de CBS e IBS (cadeia)
def factory(x, y):
    return (
        f'<g filter="url(#sh)"><rect x="{x}" y="{y + 60}" width="170" height="110" rx="6" fill="url(#cream)"/>'
        f'<polygon points="{x},{y + 60} {x + 57},{y + 25} {x + 57},{y + 60} {x + 113},{y + 25} {x + 113},{y + 60} {x + 170},{y + 25} {x + 170},{y + 60}" fill="url(#cream)"/>'
        f'<rect x="{x + 120}" y="{y - 30}" width="28" height="70" fill="{GOLD}"/>'
        f'<rect x="{x + 30}" y="{y + 100}" width="40" height="70" fill="{INK}" opacity=".8"/></g>'
    )


def truck(x, y):
    return (
        f'<g filter="url(#sh)"><rect x="{x}" y="{y + 40}" width="150" height="100" rx="8" fill="url(#gold)"/>'
        f'<path d="M{x + 150} {y + 70} h50 l30 35 v35 h-80 z" fill="url(#cream)"/>'
        f'<circle cx="{x + 40}" cy="{y + 145}" r="22" fill="{INK}"/><circle cx="{x + 190}" cy="{y + 145}" r="22" fill="{INK}"/></g>'
    )


S["credito-de-cbs-e-ibs-como-funciona"] = (
    "rt2",
    "Cadeia de fábrica, transporte e loja com créditos passando entre as etapas",
    factory(120, 300)
    + arrow(320, 400, 400, 400, color=CREAM)
    + truck(420, 300)
    + arrow(680, 400, 760, 400, color=CREAM)
    + store(780, 255, 0.95, awn="ACC")
    + coin(205, 180, 50, "+", fs=60)
    + coin(535, 180, 50, "+", fs=60)
    + coin(885, 150, 50, "+", fs=60)
    + '<path d="M255 180 C 350 120, 420 120, 485 180" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="5" stroke-dasharray="10 12"/>'
    + '<path d="M585 180 C 680 110, 760 100, 835 150" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="5" stroke-dasharray="10 12"/>',
)

# 9 Consultoria
chk = "".join(
    f'<rect x="760" y="{215 + i*62}" width="34" height="34" rx="8" fill="{GOLD}"/><path d="M768 {232 + i*62} l8 8 l14 -16" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
    f'<rect x="808" y="{224 + i*62}" width="{150 - i*25}" height="14" rx="7" fill="{INK}" opacity=".25"/>'
    for i in range(4)
)
S["consultoria-reforma-tributaria-para-empresas"] = (
    "consult",
    "Quadro de apresentação com gráfico em alta e lista de verificação",
    f"""
<g filter="url(#sh)"><rect x="230" y="150" width="760" height="340" rx="14" fill="url(#cream)"/></g>
<line x1="610" y1="490" x2="530" y2="590" stroke="{CREAM}" stroke-width="12"/><line x1="610" y1="490" x2="690" y2="590" stroke="{CREAM}" stroke-width="12"/>
{''.join(f'<rect x="{290 + i*85}" y="{430 - h}" width="56" height="{h}" rx="6" fill="{c}"/>' for i, (h, c) in enumerate([(80, "ACC"), (130, "ACC"), (170, "ACC"), (240, GOLD)]))}
<polyline points="318,330 403,280 488,240 573,170" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="573" cy="170" r="12" fill="{INK}"/>{chk}""",
)

# 10 Financiamento x capital de giro (balança)
stack = "".join(
    f'<ellipse cx="930" cy="{360 - i*22}" rx="70" ry="18" fill="url(#gold)" stroke="{INK}" stroke-opacity=".25" stroke-width="3"/>'
    for i in range(6)
)
S["financiamento-ou-capital-de-giro-custo-total"] = (
    "credito",
    "Balança comparando um banco e uma pilha de moedas",
    f"""
<rect x="590" y="140" width="20" height="380" fill="{CREAM}"/><polygon points="520,540 680,540 640,500 560,500" fill="url(#gold)"/>
<g transform="rotate(-6 600 150)"><rect x="250" y="140" width="700" height="16" rx="8" fill="url(#gold)"/>
<line x1="300" y1="156" x2="250" y2="380" stroke="{CREAM}" stroke-width="4"/><line x1="300" y1="156" x2="350" y2="380" stroke="{CREAM}" stroke-width="4"/>
<line x1="900" y1="156" x2="850" y2="380" stroke="{CREAM}" stroke-width="4"/><line x1="900" y1="156" x2="950" y2="380" stroke="{CREAM}" stroke-width="4"/></g>
<circle cx="600" cy="140" r="22" fill="{CREAM}"/>
{gov(190, 205, 0.62, fill="url(#cream)")}<path d="M210 395 h180 a90 30 0 0 1 -180 0 z" fill="ACC" opacity=".8"/>
{stack}<path d="M840 385 h180 a90 30 0 0 1 -180 0 z" fill="ACC" opacity=".8"/>""",
)

# 11 2026 ano de teste
S["cbs-e-ibs-2026-ano-de-teste"] = (
    "rt",
    "Calendário de 2026 com selo de teste aprovado",
    f"""
<g filter="url(#sh)"><rect x="300" y="110" width="420" height="420" rx="22" fill="url(#cream)"/><rect x="300" y="110" width="420" height="96" rx="22" fill="url(#gold)"/><rect x="300" y="180" width="420" height="26" fill="url(#gold)"/>
<text x="510" y="182" text-anchor="middle" font-size="58" font-weight="800" fill="{INK}">2026</text></g>
{''.join(f'<rect x="{335 + (i % 6)*60}" y="{235 + (i // 6)*58}" width="44" height="40" rx="6" fill="{INK}" opacity="{.12 if i != 15 else .9}"/>' for i in range(24))}
<g filter="url(#sh)"><circle cx="790" cy="420" r="110" fill="ACC"/><circle cx="790" cy="420" r="88" fill="none" stroke="{INK}" stroke-opacity=".3" stroke-width="6" stroke-dasharray="8 10"/>
<path d="M745 420 l32 32 l60 -66" fill="none" stroke="{INK}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/></g>""",
)

# 12 Nota fiscal
zig = " ".join(f"{850 - i*25},{560 if i % 2 == 0 else 540}" for i in range(21))
S["cbs-e-ibs-na-nota-fiscal-campos-cst"] = (
    "rt2",
    "Nota fiscal com os campos de CBS, IBS e CST destacados por uma lupa",
    f"""
<g filter="url(#sh)"><polygon points="350,70 850,70 {zig}" fill="url(#cream)"/></g>
{''.join(f'<rect x="390" y="{120 + i*40}" width="{360 if i % 2 else 260}" height="14" rx="7" fill="{INK}" opacity=".18"/>' for i in range(4))}
<rect x="370" y="290" width="460" height="64" rx="8" fill="url(#gold)"/>
<text x="400" y="333" font-size="30" font-weight="800" fill="{INK}">CST</text><text x="520" y="333" font-size="30" font-weight="800" fill="{INK}">CBS</text><text x="640" y="333" font-size="30" font-weight="800" fill="{INK}">IBS</text>
{''.join(f'<rect x="{390 + i*11}" y="430" width="{4 if i % 3 else 7}" height="70" fill="{INK}" opacity=".75"/>' for i in range(38))}
<g filter="url(#sh)"><circle cx="830" cy="300" r="105" fill="#fff" fill-opacity=".18" stroke="{CREAM}" stroke-width="18"/>
<line x1="905" y1="375" x2="1010" y2="480" stroke="{GOLD}" stroke-width="32" stroke-linecap="round"/></g>""",
)

# 13 Prestadores de serviços
S["reforma-tributaria-prestadores-de-servicos"] = (
    "rt",
    "Notebook com gráfico, maleta e engrenagem representando empresas de serviços",
    f"""
<g filter="url(#sh)"><rect x="220" y="140" width="460" height="300" rx="16" fill="{INK}" stroke="{CREAM}" stroke-width="12"/>
<polygon points="170,450 730,450 690,490 210,490" fill="url(#cream)"/></g>
{''.join(f'<rect x="{270 + i*90}" y="{400 - h}" width="54" height="{h}" rx="6" fill="{c}"/>' for i, (h, c) in enumerate([(90, "ACC"), (150, "ACC"), (120, "ACC"), (210, GOLD)]))}
<g filter="url(#sh)"><rect x="760" y="300" width="260" height="190" rx="18" fill="url(#gold)"/><rect x="840" y="265" width="100" height="45" rx="12" fill="none" stroke="{GOLD}" stroke-width="14"/>
<rect x="760" y="370" width="260" height="14" fill="{INK}" opacity=".35"/><rect x="872" y="358" width="36" height="38" rx="6" fill="{CREAM}"/></g>
<g filter="url(#sh)" transform="translate(870 170)">{''.join(f'<rect x="-14" y="-78" width="28" height="40" rx="5" fill="{CREAM}" transform="rotate({a})"/>' for a in range(0, 360, 45))}
<circle r="56" fill="{CREAM}"/><circle r="22" fill="{INK}"/></g>""",
)

# 14 Simulador
S["simulador"] = (
    "tool",
    "Calculadora e gráfico de barras para simular CBS e IBS",
    f"""
<g filter="url(#sh)"><rect x="250" y="110" width="300" height="420" rx="28" fill="{CREAM}"/><rect x="280" y="140" width="240" height="100" rx="12" fill="{INK}"/>
<text x="500" y="210" text-anchor="end" font-size="52" font-weight="800" fill="ACC">0,9%</text>
{''.join(f'<rect x="{285 + (i % 4)*60}" y="{265 + (i // 4)*62}" width="48" height="48" rx="10" fill="{GOLD if i in (3, 7, 11, 15) else INK}" opacity="{1 if i in (3, 7, 11, 15) else .2}"/>' for i in range(16))}</g>
<g filter="url(#sh)"><rect x="640" y="160" width="360" height="330" rx="18" fill="url(#cream)"/></g>
{''.join(f'<rect x="{680 + i*76}" y="{450 - h}" width="50" height="{h}" rx="6" fill="{c}"/>' for i, (h, c) in enumerate([(120, INK), (180, INK), (150, GOLD), (240, GOLD)]))}""",
)

# 15 Glossário
S["glossario"] = (
    "tool",
    "Livro aberto com as letras A e Z",
    f"""
<g filter="url(#sh)"><path d="M600 200 C 500 150, 340 150, 230 190 L230 500 C 340 460, 500 460, 600 510 Z" fill="url(#cream)"/>
<path d="M600 200 C 700 150, 860 150, 970 190 L970 500 C 860 460, 700 460, 600 510 Z" fill="#fff"/></g>
<line x1="600" y1="200" x2="600" y2="510" stroke="{INK}" stroke-opacity=".25" stroke-width="4"/>
{''.join(f'<rect x="{290 if s < 0 else 650}" y="{300 + i*36}" width="{240 - (i % 2)*60}" height="12" rx="6" fill="{INK}" opacity=".18"/>' for s in (-1, 1) for i in range(4))}
<text x="400" y="285" text-anchor="middle" font-size="96" font-weight="800" font-family="Georgia, serif" fill="{INK}">A</text>
<text x="800" y="285" text-anchor="middle" font-size="96" font-weight="800" font-family="Georgia, serif" fill="{GOLD}">Z</text>
<polygon points="870,150 910,150 910,250 890,230 870,250" fill="ACC"/>""",
)

# 16 Serviço (consultoria internacional)
S["servico"] = (
    "consult",
    "Escudo com marca de verificação sobre um gráfico em alta",
    f"""
<polyline points="200,480 380,400 520,430 700,300 860,330 1010,190" fill="none" stroke="ACC" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>
<circle cx="1010" cy="190" r="16" fill="ACC"/>
<g filter="url(#sh)"><path d="M600 110 L790 170 C 790 360, 720 470, 600 530 C 480 470, 410 360, 410 170 Z" fill="url(#gold)"/>
<path d="M600 150 L755 198 C 752 350, 695 440, 600 490 C 505 440, 448 350, 445 198 Z" fill="none" stroke="{INK}" stroke-opacity=".3" stroke-width="5"/>
<path d="M530 320 l50 50 l95 -105" fill="none" stroke="{INK}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/></g>""",
)


async def render():
    from playwright.async_api import async_playwright
    from PIL import Image

    async with async_playwright() as p:
        b = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]
        )
        pg = await b.new_page(viewport={"width": W, "height": H})
        for slug, (cat, alt, body) in S.items():
            svg = frame(cat, body)
            (OUT / f"{slug}.svg").write_text(svg)
            await pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            png = OUT / f"{slug}.png"
            await pg.screenshot(
                path=str(png), clip={"x": 0, "y": 0, "width": W, "height": H}
            )
            im = Image.open(png).convert("RGB")
            im.save(OUT / f"{slug}.webp", "WEBP", quality=82, method=6)
            im.save(
                OUT / f"{slug}.jpg", "JPEG", quality=84, optimize=True, progressive=True
            )
            im.resize((640, 336), Image.LANCZOS).save(
                OUT / f"{slug}-640.webp", "WEBP", quality=80, method=6
            )
            png.unlink()
        await b.close()
    (OUT / "alts.tsv").write_text("\n".join(f"{k}\t{v[1]}" for k, v in S.items()))


asyncio.run(render())
print(len(S), "capas")
