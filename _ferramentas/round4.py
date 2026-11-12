#!/usr/bin/env python3
"""Rodada 4 (auditoria SearchFit 12/11/2026). Idempotente. Uso: round4.py <repo>"""
import re,sys,os
R=sys.argv[1]; B='https://www.soleoconsultoria.com.br'
def rd(p): return open(os.path.join(R,p),encoding='utf-8').read()
def wr(p,s): open(os.path.join(R,p),'w',encoding='utf-8').write(s)
log=[]
def sub(p,old,new,count=1):
    s=rd(p)
    if new in s and old not in s: return
    if old not in s: log.append(f'FALTA {p}: {old[:50]}'); return
    wr(p,s.replace(old,new,count)); log.append(f'ok {p}')

# 1. titles das homes (og/twitter junto)
T={'index.html':('Soléo Consultoria Empresarial | Reforma Tributária no Brasil','Consultoria em Reforma Tributária, contratos e crédito | Soléo'),
 'pt-pt/index.html':('Soléo Consultoria Empresarial | Reforma Tributária no Brasil','Reforma Tributária no Brasil: consultoria e contratos | Soléo'),
 'en/index.html':('Soléo Business Consulting | Brazil Tax Reform Advisory','Brazil Tax Reform Consulting, Contracts and Credit | Soléo'),
 'es/index.html':('Soléo Consultoría Empresarial | Reforma Tributaria en Brasil','Consultoría en Reforma Tributaria, contratos y crédito | Soléo')}
for p,(o,n) in T.items():
    s=rd(p)
    if o in s: wr(p,s.replace(o,n)); log.append('title '+p)

# 2. rodapé h4 -> h3 (CSS acompanha)
for p in ['index.html','pt-pt/index.html','en/index.html','es/index.html']:
    s=rd(p)
    if '<h4>' in s:
        s=s.replace('<h4>','<h3>').replace('</h4>','</h3>').replace('footer h4{','footer h3{'); wr(p,s); log.append('h4 '+p)

# 3. artigo de consultoria: dono do termo comercial é a home
A='artigos/consultoria-reforma-tributaria-para-empresas/index.html'
s=rd(A); o='Consultoria em Reforma Tributária: quando contratar'; n='Como contratar consultoria em Reforma Tributária: critérios'
if o in s: wr(A,s.replace(o,n)); log.append('artigo titulo')
s=rd(A)
if 'class="see"' not in s:
    wr(A,s.replace('<section class="src">',f'<p class="see">Para conhecer o atendimento completo, veja a página de <a href="{B}/">consultoria em Reforma Tributária</a> da Soléo e use o <a href="{B}/simulador-cbs-ibs/">simulador de CBS e IBS</a>.</p><section class="src">',1)); log.append('artigo link home')

# 4. links contextuais entre artigos
F=f'<a href="{B}/artigos/financiamento-ou-capital-de-giro-custo-total/">financiamento ou capital de giro: como comparar o custo</a>'
N=f'<a href="{B}/artigos/cbs-e-ibs-na-nota-fiscal-campos-cst/">CBS e IBS na nota fiscal: campos e CST</a>'
add={'artigos/como-precificar-com-cbs-e-ibs/index.html':f'Veja também: {F}.',
 'artigos/credito-de-cbs-e-ibs-como-funciona/index.html':f'Veja também: {F} e {N}.',
 'artigos/split-payment-reforma-tributaria-quando-comeca/index.html':f'Veja também: {F} e {N}.',
 'artigos/cronograma-reforma-tributaria-2026-2033/index.html':f'Veja também: {N}.',
 'artigos/cbs-e-ibs-2026-ano-de-teste/index.html':f'Veja também: {N}.'}
for p,t in add.items():
    s=rd(p)
    if 'class="see"' in s: continue
    wr(p,s.replace('<section class="src">',f'<p class="see">{t}</p><section class="src">',1)); log.append('see '+p)

# 5. links entre versões de idioma
def li(p,items):
    s=rd(p)
    if items[0][0] in s.split('<section class="rel">')[-1] if '<section class="rel">' in s else False: return
    if '<section class="rel"><h2>' not in s: log.append('SEM rel '+p); return
    k=s.find('</ul>',s.find('<section class="rel">'))
    ins=''.join(f'<li><a href="{B}{u}">{t}</a></li>' for u,t in items)
    wr(p,s[:k]+ins+s[k:]); log.append('rel '+p)
