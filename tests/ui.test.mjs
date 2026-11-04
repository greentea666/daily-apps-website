import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { after, before, test } from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from 'esbuild';
import { JSDOM } from 'jsdom';
import React, { act } from 'react';
import { renderToString } from 'react-dom/server';

// jsdom verifies HTML and React behavior, not CSS breakpoints or visual layout.
const project = fileURLToPath(new URL('../', import.meta.url));
let temporaryDirectory;
let App;
let catalog;

before(async () => {
  await fs.mkdir(path.join(project, '.artifacts'), { recursive: true });
  temporaryDirectory = await fs.mkdtemp(path.join(project, '.artifacts', 'ui-tests-'));
  const bundle = path.join(temporaryDirectory, 'app.mjs');
  await build({
    entryPoints: [path.join(project, 'src/App.jsx')],
    outfile: bundle,
    bundle: true,
    platform: 'node',
    format: 'esm',
    packages: 'external',
    jsx: 'automatic',
  });
  ({ default: App, catalog } = await import(pathToFileURL(bundle).href));
});

after(async () => {
  if (temporaryDirectory) await fs.rm(temporaryDirectory, { recursive: true, force: true });
});

async function withPage(route, run) {
  const html = renderToString(React.createElement(App, { path: route }));
  const dom = new JSDOM('<!doctype html><html lang="zh-Hant"><body><div id="root"></div></body></html>', {
    url: `https://example.test${route}`,
  });
  const container = dom.window.document.querySelector('#root');
  container.innerHTML = html;
  const globals = {
    window: dom.window,
    document: dom.window.document,
    navigator: dom.window.navigator,
    HTMLElement: dom.window.HTMLElement,
    Node: dom.window.Node,
    IS_REACT_ACT_ENVIRONMENT: true,
  };
  const previous = new Map(Object.keys(globals).map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  for (const [key, value] of Object.entries(globals)) {
    Object.defineProperty(globalThis, key, { value, writable: true, configurable: true });
  }
  let root;
  try {
    await run({
      document: dom.window.document,
      window: dom.window,
      container,
      hydrate: async options => {
        const { hydrateRoot } = await import('react-dom/client');
        await act(async () => {
          root = hydrateRoot(container, React.createElement(App, { path: route }), options);
        });
      },
    });
  } finally {
    if (root) await act(async () => root.unmount());
    dom.window.close();
    for (const [key, descriptor] of previous) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor);
      else delete globalThis[key];
    }
  }
}

test('SSR exposes mobile navigation links while its inactive menu button stays hidden', async () => {
  await withPage('/', async ({ document }) => {
    const menu = document.querySelector('#mobile-menu');
    const button = document.querySelector('.menu-button');
    assert.equal(button.hidden, true);
    assert.equal(button.getAttribute('aria-expanded'), 'false');
    assert.equal(button.getAttribute('aria-controls'), menu.id);
    assert.equal(menu.hidden, false);
    assert.equal(menu.closest('[hidden]'), null);
    assert.deepEqual(
      [...menu.querySelectorAll('a')].map(link => link.getAttribute('href')),
      [...catalog.map(app => `/apps/${app.slug}/`), '/notes/'],
    );
    for (const link of menu.querySelectorAll('a')) assert.ok(link.textContent.trim());
    assert.equal(document.querySelectorAll('#app-list .photo-card').length, catalog.length);
  });
});

test('hydration preserves server-rendered content without recoverable or console errors', async () => {
  const routes = ['/', '/apps/guitar-tuner/', '/apps/vehicle-maintenance/', '/apps/income-tax-2027/',
    '/notes/', '/notes/guitar-standard-tuning/', '/privacy/', '/unknown-route/'];
  const consoleErrors = [];
  const originalError = console.error;
  console.error = (...args) => consoleErrors.push(args.map(String).join(' '));
  try {
    for (const route of routes) {
      await withPage(route, async ({ document, hydrate }) => {
        const main = document.querySelector('main');
        const content = main.textContent;
        const recoverableErrors = [];
        await hydrate({ onRecoverableError: error => recoverableErrors.push(error.message) });
        assert.equal(document.querySelector('main'), main, `${route}: hydration replaced the main element`);
        assert.equal(main.textContent, content, `${route}: hydration changed server-rendered content`);
        assert.deepEqual(recoverableErrors, [], `${route}: recoverable hydration errors`);
        assert.equal(document.querySelector('.menu-button').hidden, false);
        assert.equal(document.querySelector('#mobile-menu').hidden, true);
      });
    }
    assert.deepEqual(consoleErrors, []);
  } finally {
    console.error = originalError;
  }
});

test('hydrated mobile menu toggles its state and Escape closes it with focus restored', async () => {
  await withPage('/', async ({ document, window, hydrate }) => {
    await hydrate();
    const button = document.querySelector('.menu-button');
    const menu = document.querySelector('#mobile-menu');
    assert.equal(button.getAttribute('aria-expanded'), 'false');
    assert.equal(menu.hidden, true);
    await act(async () => button.click());
    assert.equal(button.getAttribute('aria-expanded'), 'true');
    assert.equal(menu.hidden, false);
    menu.querySelector('a').focus();
    await act(async () => document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
    assert.equal(button.getAttribute('aria-expanded'), 'false');
    assert.equal(menu.hidden, true);
    assert.equal(document.activeElement, button);
    await act(async () => button.click());
    await act(async () => button.click());
    assert.equal(button.getAttribute('aria-expanded'), 'false');
    assert.equal(menu.hidden, true);
  });
});

test('App category filters update real cards, pressed state and the live result status', async () => {
  await withPage('/', async ({ document, hydrate }) => {
    await hydrate();
    const buttons = [...document.querySelectorAll('.filters button')];
    const list = document.querySelector('#app-list');
    const status = document.querySelector('.filter-status');
    assert.equal(document.querySelector('.filters').getAttribute('role'), 'group');
    assert.equal(status.getAttribute('role'), 'status');
    assert.equal(status.getAttribute('aria-live'), 'polite');
    for (const button of buttons.slice(1)) {
      const category = button.textContent;
      const expected = catalog.filter(app => app.category === category);
      await act(async () => button.click());
      assert.deepEqual([...list.querySelectorAll('h3')].map(heading => heading.textContent), expected.map(app => app.name));
      assert.equal(button.getAttribute('aria-controls'), list.id);
      assert.deepEqual(buttons.filter(item => item.getAttribute('aria-pressed') === 'true'), [button]);
      assert.ok(status.textContent.includes(String(expected.length)));
      assert.ok(status.textContent.includes(category));
    }
    await act(async () => buttons[0].click());
    assert.deepEqual([...list.querySelectorAll('h3')].map(heading => heading.textContent), catalog.map(app => app.name));
    assert.deepEqual(buttons.filter(item => item.getAttribute('aria-pressed') === 'true'), [buttons[0]]);
    assert.ok(status.textContent.includes(String(catalog.length)));
  });
});
