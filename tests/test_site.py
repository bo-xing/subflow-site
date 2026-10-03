"""Release checks for the generated public pages, routes, and bilingual content."""

from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT / 'scripts' / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.ids = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])

    def attrs(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / 'site.config.json').read_text())

    def test_public_pages_links_and_metadata_for_project_and_domain(self):
        for origin in (self.config['site_url'].rstrip('/'), 'https://subflow.example'):
            with self.subTest(origin=origin), tempfile.TemporaryDirectory() as tmp:
                site = build.Site(dict(self.config, site_url=origin))
                output = Path(tmp) / 'site'
                site.build(output)
                pages = {p: Page(p.read_text()) for p in output.rglob('*.html')}
                self.assertEqual(len(pages), 9)
                for path, page in pages.items():
                    with self.subTest(page=str(path.relative_to(output))):
                        self.assertEqual(len(page.ids), len(set(page.ids)), 'Duplicate element ID')
                        self.assertEqual(len(page.attrs('h1')), 1)
                        self.assertEqual(len(page.attrs('main')), 1)
                        self.assertIn(page.attrs('html')[0]['lang'], build.LOCALES)
                        source = path.read_text()
                        self.assertNotRegex(source, r'\{(?:email|developer|privacy_url|support_url|year)\}')
                        if path.parent.name in ('support', 'privacy', 'terms'):
                            self.assertIn('mailto:' + self.config['support_email'], source)
                        description = [m for m in page.attrs('meta') if m.get('name') == 'description']
                        self.assertTrue(description[0]['content'])
                        for tag, attrs in page.tags:
                            for attr in ('href', 'src'):
                                link = attrs.get(attr)
                                if not link:
                                    continue
                                parsed = urlsplit(link)
                                if parsed.scheme in ('https', 'mailto'):
                                    if tag in ('script', 'img') or (tag == 'link' and attrs.get('rel') == 'stylesheet'):
                                        self.fail(f'Unexpected third-party asset: {link}')
                                    continue
                                self.assertNotIn(parsed.scheme, ('javascript', 'http'))
                                current = origin + '/' + path.relative_to(output).as_posix()
                                resolved = urlsplit(urljoin(current, link))
                                self.assertTrue(resolved.path.startswith(site.base), link)
                                local = output / unquote(resolved.path[len(site.base):])
                                if local.is_dir():
                                    local /= 'index.html'
                                self.assertTrue(local.is_file(), f'Broken link on {path}: {link}')
                                if resolved.fragment:
                                    self.assertIn(unquote(resolved.fragment), pages[local].ids, link)
                        for image in page.attrs('img'):
                            self.assertIn('alt', image)
                            self.assertIn('width', image)
                            self.assertIn('height', image)
                        if path.name == '404.html':
                            self.assertIn({'name': 'robots', 'content': 'noindex'}, page.attrs('meta'))
                            continue
                        canonical = [a['href'] for a in page.attrs('link') if a.get('rel') == 'canonical']
                        expected = origin + '/' + path.relative_to(output).as_posix().removesuffix('index.html')
                        self.assertEqual(canonical, [expected])
                        alternates = {a['hreflang']: a['href'] for a in page.attrs('link') if a.get('rel') == 'alternate'}
                        self.assertEqual(set(alternates), {'en', 'zh-Hans', 'x-default'})
                        self.assertEqual(alternates['x-default'], alternates['en'])
                        for url in alternates.values():
                            target = output / url.removeprefix(origin + '/') / 'index.html'
                            self.assertTrue(target.is_file())
                sitemap = ET.parse(output / 'sitemap.xml')
                self.assertEqual(len(sitemap.findall('.//{*}loc')), 8)
                self.assertFalse((output / 'site.config.json').exists())
                self.assertFalse((output / 'docs').exists())

    def test_locale_structure_and_page_switch_preservation(self):
        site = build.Site(self.config)

        def shape(value):
            if isinstance(value, dict):
                return {key: shape(item) for key, item in value.items()}
            if isinstance(value, list):
                return [shape(item) for item in value]
            return type(value).__name__

        self.assertEqual(shape(site.copy['en']), shape(site.copy['zh-Hans']))
        for lang in build.LOCALES:
            other = 'zh-Hans' if lang == 'en' else 'en'
            for key in build.PAGES:
                page = Page(site.shell(lang, key, '<h1>Test</h1>'))
                switch = [a for a in page.attrs('a') if a.get('class') == 'language-link'][0]
                self.assertEqual(switch['href'], site.url(other, key))
                self.assertEqual(switch['hreflang'], other)

    def test_release_rejects_missing_or_invalid_public_details(self):
        build.Site(self.config).validate_release()
        for change in ({'developer_name': ''}, {'support_email': ''}, {'support_email': 'invalid'}, {'app_store_url': 'https://example.com'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                build.Site(dict(self.config, **change)).validate_release()

    def test_app_store_button_is_only_shown_with_an_app_store_url(self):
        site = build.Site(dict(self.config, app_store_url=''))
        self.assertNotIn('href="https://apps.apple.com', site.home('en'))
        self.assertIn('Preparing for the App Store', site.home('en'))
        site = build.Site(dict(self.config, app_store_url='https://apps.apple.com/app/id123456789'))
        self.assertIn('href="https://apps.apple.com/app/id123456789"', site.home('en'))
        self.assertNotIn('Preparing for the App Store', site.home('en'))

    def test_content_remains_available_without_javascript(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'site'
            build.Site(self.config).build(output)
            for lang in build.LOCALES:
                support = (output / build.route(lang, 'support') / 'index.html').read_text()
                self.assertIn('mailto:' + self.config['support_email'], support)
                self.assertEqual(len(Page(support).attrs('details')), 11)
                self.assertNotIn('<script', support)
                privacy = (output / build.route(lang, 'privacy') / 'index.html').read_text()
                self.assertIn('GitHub', privacy)
                self.assertIn('Gmail', privacy)
                self.assertIn('BYOK', privacy)
                self.assertIn(self.config['developer_name'], privacy)
                self.assertNotIn('<script', privacy)
                home = (output / build.route(lang, 'home') / 'index.html').read_text()
                self.assertIn('class="captions bilingual"', home)
                self.assertNotIn('<iframe', home)


if __name__ == '__main__':
    unittest.main()
