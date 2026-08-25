# Índices de conteúdo do Maintor CMMS — Especificação de design

**Data:** 2026-08-25  
**Status:** aprovado conceitualmente; aguardando revisão desta especificação  
**Escopo:** site estático publicado pelo GitHub Pages em `maintor.com.br`

## Contexto

O domínio raiz passou do Base44 para o GitHub Pages para publicar o conteúdo do Maintor CMMS. As 34 URLs existentes estão acessíveis e entregam conteúdo distinto, mas os links de navegação `/blog` e `/calculadoras` retornam 404 porque esses diretórios não têm `index.html`.

A landing exibida na raiz é a versão CMMS presente no `main`. O histórico mostra que o commit `c9c2f7f` colocou temporariamente a landing Maintor Flow na home em 2026-08-20 e que o commit `9bb92a3`, 15 minutos depois, restaurou integralmente a landing CMMS. A virada de DNS apenas expôs a versão que já estava no `main`; não causou a substituição.

## Decisões

### 1. Preservação da landing

- Manter layout, conteúdo, seções e CTAs da landing CMMS atual.
- Alterar na landing somente referências antigas a `victoreduardodelavor.github.io/maintor-site`, normalizando-as para `https://maintor.com.br`.
- Manter links de entrada e teste apontando exclusivamente para `https://app.maintor.com.br`.
- Não restaurar a landing Maintor Flow e não reintroduzir `/flow` neste trabalho.

### 2. Índice do blog

Criar `blog/index.html` com:

- título, descrição, canonical e metadados sociais próprios para `/blog/`;
- apresentação curta do acervo de manutenção industrial;
- sete cards, um para cada artigo existente, usando seus títulos e descrições reais;
- links diretos e legíveis, sem extensão `.html`;
- CTA final para o aplicativo em `app.maintor.com.br`.

### 3. Índice de calculadoras

Criar `calculadoras/index.html` com:

- título, descrição, canonical e metadados sociais próprios para `/calculadoras/`;
- apresentação curta das ferramentas gratuitas;
- quatro cards, um para cada calculadora, explicando de forma breve o resultado oferecido;
- links diretos e legíveis, sem extensão `.html`;
- CTA final para o aplicativo em `app.maintor.com.br`.

### 4. Linguagem visual

Os dois índices reutilizarão o padrão visual e estrutural de `glossario/index.html`: navegação, tipografia, cores, largura de conteúdo, cards responsivos e rodapé. Como o site é HTML estático sem pipeline de componentes, a duplicação controlada de estilo é preferível a introduzir uma nova ferramenta de build apenas para estas duas páginas.

### 5. Sitemap e indexação

- Adicionar `https://maintor.com.br/blog/` e `https://maintor.com.br/calculadoras/` ao `sitemap.xml`.
- O sitemap passará de 34 para 36 URLs.
- Manter `/flow` ausente.
- Garantir canonical único e coerente com cada uma das 36 URLs.

## Conteúdo coberto

### Blog — 7 artigos

1. Análise de Causa Raiz na Manutenção: 5 Porquês e Ishikawa
2. CMMS vs Planilha: Quando Trocar o Excel no Chão de Fábrica
3. Os 7 Principais KPIs de Manutenção para a Gestão Industrial
4. Gestão de Manutenção na Indústria Plástica e Química
5. Plano de Manutenção Preventiva: Passo a Passo Completo
6. Manutenção Preventiva, Preditiva e Corretiva: Diferenças
7. Como Reduzir Paradas Não Planejadas na Indústria

### Calculadoras — 4 ferramentas

1. Custo de Parada de Máquina
2. MTBF, MTTR e Disponibilidade
3. OEE
4. ROI do CMMS

## Validação

Antes da publicação:

- teste automatizado deve falhar se `/blog/` ou `/calculadoras/` não tiverem arquivo de índice;
- todas as 36 entradas do sitemap devem corresponder a um HTML estático existente;
- todas as páginas devem ter canonical único no domínio `maintor.com.br`;
- nenhuma referência a `victoreduardodelavor.github.io/maintor-site` deve permanecer;
- `/flow` não pode reaparecer no conteúdo nem no sitemap;
- links do aplicativo devem permanecer em `app.maintor.com.br`;
- o diff da landing deve conter apenas a normalização de URLs já descrita.

Depois da publicação:

- aguardar o build bem-sucedido do GitHub Pages;
- confirmar HTTP 200 e conteúdo correto em `/`, `/blog/`, `/calculadoras/` e amostras das páginas internas;
- confirmar HTTP 404 em `/flow`;
- reconfirmar o aplicativo em `app.maintor.com.br` e a resposta protegida do webhook;
- reconfirmar publicamente todos os registros de e-mail e os registros do site.

## Fora de escopo

- redesenhar ou reescrever a landing CMMS;
- restaurar a landing Maintor Flow;
- alterar o aplicativo Base44;
- alterar registros DNS adicionais após a publicação já executada;
- mudar qualquer registro de e-mail.
