import html
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://maintor.com.br"

BLOG_SLUGS = {
    "causa-raiz-de-falhas",
    "cmms-vs-planilha",
    "kpis-manutencao-gestor",
    "manutencao-industria-plastico",
    "plano-manutencao-preventiva-passo-a-passo",
    "preventiva-preditiva-corretiva",
    "reduzir-paradas-nao-planejadas",
}

BLOG_DESCRIPTIONS = {
    "causa-raiz-de-falhas": "Aprenda a aplicar a Análise de Causa Raiz (RCA), o método dos 5 Porquês e o Diagrama de Ishikawa para eliminar falhas recorrentes no chão de fábrica.",
    "cmms-vs-planilha": "Descubra os sinais de que sua gestão de manutenção industrial ultrapassou o Excel e entenda os benefícios da migração para um software CMMS.",
    "kpis-manutencao-gestor": "MTBF, MTTR, Disponibilidade, OEE, Backlog e mais: conheça os 7 principais indicadores de manutenção industrial para apresentar à diretoria.",
    "manutencao-industria-plastico": "Boas práticas de manutenção industrial para injetoras, chillers, reatores e caldeiras NR-13. Evite bateladas perdidas e paradas de linha.",
    "plano-manutencao-preventiva-passo-a-passo": "Aprenda a estruturar um plano de manutenção preventiva industrial do zero: inventário, criticidade, rotinas, checklists e cronograma de execução.",
    "preventiva-preditiva-corretiva": "Entenda a diferença entre manutenção preventiva, preditiva e corretiva. Saiba quando aplicar cada tipo para otimizar o orçamento da indústria.",
    "reduzir-paradas-nao-planejadas": "Estratégias práticas para mitigar a dor nº 1 dos gestores industriais: identificação de causa raiz, preventiva eficiente e eliminação de gargalos.",
}

