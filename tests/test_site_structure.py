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

    def test_sitemap_has_36_unique_urls(self):
        locations = sitemap_locations()
        self.assertEqual(len(locations), 36)
        self.assertEqual(len(set(locations)), 36)
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


if __name__ == "__main__":
    unittest.main()
