#!/usr/bin/env python3
"""Preview dist at its configured GitHub Pages project path on localhost."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'site.config.json').read_text())
BASE = urlsplit(CONFIG['site_url']).path.rstrip('/')


class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        # GET and HEAD must use identical routing, redirects, and error pages.
        path = urlsplit(self.path).path
        if BASE and path in ('/', BASE):
            self.send_response(302)
            self.send_header('Location', BASE + '/')
            self.end_headers()
            return None
        if BASE and not path.startswith(BASE + '/'):
            self.send_error(404)
            return None
        return super().send_head()

    def translate_path(self, path):
        parsed = urlsplit(path)
        clean = unquote(parsed.path)
        if BASE and clean.startswith(BASE + '/'):
            clean = clean[len(BASE):]
        return super().translate_path(clean)

    def send_error(self, code, message=None, explain=None):
        error_page = Path(self.directory) / '404.html'
        if code == 404 and error_page.exists():
            content = error_page.read_bytes()
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(content)
            return
        super().send_error(code, message, explain)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4173)
    args = parser.parse_args()
    if not (ROOT / 'dist' / 'index.html').exists():
        raise SystemExit('Run python3 scripts/build.py first.')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT / 'dist')))
    print(f'Preview: http://127.0.0.1:{args.port}{BASE}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
