# Implementar índices de conteúdo do Maintor CMMS

> **For Codex:** execute este plano em sequência com `executing-plans` e TDD. Não alterar layout ou copy da landing.

**Objetivo:** publicar índices navegáveis e indexáveis para Blog e Calculadoras, elevar o sitemap a 36 URLs e corrigir as referências de domínio da landing sem alterar sua apresentação.

**Arquitetura:** manter o site como HTML estático sem dependências de build. Os índices reutilizam a identidade visual existente e expõem metadados SEO próprios. Um teste Python com biblioteca padrão valida o contrato entre arquivos, links, canonical e sitemap.

**Stack:** HTML5, CSS estático, XML sitemap, Python 3 `unittest`, GitHub Pages.

---

## Tarefa 1: criar o contrato estrutural do site

**Arquivos:**

- Criar: `tests/test_site_structure.py`

**Passo 1: escrever testes inicialmente vermelhos**

Cobrir:

- `blog/index.html` e `calculadoras/index.html` devem existir;
- o índice do blog deve ligar os 7 artigos existentes;
- o índice de calculadoras deve ligar as 4 ferramentas existentes;
- cada índice deve ter title, description, H1, canonical, `og:url` e CTA em `app.maintor.com.br`;
- o sitemap deve conter exatamente 36 URLs únicas;
- cada URL do sitemap deve resolver para um HTML local e ter canonical idêntico;
- nenhum HTML/XML de produção deve conter o host antigo do GitHub ou `/flow`.

**Passo 2: executar e confirmar a falha esperada**

Executar: `python3 -m unittest discover -s tests -v`

Esperado: falhas por ausência de `blog/index.html` e `calculadoras/index.html`, sitemap ainda com 34 URLs e host antigo presente na landing.

**Passo 3: commit do teste**

```bash
git add tests/test_site_structure.py
git commit -m "test: define static content publishing contract"
```

## Tarefa 2: implementar o índice do Blog

**Arquivos:**

- Criar: `blog/index.html`
- Testar: `tests/test_site_structure.py`

**Passo 1: implementar a página mínima completa**

Adicionar metadados para `https://maintor.com.br/blog/`, navegação, introdução, 7 cards com títulos/descrições reais, JSON-LD `ItemList`, CTA do app e rodapé.

**Passo 2: executar os testes focados**

Executar: `python3 -m unittest tests.test_site_structure.SiteStructureTests.test_blog_index -v`

Esperado: PASS.

## Tarefa 3: implementar o índice de Calculadoras

**Arquivos:**

- Criar: `calculadoras/index.html`
- Testar: `tests/test_site_structure.py`

**Passo 1: implementar a página mínima completa**

Adicionar metadados para `https://maintor.com.br/calculadoras/`, navegação, introdução, 4 cards, JSON-LD `ItemList`, CTA do app e rodapé.

**Passo 2: executar os testes focados**

Executar: `python3 -m unittest tests.test_site_structure.SiteStructureTests.test_calculators_index -v`

Esperado: PASS.

## Tarefa 4: integrar sitemap e corrigir URLs da landing

**Arquivos:**

- Modificar: `sitemap.xml`
- Modificar: `index.html`
- Testar: `tests/test_site_structure.py`

**Passo 1: atualizar o sitemap**

Adicionar `/blog/` e `/calculadoras/` com `lastmod` de `2026-08-25`, mantendo as 34 entradas atuais e `/flow` ausente.

**Passo 2: normalizar a landing**

Substituir somente `https://victoreduardodelavor.github.io/maintor-site` por `https://maintor.com.br`. Confirmar pelo diff que nenhuma outra linha mudou.

**Passo 3: executar toda a suíte**

Executar: `python3 -m unittest discover -s tests -v`

Esperado: todos os testes passam.

**Passo 4: validações estáticas adicionais**

Executar:

```bash
git diff --check
rg -n "victoreduardodelavor.github.io/maintor-site|maintor.com.br/flow" --glob '*.html' --glob '*.xml' .
```

Esperado: sem erros e sem ocorrências.

**Passo 5: commit da implementação**

```bash
git add index.html blog/index.html calculadoras/index.html sitemap.xml
git commit -m "feat: add blog and calculator indexes"
```

## Tarefa 5: revisar e publicar

**Arquivos:**

- Revisar: `index.html`
- Revisar: `blog/index.html`
- Revisar: `calculadoras/index.html`
- Revisar: `sitemap.xml`

**Passo 1: revisar o diff e o conteúdo renderizado**

Confirmar que a landing difere do baseline apenas por URLs. Servir o worktree localmente e inspecionar os dois novos índices em desktop e viewport móvel.

**Passo 2: integrar no `main` sem force push**

Buscar `origin/main`, confirmar que não divergiu, avançar `main` para a branch e executar `git push origin main`.

**Passo 3: aguardar GitHub Pages**

Consultar o build mais recente até que o commit publicado esteja com status `built`.

**Passo 4: verificar produção**

Confirmar:

- HTTP 200 e canonical correto em `/`, `/blog/`, `/calculadoras/` e amostras internas;
- sitemap com 36 URLs únicas e cada URL respondendo 200;
- HTTP 404 em `/flow`;
- `app.maintor.com.br` servindo o Base44;
- webhook protegido respondendo erro de assinatura quando chamado sem assinatura;
- A/AAAA/CNAME do site e todos os MX, SPF, DKIM, DMARC, autodiscover e autoconfig preservados.
