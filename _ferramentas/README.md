# Ferramentas de manutenção do site

Pasta não publicada: o GitHub Pages (Jekyll) ignora pastas que começam com `_`.

Os HTML publicados são a fonte de verdade. Estes scripts aplicam patches sobre eles. Todos são idempotentes: cada um procura o próprio marcador e não aplica de novo o que já existe. Se alguma página for regenerada por outro gerador, basta rodar de novo, nesta ordem:

| Ordem | Script | O que faz | Marcador no HTML |
|---|---|---|---|
| 1 | `uxfix.py <repo>` | Homes (4 idiomas): menu mobile, contraste AA, CTAs, rodapé em colunas, H1 fixo | `<style id="ux-fix">` |
| 2 | `covers.py <pasta>` | Gera as 16 capas (SVG → WebP 1200/640 + JPG) e `alts.tsv`. Requer Playwright e Chrome | — |
| 3 | `pages.py <repo> <pasta-capas>` | Capas e cards nos artigos e em /artigos/, og:image, cards na seção Guias das homes, contraste e toque nas internas | `<style id="cards-img">`, `<style id="gcards">` |
| 4 | `round3.py <repo>` | Home compacta no celular (carrosséis, 4 guias), idioma dos cards EN/ES, capas no sitemap | `<style id="mob-compact">` |
| 5 | `round4.py <repo>` | Auditoria SearchFit: titles das homes, h4→h3 no rodapé, links contextuais, links entre idiomas, ordem e lastmod do sitemap, dateModified, favicon (.ico + PNG 48/96/192, gerados de `brasao.png`) | `class="see"`, `favicon-192.png` |
| — | `audit_local.py` | Auditoria de todas as páginas em 390px e 1440px: contraste AA, alvos de toque, erros de JS, imagens quebradas, rolagem lateral | — |

Capas publicadas: `/img/capas/<slug>.webp`, `<slug>-640.webp`, `<slug>.jpg`.

## Publicação
- Uma sessão de publicação por vez. Antes de subir um arquivo, compare o remoto com a sua base: `git fetch origin main && git diff <base> origin/main -- <arquivo>`. Se mudou, refaça o patch em cima da versão nova.
- Depois de publicar, confira o hash do site no ar contra o do repositório.