li('simulador-cbs-ibs/index.html',[('/en/cbs-ibs-simulator/','CBS and IBS simulator (English)'),('/es/simulador-cbs-ibs/','Simulador de CBS e IBS (español)'),('/en/brazil-tax-reform-consulting/','Brazil tax reform consulting (English)'),('/es/consultoria-reforma-tributaria-brasil/','Consultoría sobre la Reforma Tributaria (español)')])
li('en/cbs-ibs-simulator/index.html',[('/es/simulador-cbs-ibs/','Simulador de CBS e IBS (español)'),('/simulador-cbs-ibs/','Simulador de CBS e IBS (português)')])
li('es/simulador-cbs-ibs/index.html',[('/en/cbs-ibs-simulator/','CBS and IBS simulator (English)'),('/simulador-cbs-ibs/','Simulador de CBS e IBS (português)')])
for p in ['en/brazil-tax-reform-consulting/index.html','es/consultoria-reforma-tributaria-brasil/index.html']:
    s=rd(p); print(p,'rel' if '<section class="rel">' in s else 'SEM rel')

# 6. sitemap: image depois de priority; lastmod por página = data real
x=rd('sitemap.xml')
def fix(m):
    b=m.group(0)
    imgs=re.findall(r'\s*<image:image>.*?</image:image>',b,re.S)
    if not imgs: return b
    for i in imgs: b=b.replace(i,'')
    return b.replace('</url>',''.join(i if i.startswith('\n') else '\n    '+i.strip() for i in imgs)+'\n  </url>')
y=re.sub(r'<url>.*?</url>',fix,x,flags=re.S)
if y!=x: wr('sitemap.xml',y); log.append('sitemap ordem')
print('\n'.join(log))

# 7. datas coerentes: dateModified = lastmod; só muda o que teve conteúdo alterado
ch=['consultoria-reforma-tributaria-para-empresas','como-precificar-com-cbs-e-ibs','credito-de-cbs-e-ibs-como-funciona','split-payment-reforma-tributaria-quando-comeca','cronograma-reforma-tributaria-2026-2033','cbs-e-ibs-2026-ano-de-teste']
for sl in ch:
    p=f'artigos/{sl}/index.html'; s=rd(p)
    s2=s.replace('"dateModified": "2026-11-11"','"dateModified": "2026-11-12"').replace('Publicado e atualizado em 11/11/2026','Publicado em 11/11/2026 · Atualizado em 12/11/2026')
    if s2!=s: wr(p,s2); log.append('data '+sl)
x=rd('sitemap.xml'); keep=set(f'{B}/artigos/{s}/' for s in ch)|{f'{B}/',f'{B}/pt-pt/',f'{B}/en/',f'{B}/es/',f'{B}/artigos/',f'{B}/politica-de-privacidade/',f'{B}/sobre/',f'{B}/exemplo-de-parecer/'}
def lm(m):
    b=m.group(0); u=re.search(r'<loc>(.*?)</loc>',b).group(1)
    if u in keep: return b
    return b.replace('<lastmod>2026-11-12</lastmod>','<lastmod>2026-11-11</lastmod>')
y=re.sub(r'<url>.*?</url>',lm,x,flags=re.S)
y=re.sub(r'\n\s*\n','\n',y)
if y!=x: wr('sitemap.xml',y); log.append('sitemap lastmod')
print('\n'.join(l for l in log if l.startswith(('data','sitemap'))))

# 8. favicon: .ico + PNG 48/96/192 (gerados de brasao.png), declarados em todas as páginas
import glob
OLD='<link rel="icon" type="image/png" href="https://www.soleoconsultoria.com.br/favicon.png"'
NEW=(f'<link rel="icon" href="{B}/favicon.ico" sizes="48x48">'
     f'<link rel="icon" type="image/png" sizes="48x48" href="{B}/favicon-48.png">'
     f'<link rel="icon" type="image/png" sizes="96x96" href="{B}/favicon-96.png">'
     f'<link rel="icon" type="image/png" sizes="192x192" href="{B}/favicon-192.png">'
     f'<link rel="apple-touch-icon" href="{B}/favicon-192.png">')
n=0
for p in glob.glob(os.path.join(R,'**/index.html'),recursive=True)+[os.path.join(R,'404.html')]:
    if '_ferramentas' in p or not os.path.exists(p): continue
    s=open(p,encoding='utf-8').read()
    if 'favicon-192.png' in s or OLD not in s: continue
    s=re.sub(re.escape(OLD)+r'\s*/?>',NEW,s,count=1); open(p,'w',encoding='utf-8').write(s); n+=1
print('favicon em',n,'paginas')

# 9. páginas de serviço EN/ES: links cruzados e para o simulador
li('en/brazil-tax-reform-consulting/index.html',[('/es/consultoria-reforma-tributaria-brasil/','Consultoría sobre la Reforma Tributaria (español)'),('/en/cbs-ibs-simulator/','CBS and IBS simulator')])
li('es/consultoria-reforma-tributaria-brasil/index.html',[('/en/brazil-tax-reform-consulting/','Brazil tax reform consulting (English)'),('/es/simulador-cbs-ibs/','Simulador de CBS e IBS')])