CALCULATOR_SLUGS = {
    "custo-parada-maquina",
    "mtbf-mttr-disponibilidade",
    "oee",
    "roi-cmms",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.h1 = ""
        self.canonical = None
        self.metadata = {}
        self.links = []
        self.card_text = {}
        self._capture = None
        self._card_href = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "title":
            self._capture = "title"
        elif tag == "h1":
            self._capture = "h1"
        elif tag == "meta":
            key = attributes.get("name") or attributes.get("property")
            if key and attributes.get("content"):
                self.metadata[key] = attributes["content"]
        elif tag == "link" and attributes.get("rel") == "canonical":
            self.canonical = attributes.get("href")
        elif tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
            if "card" in attributes.get("class", "").split():
                self._card_href = attributes["href"]
                self.card_text[self._card_href] = ""

    def handle_endtag(self, tag):
        if tag == self._capture:
            self._capture = None
        if tag == "a":
            self._card_href = None

    def handle_data(self, data):
        if self._capture == "title":
            self.title += data
        elif self._capture == "h1":
            self.h1 += data
        if self._card_href:
            self.card_text[self._card_href] += data


def parse_page(path):
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def sitemap_locations():
    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [node.text for node in tree.findall("sm:url/sm:loc", namespace)]


def local_path_for_url(url):
    path = urlparse(url).path
    if path == "/":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.strip("/") / "index.html"
    return ROOT / f"{path.strip('/')}.html"


class SiteStructureTests(unittest.TestCase):
    def test_homepage_matches_approved_commercial_offer(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")

        for expected in (
            "Centralize ordens de serviço, preventivas, ativos, estoque e indicadores",
            "Testar grátis por 30 dias",
            "https://app.maintor.com.br/Cadastro",
            "https://app.maintor.com.br/Home",
            "Start — R$ 119/mês",
            "Pro — R$ 197/mês ou R$ 1.970/ano",
            "Sense — Piloto assistido",
            "https://app.maintor.com.br/sense",
            "https://app.maintor.com.br/TermosDeUso",
            "https://app.maintor.com.br/PoliticaPrivacidade",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, content)

        self.assertNotIn("https://app.maintor.com.br\"", content)

    def test_homepage_contact_form_submits_to_the_public_lead_endpoint(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn('id="contact-form"', content)
        self.assertIn('https://app.maintor.com.br/functions/upsertPublicLead', content)
        self.assertIn("source: 'site'", content)
        self.assertIn('id="contact-status"', content)
        self.assertNotIn("Formulário demonstrativo", content)

    def assert_index_contract(self, relative_path, canonical, expected_slugs):
        path = ROOT / relative_path
        self.assertTrue(path.is_file(), f"Índice ausente: {relative_path}")

        page = parse_page(path)
        self.assertTrue(page.title.strip(), f"Title ausente em {relative_path}")
        self.assertTrue(page.h1.strip(), f"H1 ausente em {relative_path}")
        self.assertTrue(
            page.metadata.get("description", "").strip(),
            f"Description ausente em {relative_path}",
        )
        self.assertEqual(page.canonical, canonical)
        self.assertEqual(page.metadata.get("og:url"), canonical)
        self.assertIn("https://app.maintor.com.br", page.links)

        linked_slugs = {
            urlparse(link).path.rstrip("/").split("/")[-1]
            for link in page.links
        }
        self.assertTrue(
            expected_slugs.issubset(linked_slugs),
            f"Links ausentes em {relative_path}: {sorted(expected_slugs - linked_slugs)}",
        )

    def test_blog_index(self):
        self.assert_index_contract(
            "blog/index.html",
            f"{BASE_URL}/blog/",
            BLOG_SLUGS,
        )

    def test_calculators_index(self):
        self.assert_index_contract(
            "calculadoras/index.html",
            f"{BASE_URL}/calculadoras/",
            CALCULATOR_SLUGS,
        )

    def test_blog_cards_use_source_descriptions(self):
        page = parse_page(ROOT / "blog/index.html")
        for slug, description in BLOG_DESCRIPTIONS.items():
            url = f"{BASE_URL}/blog/{slug}"
            with self.subTest(slug=slug):
                self.assertIn(description, page.card_text.get(url, ""))

    def test_mobile_navigation_keeps_content_areas_available(self):
        hidden_rule = "nav a:not(.app){display:none}"
        for relative_path in ("blog/index.html", "calculadoras/index.html"):
            content = (ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(relative_path=relative_path):
                self.assertNotIn(hidden_rule, content)

    def test_sitemap_has_37_unique_urls(self):
        locations = sitemap_locations()
        self.assertEqual(len(locations), 37)
        self.assertEqual(len(set(locations)), 37)
        self.assertIn(f"{BASE_URL}/blog/", locations)
        self.assertIn(f"{BASE_URL}/calculadoras/", locations)

    def test_every_sitemap_url_has_matching_file_and_canonical(self):
        for location in sitemap_locations():
            with self.subTest(location=location):
                parsed = urlparse(location)
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.netloc, "maintor.com.br")
                path = local_path_for_url(location)
                self.assertTrue(path.is_file(), f"Arquivo ausente para {location}: {path}")
                self.assertEqual(parse_page(path).canonical, location)

    def test_production_files_have_no_stale_host_or_flow_route(self):
        production_files = sorted(ROOT.rglob("*.html"))
        production_files.extend(sorted(ROOT.rglob("*.xml")))
        production_files = [
            path for path in production_files if "docs" not in path.parts
        ]

        forbidden = (
            "victoreduardodelavor.github.io/maintor-site",
            "maintor.com.br/flow",
        )
        for path in production_files:
            content = path.read_text(encoding="utf-8")
            for value in forbidden:
                with self.subTest(path=path.relative_to(ROOT), value=value):
                    self.assertNotIn(value, content)

    def test_404_is_a_real_error_page_with_no_form_that_drops_leads(self):
        content = (ROOT / "404.html").read_text(encoding="utf-8")

        self.assertNotIn("<form", content)
        self.assertNotIn("Formulário demonstrativo", content)
        self.assertNotIn("alert(", content)
        self.assertIn('name="robots" content="noindex"', content)
        self.assertIn("https://wa.me/5511946610634", content)
        self.assertIn("victor@maintor.com.br", content)

    def test_no_form_in_the_site_discards_the_visitor_message(self):
        for path in sorted(ROOT.rglob("*.html")):
            if "docs" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn('onsubmit="alert(', content)
                # Formulário que coleta contato (e-mail/telefone) tem de chamar o endpoint de lead.
                # As calculadoras também têm <form>, mas só de números.
                if "<form" in content and re.search(r'type="(email|tel)"', content):
                    self.assertIn("upsertPublicLead", content)

    def json_ld_blocks(self, relative_path):
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        blocks = re.findall(
            r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', content, re.S
        )
        return [json.loads(block) for block in blocks]

    def test_homepage_structured_data_has_real_prices(self):
        software = next(
            block for block in self.json_ld_blocks("index.html")
            if block.get("@type") == "SoftwareApplication"
        )
        offers = software["offers"]
        self.assertIsInstance(offers, list)
        prices = {offer["name"]: offer["price"] for offer in offers}
        self.assertEqual(
            prices,
            {"Maintor Start": "119.00", "Maintor Pro": "197.00", "Maintor Pro (anual)": "1970.00"},
        )
        for offer in offers:
            self.assertEqual(offer["priceCurrency"], "BRL")
            self.assertNotEqual(offer["price"], "0")
        self.assertNotIn("telemetria", software["description"].lower())

    def test_homepage_faq_structured_data_matches_the_visible_faq(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        visible = re.findall(r"<details>\s*<summary>(.*?)</summary>", content, re.S)
        faq = next(
            block for block in self.json_ld_blocks("index.html")
            if block.get("@type") == "FAQPage"
        )
        structured = [question["name"] for question in faq["mainEntity"]]
        self.assertEqual(len(visible), 7)
        self.assertEqual(structured, [html.unescape(question).strip() for question in visible])
        self.assertIn("Qual a diferença entre Start e Pro?", structured)

    def test_omie_wording_makes_no_promise_the_product_cannot_keep(self):
        content = (ROOT / "index.html").read_text(encoding="utf-8")
        for forbidden in ("direto ao ERP", "direto para o ERP", "tempo real com o OMIE"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, content)
        self.assertIn("ativa a integração na implantação", content)

    def content_pages(self):
        pages = []
        for folder in ("glossario", "blog", "calculadoras"):
            pages.extend(
                path for path in sorted((ROOT / folder).glob("*.html"))
                if path.name != "index.html"
            )
        return pages

    def test_every_content_page_leads_to_the_funnel(self):
        pages = self.content_pages()
        self.assertEqual(len(pages), 32)
        for path in pages:
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("https://app.maintor.com.br/Cadastro?utm_source=site", content)
                self.assertIn("utm_medium=conteudo", content)
                self.assertIn(f"utm_campaign={path.parent.name.replace('calculadoras', 'calculadora')}-{path.stem}", content)
                self.assertIn("https://maintor.com.br/#video-demo", content)
                self.assertIn("https://wa.me/5511946610634", content)
                self.assertNotIn("11) 93941-3839", content)
                self.assertNotIn("contato@maintor.com.br", content)

    def test_sitemap_lastmod_is_not_older_than_the_last_change(self):
        tree = ET.parse(ROOT / "sitemap.xml")
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for node in tree.findall("sm:url", namespace):
            location = node.find("sm:loc", namespace).text
            lastmod = node.find("sm:lastmod", namespace).text
            path = local_path_for_url(location)
            with self.subTest(location=location):
                self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}$")
                try:
                    result = subprocess.run(
                        ["git", "-c", "safe.directory=*", "log", "-1", "--format=%cs", "--", str(path.relative_to(ROOT))],
                        cwd=ROOT, capture_output=True, text=True, check=True,
                    )
                except (OSError, subprocess.CalledProcessError):
                    self.skipTest("git indisponível")
                last_change = result.stdout.strip()
                if last_change:
                    self.assertGreaterEqual(lastmod, last_change)

    def test_help_page_publishes_the_support_rule(self):
        content = (ROOT / "ajuda/index.html").read_text(encoding="utf-8")
        for expected in (
            "https://wa.me/5511946610634",
            "victor@maintor.com.br",
            "segunda a sexta, das 9h às 18h",
            "não prometemos um prazo fixo",
            "Gerenciar assinatura",
            "Exportar Excel",
            "Excluir minha conta",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, content)
        # Decisão D13: sem SLA numérico, sem "atendimento prioritário".
        self.assertNotRegex(content, r"em até \d+ ?(h|horas|minutos)")
        self.assertNotIn("prioritário", content)
        self.assertNotIn("93941", content)
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("https://maintor.com.br/ajuda/", home)
        self.assertNotIn('href="#demo"', home)


if __name__ == "__main__":
    unittest.main()
