"""Check rendered, crawlable HTML and all generated SEO/asset relationships."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse
import json
import xml.etree.ElementTree as ET

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.title = ''
        self.jsonld = []
        self.in_title = False
        self.in_json = False
        self.buffer = ''
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'title': self.in_title = True
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json = True
            self.buffer = ''
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.in_json:
            self.jsonld.append(json.loads(self.buffer))
            self.in_json = False
    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.in_json: self.buffer += data
    def attrs(self, tag): return [a for t, a in self.tags if t == tag]

def check(root):
    root = root.resolve()
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    urls = [e.text for e in ET.parse(root / 'sitemap.xml').iter(ns + 'loc')]
    assert len(urls) == len(set(urls)), 'Duplicate sitemap URLs'
    html_files = sorted(root.rglob('*.html'))
    parsed = {file: Page(file.read_text(encoding='utf8')) for file in html_files}
    homepage = parsed[root / 'index.html']
    canonical_home = next(a['href'] for a in homepage.attrs('link') if a.get('rel') == 'canonical')
    base = urlsplit(canonical_home)
    origin = f'{base.scheme}://{base.netloc}'
    titles, descriptions, indexed, linked = set(), set(), set(), set()
    for file, page in parsed.items():
        metas = {a.get('name'): a.get('content') for a in page.attrs('meta')}
        path = '/' + file.relative_to(root).as_posix().removesuffix('index.html')
        assert page.title and len(page.attrs('title')) == 1, file
        assert len(page.attrs('h1')) == 1, file
        assert metas.get('description'), file
        assert page.attrs('html')[0].get('lang') == 'zh-Hant', file
        canonicals = [a['href'] for a in page.attrs('link') if a.get('rel') == 'canonical']
        if path == '/404.html':
            assert not canonicals and not page.jsonld and 'noindex' in metas.get('robots', ''), file
        else:
            assert canonicals == [origin + path], file
            assert page.jsonld, file
        if 'noindex' not in metas.get('robots', ''):
            assert page.title not in titles, file
            assert metas['description'] not in descriptions, file
            titles.add(page.title); descriptions.add(metas['description']); indexed.add(origin + path)
        else:
            assert origin + path not in urls, file
        for graph in page.jsonld:
            assert graph['@context'] == 'https://schema.org', file
            assert all(entity.get('@type') != 'FAQPage' for entity in graph.get('@graph', [])), file
        for tag, attrs in page.tags:
            refs = [(attrs[key], tag == 'a') for key in ('href', 'src') if attrs.get(key)]
            refs += [(v.strip().rsplit(' ', 1)[0], False) for v in attrs.get('srcSet', attrs.get('srcset', '')).split(',') if v.strip()]
            for value, anchor in refs:
                url = urlsplit(value)
                if url.scheme or url.netloc: continue
                target = unquote(url.path)
                local = root / target.lstrip('/') if target.startswith('/') else file.parent / target
                if not target: local = file
                elif local.is_dir(): local /= 'index.html'
                assert local.resolve().is_relative_to(root) and local.is_file(), (file, value)
                if anchor and target.startswith('/'): linked.add(target)
                if url.fragment and anchor:
                    destination = parsed.get(local)
                    assert destination and any(a.get('id') == url.fragment for _, a in destination.tags), (file, value)
        for image in page.attrs('img'):
            assert image.get('alt') and int(image.get('width', 0)) > 0 and int(image.get('height', 0)) > 0, file
    assert indexed == set(urls), 'Sitemap and indexing directives differ'
    assert all(urlsplit(u).path in linked for u in urls), 'Orphaned indexable page'
    robots = (root / 'robots.txt').read_text(encoding='utf8')
    assert 'Disallow: /' not in robots and f'Sitemap: {origin}/sitemap.xml' in robots
    print(f'PASS: {len(urls)} indexable pages; metadata, canonical, JSON-LD, local assets, srcset, fragments, robots and sitemap')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'dist')
    check(parser.parse_args().directory)
