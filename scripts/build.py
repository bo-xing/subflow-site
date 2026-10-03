#!/usr/bin/env python3
"""Build the bilingual site using only the Python standard library."""

import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("home", "support", "privacy", "terms")
LOCALES = ("en", "zh-Hans")


def route(lang, page):
    return ("" if lang == "en" else "zh-Hans/") + ("" if page == "home" else page + "/")


def icon(name):
    paths = {
        "device": '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 18h4"/>',
        "captions": '<rect x="2" y="4" width="20" height="16" rx="3"/><path d="M6 10h5m2 0h5M6 14h8m2 0h2"/>',
        "shield": '<path d="m12 2 8 3v6c0 5-5 9-8 11-3-2-8-6-8-11V5l8-3Z"/><path d="m8 12 3 3 5-6"/>',
        "language": '<path d="M3 5h12M9 2v3m4 0c-1 7-5 10-10 12m2-9c1 4 4 7 7 8m2 5 4-11 4 11m-7-3h6"/>',
    }
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'


class Site:
    def __init__(self, config):
        self.config = config
        self.site_url = config["site_url"].rstrip("/")
        parsed = urlsplit(self.site_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("site_url must be an HTTPS URL without a query or fragment")
        if not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)*", parsed.path):
            raise ValueError("site_url must have a simple, unescaped project path")
        self.base = parsed.path + "/"
        self.updated = date.fromisoformat(config["updated"])
        self.copy = {lang: json.loads((ROOT / "content" / f"{lang}.json").read_text()) for lang in LOCALES}

    def validate_release(self):
        if not self.config["developer_name"].strip():
            raise ValueError("Set developer_name before publishing")
        if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", self.config["support_email"]):
            raise ValueError("Set a valid public support_email before publishing")
        app_url = self.config["app_store_url"]
        if app_url and (urlsplit(app_url).scheme != "https" or urlsplit(app_url).hostname != "apps.apple.com"):
            raise ValueError("app_store_url must be an HTTPS App Store URL or empty")

    def url(self, lang, page):
        return self.base + route(lang, page)

    def absolute(self, lang, page):
        return self.site_url + "/" + route(lang, page)

    def rich(self, value, lang):
        # Only checked-in copy contains markup; inserted configuration is escaped.
        replacements = {
            "developer": self.config["developer_name"] or "SubFlow",
            "email": self.config["support_email"],
            "year": str(self.updated.year),
            "privacy_url": self.url(lang, "privacy"),
            "support_url": self.url(lang, "support"),
        }
        for key, replacement in replacements.items():
            value = value.replace("{" + key + "}", escape(replacement, quote=True))
        return value

    def updated_label(self, lang):
        if lang == "zh-Hans":
            return f"更新日期：{self.updated.year} 年 {self.updated.month} 月 {self.updated.day} 日"
        return f"Last updated: {self.updated.strftime('%B')} {self.updated.day}, {self.updated.year}"

    def shell(self, lang, page, body):
        data = self.copy[lang]
        common = data["common"]
        info = data[page] if page in PAGES else data["not_found"]
        is_404 = page == "404"
        target_page = "home" if is_404 else page
        other = "zh-Hans" if lang == "en" else "en"
        nav = "".join(f'<a href="{self.url(lang, key)}"' + (' aria-current="page"' if page == key else '') + f'>{escape(label)}</a>' for key, label in data["nav"].items())
        footer_links = "".join(f'<a href="{self.url(lang, key)}">{escape(data["nav"][key])}</a>' for key in PAGES[1:])
        metadata = '<meta name="robots" content="noindex">' if is_404 else (
            f'<link rel="canonical" href="{self.absolute(lang, page)}">\n' +
            "\n".join(f'<link rel="alternate" hreflang="{loc}" href="{self.absolute(loc, page)}">' for loc in LOCALES) +
            f'\n<link rel="alternate" hreflang="x-default" href="{self.absolute("en", page)}">')
        script = f'<script src="{self.base}assets/preview.js" defer></script>' if page == "home" else ''
        draft = '' if self.config["support_email"] and self.config["developer_name"] else f'<div class="draft-notice">{escape(common["draft"])}</div>'
        description = info.get("description", info.get("body", ""))
        description = escape(description.replace('{developer}', self.config['developer_name']).replace('{email}', self.config['support_email']), quote=True)
        return f'''<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#090a0d">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <title>{escape(info['title'])}</title>
  <meta name="description" content="{description}">
  {metadata}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="SubFlow">
  <meta property="og:locale" content="{data['locale']}">
  <meta property="og:title" content="{escape(info['title'], quote=True)}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{self.absolute(lang, target_page)}">
  <meta property="og:image" content="{self.site_url}/assets/app-icon.png">
  <meta property="og:image:width" content="1024">
  <meta property="og:image:height" content="1024">
  <meta property="og:image:alt" content="SubFlow">
  <meta name="twitter:card" content="summary">
  <link rel="icon" type="image/png" href="{self.base}assets/app-icon.png">
  <link rel="apple-touch-icon" href="{self.base}assets/app-icon.png">
  <link rel="stylesheet" href="{self.base}assets/styles.css">
  {script}
</head>
<body>
  <a class="skip-link" href="#main">{escape(common['skip'])}</a>
  {draft}
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="brand" href="{self.url(lang, 'home')}"><img src="{self.base}assets/app-icon.png" alt="" width="40" height="40">SubFlow</a>
      <nav class="main-nav" aria-label="{escape(common['navigation'])}">{nav}</nav>
      <a class="language-link" href="{self.url(other, target_page)}" lang="{other}" hreflang="{other}" aria-label="{escape(common['language_label'])}">{icon('language')}{escape(common['language'])}</a>
    </div>
  </header>
  <main id="main">{body}</main>
  <footer class="site-footer">
    <div class="wrap footer-inner">
      <div><span class="footer-brand">SubFlow</span><p class="footer-note">{escape(common['footer'])}<br>{self.rich(common['copyright'], lang)}</p></div>
      <nav class="footer-links" aria-label="{escape(common['footer_navigation'])}">{footer_links}</nav>
    </div>
  </footer>
</body>
</html>
'''

    def home(self, lang):
        h = self.copy[lang]["home"]
        primary_url = self.config["app_store_url"] or '#features'
        primary_label = h['download'] if self.config["app_store_url"] else h['cta']
        release = '' if self.config["app_store_url"] else f'<br>{escape(h["prerelease"])}'
        mode_buttons = ''.join(f'<button type="button" data-mode="{mode}" aria-pressed="{str(index == 0).lower()}">{escape(label)}</button>' for index, (mode, label) in enumerate(zip(('bilingual', 'original', 'cinema'), h['modes'])))
        principles = ''.join(f'<div>{icon(name)}<span>{escape(label)}</span></div>' for name, label in zip(('device', 'captions', 'shield'), h['principles']))
        features = ''.join(f'<article class="feature"><span class="feature-number">0{i}</span><h3>{escape(f["title"])}</h3><p>{escape(f["body"])}</p><span class="feature-tag">{escape(f["tag"])}</span></article>' for i, f in enumerate(h['features'], 1))
        sources = ''.join(f'<li><strong>{escape(name)}</strong><span>{escape(tier)}</span></li>' for name, tier in h['sources'])
        free_features = ''.join(f'<li>{escape(item)}</li>' for item in h['free_features'])
        pro_features = ''.join(f'<li>{escape(item)}</li>' for item in h['pro_features'])
        return f'''
<div class="wrap">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-copy">
      <p class="eyebrow">{escape(h['eyebrow'])}</p>
      <h1 id="hero-title">{h['headline']}</h1>
      <p class="lead">{escape(h['intro'])}</p>
      <div class="actions"><a class="button button-primary" href="{escape(primary_url, quote=True)}">{escape(primary_label)} <span aria-hidden="true">↗</span></a><a class="text-link" href="{self.url(lang, 'support')}">{escape(h['secondary'])} <span aria-hidden="true">→</span></a></div>
      <p class="availability">{escape(h['availability'])}{release}</p>
    </div>
    <figure class="preview">
      <div class="preview-frame">
        <div class="preview-top"><span>{escape(h['preview_title'])}</span><span>{escape(h['preview_tag'])}</span></div>
        <div class="preview-art">
          <img class="landscape" src="{self.base}assets/landscape.svg" alt="" width="900" height="620" fetchpriority="high">
          <span class="scene-label">{escape(h['scene'])}</span>
          <div class="captions bilingual"><span class="caption-en" lang="en">{escape(h['caption_en'])}</span><span class="caption-zh" lang="zh-Hans">{escape(h['caption_zh'])}</span></div>
        </div>
        <div class="preview-controls" aria-hidden="true"><div class="progress-track"></div><div class="preview-time"><span>02:34</span><span>{escape(h['preview_ready'])}</span><span>06:48</span></div></div>
      </div>
      <figcaption class="preview-caption"><span>{escape(h['preview_note'])}</span><div class="preview-modes" role="group" aria-label="{escape(h['preview_modes'])}" hidden>{mode_buttons}</div></figcaption>
    </figure>
  </section>
  <div class="principles">{principles}</div>
  <section class="section" id="features" aria-labelledby="features-title">
    <p class="eyebrow">{escape(h['features_eyebrow'])}</p>
    <div class="section-heading"><h2 id="features-title">{h['features_title']}</h2><p>{escape(h['features_intro'])}</p></div>
    <div class="feature-grid">{features}</div>
  </section>
</div>
<section class="source-section section" aria-labelledby="sources-title"><div class="wrap sources"><div><p class="eyebrow">{escape(h['sources_eyebrow'])}</p><h2 id="sources-title">{h['sources_title']}</h2><p class="muted">{escape(h['sources_body'])}</p><p class="fine-print">{escape(h['sources_note'])}</p></div><ul class="source-list">{sources}</ul></div></section>
<div class="wrap">
  <section class="section" id="pro" aria-labelledby="plans-title">
    <p class="eyebrow">{escape(h['plans_eyebrow'])}</p><div class="section-heading"><h2 id="plans-title">{h['plans_title']}</h2></div>
    <div class="plans"><article class="plan"><div class="plan-top"><h3>{escape(h['free'])}</h3></div><p>{escape(h['free_intro'])}</p><ul>{free_features}</ul></article><article class="plan pro"><div class="plan-top"><h3>{escape(h['pro'])}</h3><span class="pill">{escape(h['pro_badge'])}</span></div><p>{escape(h['pro_intro'])}</p><ul>{pro_features}</ul></article></div>
    <p class="fine-print plan-note">{escape(h['plans_note'])} <a href="{self.url(lang, 'terms')}">{escape(h['plans_link'])} <span aria-hidden="true">↗</span></a></p>
    <p class="fine-print plan-note">{escape(h['capability_note'])}</p>
  </section>
  <section class="privacy-banner" aria-labelledby="privacy-title"><div><p class="eyebrow">{escape(h['privacy_eyebrow'])}</p><h2 id="privacy-title">{escape(h['privacy_title'])}</h2></div><div><p>{escape(h['privacy_body'])}</p><p>{escape(h['privacy_detail'])}</p><a class="text-link" href="{self.url(lang, 'privacy')}">{escape(h['privacy_link'])} <span aria-hidden="true">→</span></a></div></section>
</div>'''

    def heading(self, lang, page):
        data = self.copy[lang][page]
        updated = f'<p class="updated">{self.updated_label(lang)}</p>' if page in ('privacy', 'terms') else ''
        return f'<div class="page-heading"><p class="eyebrow">{escape(data["eyebrow"])}</p><h1>{data["headline"]}</h1><p class="lead">{escape(data["intro"])}</p>{updated}</div>'

    def toc(self, lang, links):
        common = self.copy[lang]['common']
        items = ''.join(f'<a href="#{escape(identifier)}">{escape(title)}</a>' for identifier, title in links)
        return f'<nav class="toc" aria-label="{escape(common["contents"])}"><p>{escape(common["contents"])}</p>{items}</nav>'

    def contact(self, lang):
        common = self.copy[lang]['common']
        email = escape(self.config['support_email'], quote=True)
        return f'<section class="contact-panel" id="contact"><h2>{escape(common["contact_title"])}</h2><p>{self.rich(common["contact_body"], lang)}</p><a class="contact-address" href="mailto:{email}">{email}</a><p class="fine-print">{escape(common["contact_note"])}</p></section>'

    def support(self, lang):
        data = self.copy[lang]['support']
        common = self.copy[lang]['common']
        toc = self.toc(lang, [('contact', common['email_label']), ('start', data['start_title']), ('faq', data['faq_title']), ('report', data['report_title'])])
        faqs = ''.join(f'<details><summary>{escape(item["q"])}</summary><p>{self.rich(item["a"], lang)}</p></details>' for item in data['faq'])
        report = ''.join(f'<li>{escape(item)}</li>' for item in data['report_items'])
        return f'''<div class="wrap">{self.heading(lang, 'support')}<div class="document-layout">{toc}<div class="prose">
{self.contact(lang)}
<section id="start"><h2>{escape(data['start_title'])}</h2><p>{escape(data['start_body'])}</p></section>
<section id="faq" class="faq"><h2>{escape(data['faq_title'])}</h2>{faqs}</section>
<section id="report"><h2>{escape(data['report_title'])}</h2><p>{escape(data['report_body'])}</p><ul>{report}</ul><p>{escape(data['report_note'])}</p></section>
</div></div></div>'''

    def document(self, lang, page):
        data = self.copy[lang][page]
        toc = self.toc(lang, [(s['id'], s['title']) for s in data['sections']])
        sections = ''
        for section in data['sections']:
            paragraphs = ''.join(f'<p>{self.rich(p, lang)}</p>' for p in section['body'])
            sections += f'<section id="{escape(section["id"])}"><h2>{escape(section["title"])}</h2>{paragraphs}</section>'
        return f'<div class="wrap">{self.heading(lang, page)}<div class="document-layout">{toc}<div class="prose"><div class="callout"><p>{escape(data["summary"])}</p></div>{sections}</div></div></div>'

    def build(self, output):
        # The CLI fixes this directory to dist; callers use isolated temporary dirs.
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        shutil.copytree(ROOT / 'assets', output / 'assets')
        urls = []
        for lang in LOCALES:
            for page in PAGES:
                content = self.home(lang) if page == 'home' else self.support(lang) if page == 'support' else self.document(lang, page)
                target = output / route(lang, page) / 'index.html'
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(self.shell(lang, page, content), encoding='utf-8')
                urls.append(self.absolute(lang, page))
        nf = self.copy['en']['not_found']
        body = f'<div class="wrap"><div class="not-found"><p class="eyebrow">{escape(nf["eyebrow"])}</p><h1>{escape(nf["headline"])}</h1><p class="lead">{escape(nf["body"])}</p><div class="actions"><a class="button button-primary" href="{self.url("en", "home")}">{escape(nf["home"])}</a><a class="text-link" href="{self.url("en", "support")}">{escape(nf["support"])}</a><a class="text-link" lang="zh-Hans" href="{self.url("zh-Hans", "home")}">简体中文首页</a></div></div></div>'
        (output / '404.html').write_text(self.shell('en', '404', body), encoding='utf-8')
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        sitemap += ''.join(f'  <url><loc>{escape(url)}</loc><lastmod>{self.updated.isoformat()}</lastmod></url>\n' for url in urls) + '</urlset>\n'
        (output / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
        (output / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {self.site_url}/sitemap.xml\n', encoding='utf-8')
        (output / '.nojekyll').touch()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true', help='Require valid public contact details')
    args = parser.parse_args()
    site = Site(json.loads((ROOT / 'site.config.json').read_text()))
    if args.release:
        site.validate_release()
    site.build(ROOT / 'dist')
    print(f'Built 8 localized pages + 404 into {ROOT / "dist"} (base path: {site.base})')


if __name__ == '__main__':
    main()
