# Boletim Empresarial Diário

Pasta não publicada (o Jekyll do GitHub Pages ignora pastas com `_`).

## Arquitetura (somente Google Workspace + GitHub Pages)

| Peça | Onde | Função |
|---|---|---|
| Edição (JSON) | `_boletim/edicoes/AAAA-MM-DD.json` | Fonte de cada edição |
| Gerador | `_ferramentas/boletim.py` | JSON → páginas, e-mail, feeds, sitemap |
| Página da newsletter | `/boletim/` | Inscrição + arquivo de edições |
| Edição no site | `/boletim/<slug>/` | Artigo do dia + radar dos tribunais |
| E-mail | `/boletim/email/<slug>.html` e `.txt` | Corpo enviado (placeholders `{{NOME}}`, `{{DESCADASTRO}}`); bloqueado no robots.txt |
| Feed | `/boletim/feed.json` (lido pelo Apps Script) e `/boletim/feed.xml` (RSS) | |
| Inscrição e envio | Apps Script "Boletim Empresarial Diário · inscrição e envio" na conta atendimento@ (código em `apps_script/Codigo.gs`) | Web app recebe inscrições (POST), confirma (dupla confirmação), descadastra; gatilho de 30 em 30 min envia a edição do dia aos inscritos ativos via Gmail de atendimento@ |
| Inscritos | Planilha "Boletim Empresarial Diário · Inscritos" (Drive de atendimento@, compartilhada com marcos@) | abas `Inscritos` e `Envios` |

## Esquema da edição

```json
{
  "data": "AAAA-MM-DD",
  "slug": "AAAA-MM-DD-palavras-chave",
  "tema": "Área do artigo",
  "titulo": "Título do artigo do dia (até ~90 caracteres)",
  "descricao": "Meta description (até ~160 caracteres)",
  "assunto": "Assunto do e-mail (até ~60 caracteres)",
  "preheader": "Pré-visualização do e-mail",
  "artigo": {"lead": "Resumo de 2-3 frases", "secoes": [{"h2": "Subtítulo", "html": "<p>…</p>"}]},
  "noticias": [{"tribunal": "STF|STJ|TST|TRF-n|TJXX|TRT-n|CARF|CVM|CADE", "tema": "…", "data": "AAAA-MM-DD",
                "titulo": "…", "resumo": "…", "impacto": "…", "fonte": "https://…", "fonte_nome": "…"}],
  "fontes": [{"nome": "…", "url": "https://…"}]
}
```

## Rotina diária

1. `git clone https://github.com/soleomarcos/soleoconsultoria-site.git`
2. Escrever `_boletim/edicoes/<hoje>.json`.
3. `python3 _ferramentas/boletim.py <repo> --qa` (zero termos proibidos) e `python3 _ferramentas/boletim.py <repo>`.
4. Subir pela web do GitHub, nesta ordem (uma pasta por commit): `_boletim/edicoes`, `boletim/<slug>`, `boletim/email`, raiz (`sitemap.xml`), e por último `boletim` (`index.html`, `feed.json`, `feed.xml`) — o feed dispara o envio.
5. Conferir no ar (SHA-256 e render 390/1440 px). O Apps Script envia em até 30 min.
