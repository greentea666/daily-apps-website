"""End-to-end build and deployment regressions; uses only Python's standard library.

Run after npm ci: python3 -m unittest discover -s tests -v
All output and altered catalogs stay in temporary directories.
"""
import copy
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://daily-apps-audit.pages.dev'


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.title = ''
        self.json = []
        self._in_title = False
        self._json = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'title':
            self._in_title = True
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self._json = ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        if tag == 'script' and self._json is not None:
            self.json.append(json.loads(self._json))
            self._json = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._json is not None:
            self._json += data

    def attrs(self, tag):
        return [attrs for current, attrs in self.tags if current == tag]

    def meta(self, key):
        return [a.get('content', '') for a in self.attrs('meta')
                if a.get('name') == key or a.get('property') == key]

    def canonicals(self):
        return [a['href'] for a in self.attrs('link') if a.get('rel') == 'canonical']


def run_build(source, output, *, origin=ORIGIN, extra_env=None):
    env = os.environ.copy()
    for name in ('SITE_ORIGIN', 'SITE_OUTPUT_DIR', 'CF_PAGES', 'CF_PAGES_URL',
                 'GOOGLE_SITE_VERIFICATION', 'SITE_NOINDEX'):
        env.pop(name, None)
    env['SITE_OUTPUT_DIR'] = str(output)
    if origin is not None:
        env['SITE_ORIGIN'] = origin
    env.update(extra_env or {})
    return subprocess.run(['node', str(source / 'scripts/build.mjs')], cwd=source,
                          env=env, capture_output=True, text=True, timeout=60)


def fixture_source(parent):
    source = parent / 'source'
    source.mkdir()
    for name in ('apps.json', 'notes.json', 'image-metadata.json', 'package.json',
                 'package-lock.json', 'build.py'):
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, source / name)
    for name in ('src', 'public', 'scripts'):
        shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns('__pycache__'))
    # Test fixtures share installed dependencies but never install or modify them.
    (source / 'node_modules').symlink_to(ROOT / 'node_modules', target_is_directory=True)
    return source


def page_path(file, output):
    relative = file.relative_to(output).as_posix()
    return '/' + (relative[:-10] if relative.endswith('index.html') else relative)


def resolve_asset(output, value, base='/'):
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = Path(unquote(parsed.path))
    candidate = output / path.as_posix().lstrip('/') if path.is_absolute() else output / base.lstrip('/') / path
    return candidate if candidate.is_file() else candidate / 'index.html'


class BuiltSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='daily-apps-tests-')
        cls.base = Path(cls.temporary.name)
        cls.source = fixture_source(cls.base)
        cls.output = cls.base / 'output'
        result = run_build(cls.source, cls.output)
        if result.returncode:
            cls.temporary.cleanup()
            raise AssertionError(result.stdout + result.stderr)
        cls.pages = {page_path(file, cls.output): Page(file.read_text(encoding='utf-8'))
                     for file in cls.output.rglob('*.html')}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_indexing_metadata_and_canonical_agree_with_sitemap(self):
        urls = [element.text for element in ET.parse(self.output / 'sitemap.xml').iter(
            '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(urls), len(set(urls)), 'Duplicate sitemap entries')
        indexed = set()
        titles, descriptions = set(), set()
        for path, page in self.pages.items():
            with self.subTest(path=path):
                self.assertEqual(len(page.attrs('h1')), 1)
                self.assertEqual(page.attrs('html')[0]['lang'], 'zh-Hant')
                self.assertEqual(len(page.meta('description')), 1)
                self.assertTrue(page.title)
                self.assertTrue(page.meta('description')[0])
                self.assertEqual(page.meta('google-site-verification'),
                                 ['baYzpitVeMcfKx5CBc7M2PPL-9_dE3GzjkUho9gdUN8'])
                if path == '/404.html':
                    self.assertIn('noindex', page.meta('robots')[0])
                    self.assertEqual(page.canonicals(), [])
                    self.assertEqual(page.json, [])
                    continue
                self.assertEqual(page.canonicals(), [ORIGIN + path])
                self.assertEqual(page.meta('og:url'), [ORIGIN + path])
                if 'noindex' not in page.meta('robots')[0]:
                    indexed.add(ORIGIN + path)
                    self.assertNotIn(page.title, titles, 'Duplicate page title')
                    self.assertNotIn(page.meta('description')[0], descriptions,
                                     'Duplicate page description')
                    titles.add(page.title)
                    descriptions.add(page.meta('description')[0])
        self.assertEqual(indexed, set(urls))
        apps = json.loads((self.source / 'apps.json').read_text(encoding='utf-8'))
        articles = json.loads((self.source / 'notes.json').read_text(encoding='utf-8'))
        expected = {ORIGIN + '/', ORIGIN + '/notes/', ORIGIN + '/privacy/'}
        expected.update(ORIGIN + '/apps/' + a['slug'] + '/' for a in apps if a.get('listed', True))
        expected.update(ORIGIN + '/notes/' + a[0] + '/' for a in articles)
        self.assertEqual(indexed, expected)
        robots = (self.output / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn('Sitemap: ' + ORIGIN + '/sitemap.xml', robots)
        self.assertNotIn('Disallow: /', robots)

    def test_every_page_asset_fragment_and_indexable_route_is_reachable(self):
        linked = {'/'}
        for current, page in self.pages.items():
            for tag, attrs in page.tags:
                values = [attrs[key] for key in ('src', 'href') if key in attrs]
                if attrs.get('srcset'):
                    values.extend(item.strip().split()[0] for item in attrs['srcset'].split(','))
                for value in values:
                    with self.subTest(page=current, value=value):
                        target = resolve_asset(self.output, value,
                                               current if current.endswith('/') else '/')
                        if target is not None:
                            self.assertTrue(target.is_file(), str(target))
                        parsed = urlsplit(value)
                        if not parsed.scheme and not parsed.netloc and tag == 'a':
                            if parsed.path.startswith('/'):
                                linked.add(parsed.path)
                            if parsed.fragment:
                                target_page = self.pages.get(parsed.path or current)
                                if target_page:
                                    self.assertIn(unquote(parsed.fragment),
                                                  [a.get('id') for _, a in target_page.tags])
            for image in page.attrs('img'):
                self.assertTrue(image.get('alt'), current)
                self.assertGreater(int(image.get('width', 0)), 0)
                self.assertGreater(int(image.get('height', 0)), 0)
        for path, page in self.pages.items():
            if 'noindex' not in page.meta('robots')[0]:
                self.assertIn(path, linked, 'Orphan page: ' + path)
        for file in self.output.rglob('*.css'):
            for value in re.findall(r'url\(\s*[\'"]?([^\)\'"\s]+)', file.read_text(encoding='utf-8')):
                target = resolve_asset(self.output, value, '/' + file.relative_to(self.output).parent.as_posix() + '/')
                if target is not None:
                    self.assertTrue(target.is_file(), f'{file}: {value}')

    def test_jsonld_uses_real_catalog_without_unconfirmed_ratings_or_prices(self):
        apps = json.loads((self.source / 'apps.json').read_text(encoding='utf-8'))
        for app in apps:
            page = self.pages['/apps/' + app['slug'] + '/']
            nodes = [node for data in page.json for node in data.get('@graph', [])]
            products = [node for node in nodes if node.get('@type') == 'SoftwareApplication']
            if app.get('listed', True) is False:
                self.assertEqual(products, [])
                continue
            self.assertEqual(len(products), 1)
            product = products[0]
            self.assertEqual(product['name'], app['name'])
            self.assertEqual(product['applicationCategory'], app['schemaCategory'])
            self.assertNotIn('aggregateRating', product)
            self.assertNotIn('offers', product)
            if not app.get('platform'):
                self.assertNotIn('operatingSystem', product)
        home = self.pages['/']
        nodes = [node for data in home.json for node in data.get('@graph', [])]
        item_list = next(node for node in nodes if node.get('@type') == 'ItemList')
        self.assertEqual(item_list['numberOfItems'], sum(a.get('listed', True) for a in apps))
        self.assertNotIn('FAQPage', [node.get('@type') for node in nodes])


class BuildSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='daily-apps-safety-')
        self.base = Path(self.temporary.name)
        self.source = fixture_source(self.base)
        self.output = self.base / 'output'
        self.output.mkdir()
        self.marker = self.output / 'existing-marker'
        self.marker.write_text('Keep the previous successful build.', encoding='utf-8')

    def tearDown(self):
        self.temporary.cleanup()

    def assert_rejected(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.marker.is_file(), 'Previous build was deleted after invalid input')
        self.assertEqual(self.marker.read_text(encoding='utf-8'),
                         'Keep the previous successful build.')

    def test_invalid_origins_fail_without_touching_previous_build(self):
        for origin in ('http://site.test', 'https://user:pass@site.test',
                       'https://site.test/path', 'https://site.test?x=1',
                       'https://site.test/#fragment', ' https://site.test',
                       'https://site.test\n', 'https://site.test:99999',
                       'https://site.test:bad', 'https://site.test\\evil'):
            with self.subTest(origin=origin):
                self.assert_rejected(run_build(self.source, self.output, origin=origin))

    def test_bad_catalogs_fail_before_any_output_change(self):
        original_apps = json.loads((self.source / 'apps.json').read_text(encoding='utf-8'))
        original_notes = json.loads((self.source / 'notes.json').read_text(encoding='utf-8'))
        cases = []
        for field, value in [('slug', '../../outside'), ('image', '/../secret.jpg'),
                             ('image', 'https://site.test/photo.jpg'),
                             ('image', '/images/does-not-exist.jpg'),
                             ('cardImage', '//site.test/photo.jpg'),
                             ('features', 'one feature'), ('listed', 'false'),
                             ('iosUrl', ''),
                             ('iosUrl', 'javascript:alert(1)'),
                             ('iosUrl', 'https://user:pass@apps.apple.com/app/id1'),
                             ('iosUrl', 'https://unrelated.test/app')]:
            apps = copy.deepcopy(original_apps)
            apps[0][field] = value
            cases.append((field + '=' + value, apps, original_notes))
        duplicate = copy.deepcopy(original_apps)
        duplicate.append(copy.deepcopy(duplicate[0]))
        cases.append(('duplicate app slug', duplicate, original_notes))
        notes = copy.deepcopy(original_notes)
        notes[0][0] = '../outside'
        cases.append(('note traversal', original_apps, notes))
        notes = copy.deepcopy(original_notes)
        notes.append(copy.deepcopy(notes[0]))
        cases.append(('duplicate note slug', original_apps, notes))
        cases.append(('catalog is not an array', {}, original_notes))
        for label, apps, notes in cases:
            with self.subTest(case=label):
                (self.source / 'apps.json').write_text(json.dumps(apps), encoding='utf-8')
                (self.source / 'notes.json').write_text(json.dumps(notes), encoding='utf-8')
                self.assert_rejected(run_build(self.source, self.output))

    def test_source_directories_are_protected_from_output_deletion(self):
        sentinel = self.source / 'public' / 'do-not-delete.txt'
        sentinel.write_text('source asset', encoding='utf-8')
        for output in (self.source, self.source / 'public', self.source / 'src', self.base):
            with self.subTest(output=output):
                self.assertNotEqual(run_build(self.source, output).returncode, 0)
                self.assertEqual(sentinel.read_text(encoding='utf-8'), 'source asset')
        linked = self.base / 'linked-output'
        linked.symlink_to(self.source / 'public', target_is_directory=True)
        self.assertNotEqual(run_build(self.source, linked).returncode, 0)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'source asset')

    def test_nested_output_symlink_cannot_redirect_publish_into_sources(self):
        protected = self.source / 'public' / 'do-not-overwrite'
        protected.mkdir()
        sentinel = protected / 'sentinel.txt'
        sentinel.write_text('source data', encoding='utf-8')
        (self.output / 'apps').symlink_to(protected, target_is_directory=True)
        before = {file.relative_to(protected).as_posix(): file.read_bytes()
                  for file in protected.rglob('*') if file.is_file()}
        self.assert_rejected(run_build(self.source, self.output))
        after = {file.relative_to(protected).as_posix(): file.read_bytes()
                 for file in protected.rglob('*') if file.is_file()}
        self.assertEqual(before, after, 'Publishing followed a nested output symlink')

    def test_invalid_owned_file_manifest_cannot_remove_files_outside_output(self):
        external = self.base / 'external.txt'
        external.write_text('unrelated file', encoding='utf-8')
        (self.output / '.site-build-manifest.json').write_text(
            json.dumps(['../external.txt']), encoding='utf-8')
        self.assert_rejected(run_build(self.source, self.output))
        self.assertEqual(external.read_text(encoding='utf-8'), 'unrelated file')

    def test_cloudflare_requires_explicit_production_origin(self):
        result = run_build(self.source, self.output, origin=None, extra_env={
            'CF_PAGES': '1', 'CF_PAGES_URL': 'https://daily-apps-production.pages.dev'})
        self.assert_rejected(result)

    def test_preview_build_is_noindex_with_empty_sitemap(self):
        result = run_build(self.source, self.output, extra_env={'SITE_NOINDEX': '1'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for file in self.output.rglob('*.html'):
            page = Page(file.read_text(encoding='utf-8'))
            self.assertIn('noindex', page.meta('robots')[0], file.as_posix())
        urls = list(ET.parse(self.output / 'sitemap.xml').iter(
            '{http://www.sitemaps.org/schemas/sitemap/0.9}loc'))
        self.assertEqual(urls, [])

    def test_future_apps_render_and_removed_pages_do_not_survive_rebuild(self):
        apps = json.loads((self.source / 'apps.json').read_text(encoding='utf-8'))
        extra = copy.deepcopy(apps[0])
        extra.update(slug='future-tool', name='未來的小工具', seoTitle='未來的小工具 App')
        apps.append(extra)
        notes = json.loads((self.source / 'notes.json').read_text(encoding='utf-8'))
        extra_note = copy.deepcopy(notes[0])
        extra_note[0] = 'future-note'
        notes.append(extra_note)
        (self.source / 'apps.json').write_text(json.dumps(apps), encoding='utf-8')
        (self.source / 'notes.json').write_text(json.dumps(notes), encoding='utf-8')
        result = run_build(self.source, self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        future = self.output / 'apps' / 'future-tool' / 'index.html'
        future_note = self.output / 'notes' / 'future-note' / 'index.html'
        self.assertTrue(future.is_file())
        self.assertTrue(future_note.is_file())
        self.assertIn('未來的小工具', future.read_text(encoding='utf-8'))
        old_bundles = set((self.output / 'assets').glob('*.js'))
        (self.source / 'apps.json').write_text(json.dumps(apps[:-1]), encoding='utf-8')
        (self.source / 'notes.json').write_text(json.dumps(notes[:-1]), encoding='utf-8')
        result = run_build(self.source, self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(future.exists())
        self.assertFalse(future_note.exists())
        new_bundles = set((self.output / 'assets').glob('*.js'))
        self.assertTrue(new_bundles)
        self.assertTrue(old_bundles.isdisjoint(new_bundles), 'Stale hashed client bundles remain')
        self.assertTrue(self.marker.is_file(), 'Unrelated output files must be preserved')

    def test_compile_failure_keeps_entire_previous_build(self):
        result = run_build(self.source, self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        before = {file.relative_to(self.output).as_posix(): file.read_bytes()
                  for file in self.output.rglob('*') if file.is_file()}
        with (self.source / 'src' / 'App.jsx').open('a', encoding='utf-8') as handle:
            handle.write('\nexport const deliberatelyBroken = ;\n')
        result = run_build(self.source, self.output)
        self.assertNotEqual(result.returncode, 0)
        after = {file.relative_to(self.output).as_posix(): file.read_bytes()
                 for file in self.output.rglob('*') if file.is_file()}
        self.assertEqual(before, after)

    def test_verified_store_links_render_with_safe_external_link_attributes(self):
        apps = json.loads((self.source / 'apps.json').read_text(encoding='utf-8'))
        links = {'iosUrl': 'https://apps.apple.com/tw/app/id1234567890',
                 'androidUrl': 'https://play.google.com/store/apps/details?id=com.example.app&hl=zh_TW'}
        apps[0].update(links)
        (self.source / 'apps.json').write_text(json.dumps(apps), encoding='utf-8')
        result = run_build(self.source, self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = Page((self.output / 'apps' / apps[0]['slug'] / 'index.html').read_text(encoding='utf-8'))
        for value in links.values():
            anchor = next(a for a in page.attrs('a') if a.get('href') == value)
            self.assertEqual(anchor.get('target'), '_blank')
            self.assertTrue({'noopener', 'noreferrer'}.issubset(anchor.get('rel', '').split()))

    def test_catalog_text_is_escaped_in_html_and_jsonld(self):
        apps = json.loads((self.source / 'apps.json').read_text(encoding='utf-8'))
        text = '文字 </script><script id="injected">alert(1)</script> & "測試"'
        apps[0].update(name=text, description=text, seoTitle=text, features=[text])
        (self.source / 'apps.json').write_text(json.dumps(apps), encoding='utf-8')
        result = run_build(self.source, self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = Page((self.output / 'apps' / apps[0]['slug'] / 'index.html').read_text(encoding='utf-8'))
        self.assertEqual(page.title, text)
        self.assertEqual(page.meta('description'), [text])
        self.assertNotIn('injected', [attrs.get('id') for _, attrs in page.tags])
        product = next(node for data in page.json for node in data.get('@graph', [])
                       if node.get('@type') == 'SoftwareApplication')
        self.assertEqual(product['name'], text)


class CloudflarePackageTests(unittest.TestCase):
    def test_archives_are_reproducible_complete_and_use_requested_origin(self):
        with tempfile.TemporaryDirectory(prefix='daily-apps-package-') as temporary:
            base = Path(temporary)
            source = fixture_source(base)
            output = base / 'website.zip'
            command = [sys.executable, str(source / 'scripts/package-cloudflare.py'),
                       '--origin', ORIGIN, '--output', str(output)]
            env = os.environ.copy()
            env['SITE_NOINDEX'] = '1'
            result = subprocess.run(command, cwd=base, env=env,
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            first = output.read_bytes()
            # Archives must not inherit changing source-asset timestamps.
            for asset in (source / 'public').rglob('*'):
                if asset.is_file():
                    os.utime(asset, (1800000000, 1800000000))
            result = subprocess.run(command, cwd=base, env=env,
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(first, output.read_bytes())
            with ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertIn('index.html', names)
                self.assertIn('404.html', names)
                self.assertIn('_headers', names)
                self.assertTrue(any(name.startswith('assets/') and name.endswith('.js') for name in names))
                self.assertNotIn('dist/index.html', names)
                self.assertEqual(names, sorted(names))
                self.assertTrue(all(not name.startswith('/') and '..' not in Path(name).parts for name in names))
                for asset in (source / 'public').rglob('*'):
                    if asset.is_file():
                        relative = asset.relative_to(source / 'public').as_posix()
                        self.assertEqual(archive.read(relative), asset.read_bytes())
                page = Page(archive.read('index.html').decode('utf-8'))
                self.assertEqual(page.canonicals(), [ORIGIN + '/'])
                self.assertNotIn('noindex', page.meta('robots')[0])
                self.assertTrue(all(entry.date_time == (1980, 1, 1, 0, 0, 0) for entry in archive.infolist()))
            # A failed rebuild must leave the last successful upload bundle intact.
            (source / 'apps.json').write_text('[] not JSON', encoding='utf-8')
            result = subprocess.run(command, cwd=base, env=env,
                                    capture_output=True, text=True, timeout=60)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(first, output.read_bytes())
            self.assertEqual(list(base.glob('.cloudflare-*.zip')), [])

    def test_packager_rejects_destructive_outputs_and_invalid_origins(self):
        with tempfile.TemporaryDirectory(prefix='daily-apps-package-') as temporary:
            base = Path(temporary)
            source = fixture_source(base)
            for origin, output in [('https://site.test:bad', base / 'invalid.zip'),
                                   ('https://user@site.test', base / 'invalid.zip'),
                                   (ORIGIN, source / 'build.py'),
                                   (ORIGIN, source / 'dist' / 'bundle.zip'),
                                   (ORIGIN, source / 'public' / 'bundle.zip')]:
                with self.subTest(origin=origin, output=output):
                    result = subprocess.run([sys.executable, str(source / 'scripts/package-cloudflare.py'),
                                             '--origin', origin, '--output', str(output)],
                                            cwd=base, capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
