import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import { build } from 'esbuild';
import React from 'react';
import { renderToString } from 'react-dom/server';

const root = await fs.realpath(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'));
const out = path.resolve(process.env.SITE_OUTPUT_DIR || path.join(root, 'dist'));
const DEFAULT_ORIGIN = 'https://autocare-app-studio.t410002246.chatgpt.site';
const fail = message => { throw new Error(message); };
function httpsURL(value, label, originOnly = false) {
  if (typeof value !== 'string' || /[\s\\\u0000-\u001f\u007f]/u.test(value)) fail(`Invalid ${label}`);
  let parsed;
  try { parsed = new URL(value); } catch { fail(`Invalid ${label}`); }
  if (parsed.protocol !== 'https:' || !parsed.hostname || parsed.port === '0' || parsed.username || parsed.password ||
      (originOnly && (parsed.pathname !== '/' || parsed.search || parsed.hash))) fail(`Invalid ${label}: HTTPS URL required`);
  return parsed;
}
if (process.env.CF_PAGES && !process.env.SITE_ORIGIN) fail('Set SITE_ORIGIN to the confirmed production Pages origin before building');
const origin = httpsURL(process.env.SITE_ORIGIN || DEFAULT_ORIGIN, 'SITE_ORIGIN', true).origin;
const preview = process.env.SITE_NOINDEX === '1';
// Resolve existing ancestors too, so a symlink cannot disguise a source directory.
async function resolvedTarget(target) {
  try { return await fs.realpath(target); }
  catch (error) {
    if (error.code !== 'ENOENT') throw error;
    return path.join(await resolvedTarget(path.dirname(target)), path.basename(target));
  }
}
const resolvedOut = await resolvedTarget(out);
if (resolvedOut === path.parse(resolvedOut).root || root === resolvedOut || root.startsWith(resolvedOut + path.sep) ||
    (resolvedOut.startsWith(root + path.sep) && resolvedOut !== path.join(root, 'dist'))) fail('Output must not overwrite source directories');
const apps = JSON.parse(await fs.readFile(path.join(root, 'apps.json'), 'utf8'));
const articles = JSON.parse(await fs.readFile(path.join(root, 'notes.json'), 'utf8'));
const images = JSON.parse(await fs.readFile(path.join(root, 'image-metadata.json'), 'utf8'));
const text = (v, label) => { if (typeof v !== 'string' || !v.trim()) fail(`Invalid ${label}`); };
const slugs = new Set();
function slug(value, kind) {
  if (typeof value !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value) || slugs.has(kind + value)) fail(`Invalid or duplicate ${kind} slug`);
  slugs.add(kind + value);
}
async function localImage(value, label) {
  if (typeof value !== 'string' || !/^\/(?!\/)[a-zA-Z0-9/_-]+\.(?:jpe?g|png|webp|svg)$/.test(value)) fail(`Invalid local image: ${label}`);
  const file = await fs.realpath(path.join(root, 'public', value));
  if (!file.startsWith(path.join(root, 'public') + path.sep) || !(await fs.stat(file)).isFile()) fail(`Invalid local image: ${label}`);
}
if (!Array.isArray(apps) || !apps.length || !Array.isArray(articles)) fail('Catalogs must be arrays');
for (const app of apps) {
  if (!app || typeof app !== 'object') fail('Invalid app');
  slug(app.slug, 'app');
  for (const field of ['name', 'description', 'category', 'tagline']) text(app[field], field);
  if (app.listed !== undefined && typeof app.listed !== 'boolean') fail('listed must be boolean');
  if (!Array.isArray(app.features) || app.features.some(f => typeof f !== 'string' || !f.trim())) fail('features must be text entries');
  if (app.listed !== false) for (const field of ['image', 'cardImage']) await localImage(app[field], app.slug + ' ' + field);
  if (app.listed !== false) for (const field of ['seoTitle', 'schemaCategory', 'imageAlt']) text(app[field], field);
  for (const [field, host] of [['iosUrl', 'apps.apple.com'], ['androidUrl', 'play.google.com']]) {
    if (app[field] != null) {
      const target = httpsURL(app[field], field);
      if (target.hostname !== host || target.port) fail(`Invalid store hostname: ${field}`);
    }
  }
}
for (const note of articles) {
  if (!Array.isArray(note) || note.length !== 5) fail('Invalid note');
  slug(note[0], 'note');
  for (const v of note.slice(1, 4)) text(v, 'note text');
  if (!Array.isArray(note[4]) || !note[4].length || note[4].some(p => !Array.isArray(p) || p.length !== 2 || p.some(v => typeof v !== 'string' || !v.trim()))) fail('Invalid note paragraphs');
}
const listed = apps.filter(a => a.listed !== false);
const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const json = value => JSON.stringify(value).replace(/</g, '\\u003c');
const org = {'@type':'Organization','@id':origin+'/#organization',name:'日常 App',url:origin+'/'};
const website = {'@type':'WebSite','@id':origin+'/#website',name:'日常 App',url:origin+'/',inLanguage:'zh-Hant',publisher:{'@id':org['@id']}};
const breadcrumb = items => ({'@type':'BreadcrumbList',itemListElement:items.map(([name,p],i)=>({'@type':'ListItem',position:i+1,name,item:origin+p}))});
const pages = [{path:'/',title:'吉他調音器・汽機車保養・所得稅2027｜日常 App',description:'日常 App，從練琴、用車到年度事務，找到適合你的生活工具。認識獨立開發的吉他調音器、汽機車保養與所得稅2027，閱讀標準調音、保養週期與用車紀錄筆記。',image:'/images/guitar.jpg',pageType:'CollectionPage',graph:[{'@type':'ItemList',name:'日常 App 選集',numberOfItems:listed.length,itemListElement:listed.map((a,i)=>({'@type':'ListItem',position:i+1,name:a.name,url:origin+`/apps/${a.slug}/`}))}]}];
for (const a of apps) {
  const p = `/apps/${a.slug}/`;
  const application = {'@type':'SoftwareApplication','@id':origin+p+'#app',name:a.name,url:origin+p,description:a.description,applicationCategory:a.schemaCategory,inLanguage:'zh-Hant',image:origin+(a.image||'/drive.jpg')};
  if (a.platform) application.operatingSystem = a.platform;
  pages.push({path:p,title:a.seoTitle||a.name+'｜獨立產品概念',description:a.description,image:a.image||'/drive.jpg',imageAlt:a.imageAlt,noindex:a.listed===false,mainEntity:a.listed===false?null:application['@id'],graph:[breadcrumb([['首頁','/'],[a.name,p]]),...(a.listed===false?[]:[application])]});
}
pages.push({path:'/notes/',title:'生活筆記｜吉他調音與汽機車保養・日常 App',description:'閱讀吉他標準調音、汽車保養週期、維修紀錄與用車支出的入門筆記。從六條琴弦到每次出發，把實用的小知識融入生活。',pageType:'CollectionPage',graph:[breadcrumb([['首頁','/'],['生活筆記','/notes/']])]});
for (const [slug,category,title,description] of articles) {
  const p = `/notes/${slug}/`, image = slug==='guitar-standard-tuning'?'/images/guitar.jpg':'/drive.jpg';
  pages.push({path:p,title:title+'｜日常 App 生活筆記',description,image,article:true,mainEntity:origin+p+'#article',graph:[breadcrumb([['首頁','/'],['生活筆記','/notes/'],[title,p]]),{'@type':'Article','@id':origin+p+'#article',headline:title,description,articleSection:category,image:origin+image,inLanguage:'zh-Hant',mainEntityOfPage:{'@id':origin+p+'#webpage'},author:{'@id':org['@id']},publisher:{'@id':org['@id']}}]});
}
pages.push({path:'/privacy/',title:'隱私說明｜日常 App',description:'了解日常 App 產品介紹網站的資料使用方式、Google Fonts 與外部連結，以及各款 App 隱私政策的適用範圍。',graph:[breadcrumb([['首頁','/'],['隱私說明','/privacy/']])]});
pages.push({path:'/404.html',title:'找不到頁面｜日常 App',description:'回到日常 App 選集，探索吉他調音器、汽機車保養與所得稅2027。',noindex:true});
const verification = process.env.GOOGLE_SITE_VERIFICATION ?? 'baYzpitVeMcfKx5CBc7M2PPL-9_dE3GzjkUho9gdUN8';
const fonts = 'https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700;800;900&family=Noto+Serif+TC:wght@500;600;700&display=swap';
const artifacts = path.join(root, '.artifacts');
await fs.mkdir(artifacts, {recursive:true});
const workspace = await fs.mkdtemp(path.join(artifacts, 'render-'));
const stage = path.join(workspace, 'output');
try {
  const serverFile = path.join(workspace, 'render.mjs');
  await build({entryPoints:[path.join(root,'src/App.jsx')],outfile:serverFile,bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic'});
  const {default:App} = await import(serverFile);
  await fs.cp(path.join(root,'public'),stage,{recursive:true});
  const client = await build({entryPoints:[path.join(root,'src/client.jsx')],outdir:path.join(stage,'assets'),entryNames:'app-[hash]',bundle:true,minify:true,format:'esm',jsx:'automatic',metafile:true,target:['es2020'],define:{'process.env.NODE_ENV':'"production"'}});
  const clientPath = '/' + path.relative(stage,path.resolve(Object.keys(client.metafile.outputs).find(p=>p.endsWith('.js')))).split(path.sep).join('/');
  for (const page of pages) {
    const is404 = page.path === '/404.html', image = page.image || '/images/guitar.jpg', canonical = origin + page.path;
    const meta = images[image] || {}, imageAlt = page.imageAlt || (image.includes('guitar')?'暖色光線下的木吉他與彈奏雙手':'綠意道路旁的銀色汽車');
    const webpage = {'@type':page.pageType||'WebPage','@id':canonical+'#webpage',name:page.title,description:page.description,url:canonical,inLanguage:'zh-Hant',isPartOf:{'@id':website['@id']},primaryImageOfPage:{'@type':'ImageObject',url:origin+image,width:meta.width,height:meta.height}};
    if (page.mainEntity) webpage.mainEntity = {'@id':page.mainEntity};
    const content = renderToString(React.createElement(App,{path:page.path}));
    const html = `<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escape(page.title)}</title><meta name="description" content="${escape(page.description)}">
<meta name="robots" content="${page.noindex||preview?'noindex,follow':'index,follow,max-image-preview:large'}">
${verification?`<meta name="google-site-verification" content="${escape(verification)}">`:''}${is404?'':`<link rel="canonical" href="${escape(canonical)}">`}
<meta name="theme-color" content="#245448"><meta property="og:type" content="${page.article?'article':'website'}">
<meta property="og:locale" content="zh_TW"><meta property="og:site_name" content="日常 App">
<meta property="og:title" content="${escape(page.title)}"><meta property="og:description" content="${escape(page.description)}">
${is404?'':`<meta property="og:url" content="${escape(canonical)}">`}<meta property="og:image" content="${escape(origin+image)}"><meta property="og:image:alt" content="${escape(imageAlt)}">
${meta.width?`<meta property="og:image:width" content="${meta.width}"><meta property="og:image:height" content="${meta.height}"><meta property="og:image:type" content="${escape(meta.type)}">`:''}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${escape(page.title)}">
<meta name="twitter:description" content="${escape(page.description)}"><meta name="twitter:image" content="${escape(origin+image)}"><meta name="twitter:image:alt" content="${escape(imageAlt)}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="${fonts.replace(/&/g,'&amp;')}"><link rel="stylesheet" href="/style.css">
${is404?'':`<script type="application/ld+json">${json({'@context':'https://schema.org','@graph':[org,website,webpage,...page.graph||[]]})}</script>`}
</head><body><div id="root" data-path="${escape(page.path)}">${content}</div><script type="module" src="${clientPath}"></script></body></html>`;
    const file = is404 ? path.join(stage,'404.html') : path.join(stage,page.path.slice(1),'index.html');
    await fs.mkdir(path.dirname(file),{recursive:true}); await fs.writeFile(file,html,'utf8');
  }
  const indexed = pages.filter(p=>!p.noindex&&!preview);
  await fs.writeFile(path.join(stage,'sitemap.xml'),'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'+indexed.map(p=>`  <url><loc>${escape(origin+p.path)}</loc>${p.image?`<image:image><image:loc>${escape(origin+p.image)}</image:loc></image:image>`:''}</url>`).join('\n')+'\n</urlset>\n');
  await fs.writeFile(path.join(stage,'robots.txt'),`User-agent: *\nAllow: /\n\nSitemap: ${origin}/sitemap.xml\n`);
  await fs.writeFile(path.join(stage,'_headers'),'/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/404.html\n  X-Robots-Tag: noindex\n/apps/autocare/*\n  X-Robots-Tag: noindex\n');
  async function listFiles(dir, prefix='') {
    const found=[];
    for (const entry of await fs.readdir(dir,{withFileTypes:true})) {
      const name=prefix+entry.name;
      if(entry.isDirectory()) found.push(...await listFiles(path.join(dir,entry.name),name+'/'));
      else if(entry.isFile()) found.push(name);
      else fail('Static output must not contain symlinks');
    }
    return found.sort();
  }
  const files = await listFiles(stage), manifestName = '.site-build-manifest.json';
  let previous=[];
  try { previous=JSON.parse(await fs.readFile(path.join(out,manifestName),'utf8')); } catch(error) { if(error.code!=='ENOENT') throw error; }
  if (!Array.isArray(previous) || previous.some(p=>typeof p!=='string'||p.startsWith('/')||p.split('/').some(x=>!x||x==='.'||x==='..')||p.includes('\\'))) fail('Invalid output manifest');
  // Validate every destination parent before modifying output: a nested
  // symlink must never redirect a generated file or stale-file cleanup.
  for (const name of [...files, ...previous, manifestName]) {
    const parent = await resolvedTarget(path.dirname(path.join(out, name)));
    const expected = path.resolve(resolvedOut, path.dirname(name));
    if (parent !== expected) fail('Output contains a symbolic-link destination');
  }
  // Publish complete files and remove only files this builder previously owned.
  for(const name of [...files,manifestName]) {
    const dest=path.join(out,name), temporary=dest+'.'+randomUUID()+'.tmp';
    await fs.mkdir(path.dirname(dest),{recursive:true});
    if(name===manifestName) await fs.writeFile(temporary,JSON.stringify(files,null,2)+'\n');
    else await fs.copyFile(path.join(stage,name),temporary);
    await fs.rename(temporary,dest);
  }
  for(const name of previous) if(!files.includes(name)) await fs.rm(path.join(out,name),{force:true});
  console.log(`Built React website: ${indexed.length} indexable pages for ${origin}`);
} finally {
  await fs.rm(workspace,{recursive:true,force:true});
}
