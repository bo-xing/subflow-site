"""Check the preview server against the project-path behavior used by Pages."""

from functools import partial
import http.client
from http.server import ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

from test_site import build, ROOT

spec = importlib.util.spec_from_file_location('site_preview', ROOT / 'scripts' / 'serve.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class QuietHandler(preview.Handler):
    def log_message(self, format, *args):
        pass


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        output = Path(cls.temp.name) / 'site'
        site = build.Site(json.loads((ROOT / 'site.config.json').read_text()))
        site.build(output)
        cls.base = site.base.rstrip('/')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(output)))
        cls.addClassCleanup(cls.server.server_close)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.stop_server)

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)

    def request(self, method, path):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path)
            response = connection.getresponse()
            return response.status, {key.lower(): value for key, value in response.getheaders()}, response.read()
        finally:
            connection.close()

    def test_get_and_head_agree_for_pages_assets_and_errors(self):
        for path, expected in (
            (self.base + '/', 200),
            (self.base + '/zh-Hans/privacy/', 200),
            (self.base + '/assets/styles.css', 200),
            (self.base + '/missing/deep/page/', 404),
            ('/privacy/', 404 if self.base else 200),
            ('/assets/styles.css', 404 if self.base else 200),
        ):
            with self.subTest(path=path):
                get_status, get_headers, body = self.request('GET', path)
                head_status, head_headers, head_body = self.request('HEAD', path)
                self.assertEqual(get_status, expected)
                self.assertEqual(head_status, get_status)
                self.assertEqual(head_headers['content-type'], get_headers['content-type'])
                self.assertEqual(int(head_headers['content-length']), len(body))
                self.assertEqual(head_body, b'')
                if expected == 404:
                    self.assertIn(b'Page not found', body)
                    self.assertIn((self.base + '/assets/styles.css').encode(), body)

    def test_get_and_head_agree_on_project_and_directory_redirects(self):
        redirects = [(self.base + '/support', self.base + '/support/', 301)]
        if self.base:
            redirects.extend([('/', self.base + '/', 302), (self.base, self.base + '/', 302)])
        for path, target, expected in redirects:
            for method in ('GET', 'HEAD'):
                with self.subTest(path=path, method=method):
                    status, headers, body = self.request(method, path)
                    self.assertEqual(status, expected)
                    self.assertEqual(headers['location'], target)
                    self.assertEqual(body, b'')


if __name__ == '__main__':
    unittest.main()
