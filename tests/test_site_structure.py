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
        self._capture = None

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

    def handle_endtag(self, tag):
        if tag == self._capture:
            self._capture = None

    def handle_data(self, data):
        if self._capture == "title":
            self.title += data
        elif self._capture == "h1":
            self.h1 += data


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

    def test_sitemap_has_36_unique_urls(self):
        locations = sitemap_locations()
        self.assertEqual(len(locations), 36)
        self.assertEqual(len(set(locations)), 36)
        self.assertIn(f"{BASE_URL}/blog/", locations)
        self.assertIn(f"{BASE_URL}/calculadoras/", locations)

    def test_every_sitemap_url_has_matching_file_and_canonical(self):
        for location in sitemap_locations():
            with self.subTest(location=location):
                path = local_path_for_url(location)
                self.assertTrue(path.is_file(), f"Arquivo ausente para {location}: {path}")
                self.assertEqual(parse_page(path).canonical, location)

    def test_production_files_have_no_stale_host_or_flow_route(self):
        production_files = [ROOT / "index.html", ROOT / "sitemap.xml"]
        for directory in ("blog", "calculadoras", "glossario"):
            production_files.extend(sorted((ROOT / directory).glob("*.html")))

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
