"""Build the shared App website and its SEO files using the product catalog."""
import html
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get('SITE_OUTPUT_DIR', str(ROOT / 'dist')))
ORIGIN = os.environ.get('SITE_ORIGIN', 'https://autocare-app-studio.t410002246.chatgpt.site').rstrip('/')
if urlsplit(ORIGIN).scheme != 'https' or not urlsplit(ORIGIN).netloc:
    raise ValueError('SITE_ORIGIN must be an absolute HTTPS origin')
SITE_NAME = '日常 App'
VERIFY = 'baYzpitVeMcfKx5CBc7M2PPL-9_dE3GzjkUho9gdUN8'
apps = json.loads((ROOT / 'apps.json').read_text())
articles = json.loads((ROOT / 'notes.json').read_text())
listed_apps = [app for app in apps if app.get('listed', True)]
E = html.escape
OUT.mkdir(parents=True, exist_ok=True)
paths = []


def dump(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def breadcrumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': label, 'item': ORIGIN + path}
        for i, (label, path) in enumerate(items)]}


def shell(title, description, body, path='/', graph=None, image=None):
    site = {'@type': 'WebSite', '@id': ORIGIN + '/#website', 'name': SITE_NAME,
            'url': ORIGIN + '/', 'inLanguage': 'zh-Hant'}
    page = {'@type': 'WebPage', '@id': ORIGIN + path + '#webpage', 'url': ORIGIN + path,
            'name': title, 'description': description, 'inLanguage': 'zh-Hant',
            'isPartOf': {'@id': ORIGIN + '/#website'}}
    data = {'@context': 'https://schema.org', '@graph': [site, page] + (graph or [])}
    image_tags = (f'<meta property="og:image" content="{E(ORIGIN + image)}">'
                  f'<meta name="twitter:image" content="{E(ORIGIN + image)}">') if image else ''
    return f'''<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(description)}">
<meta name="google-site-verification" content="{VERIFY}"><meta name="robots" content="index,follow">
<link rel="canonical" href="{E(ORIGIN + path)}"><meta name="theme-color" content="#315d42">
<meta property="og:type" content="website"><meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="{SITE_NAME}"><meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}"><meta property="og:url" content="{E(ORIGIN + path)}">
<meta name="twitter:card" content="{'summary_large_image' if image else 'summary'}">
<meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(description)}">{image_tags}
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{dump(data)}</script></head><body>
<a class="skip-link" href="#main-content">跳至主要內容</a><div class="wrap"><header class="nav">
<a class="brand" href="/" aria-label="日常 App 首頁"><span class="brand-mark" aria-hidden="true">＋</span>日常 App <small>EVERYDAY TOOLS</small></a>
<nav class="navlinks" aria-label="主要導覽"><a href="/apps/vehicle-maintenance/">汽機車保養</a><a href="/apps/income-tax-2027/">所得稅2027</a><a href="/notes/">生活筆記</a><a class="btn" href="/#apps">探索 App ↗</a></nav></header></div>
{body}<footer class="wrap footer"><div class="footer-top"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">＋</span>日常 App <small>EVERYDAY TOOLS</small></a><p>從照顧愛車，到年度所得稅。為生活，多想一步。</p></div><nav class="footer-links" aria-label="頁尾導覽"><a href="/apps/vehicle-maintenance/">汽機車保養</a><a href="/apps/income-tax-2027/">所得稅2027</a><a href="/notes/">生活筆記</a><a href="/privacy/">隱私說明</a></nav></div><div class="copyright"><span>© 2026 日常 App</span><span>汽機車保養 · 所得稅2027 · 更多生活應用</span></div></footer><script src="/app.js" defer></script></body></html>'''


def write_page(path, title, description, body, graph=None, image=None):
    target = OUT / path.strip('/') / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(shell(title, description, body, path, graph, image))
    paths.append(path)


def download_links(app):
    links = []
    for field, label in [('iosUrl', '前往 App Store'), ('androidUrl', '前往 Google Play')]:
        url = app.get(field)
        if not url:
            continue
        if urlsplit(url).scheme != 'https' or not urlsplit(url).netloc:
            raise ValueError(f'Invalid download URL for {app["name"]}')
        links.append(f'<a class="btn" href="{E(url, quote=True)}" target="_blank" rel="noopener noreferrer">{label} ↗</a>')
    return '<div class="actions">' + ''.join(links) + '</div>' if links else ''


def app_card(app, index):
    symbol = E(app.get('symbol', '＋'))
    tone = 'tax-art' if app['slug'] == 'income-tax-2027' else 'care-art'
    platform = E(app.get('platform') or 'App 介紹')
    return f'''<article class="app-card" data-category="{E(app['category'])}"><div class="app-art {tone}"><span class="app-art-index">0{index} / DAILY COLLECTION</span><div class="app-logo" aria-hidden="true">{symbol}</div></div><div class="app-content"><span class="tag">{E(app['category'])}</span><h3><a href="/apps/{E(app['slug'])}/">{E(app['name'])}</a></h3><p>{E(app['tagline'])}</p><div class="app-bottom"><small>{platform}</small><a class="text-link" href="/apps/{E(app['slug'])}/" aria-label="了解{E(app['name'])}">了解 App ↗</a></div></div></article>'''


faq = [
    ('這裡可以找到哪些 App？', '這裡集中介紹「汽機車保養」與「所得稅2027」。各款 App 均有獨立介紹頁，方便依用車生活或所得稅主題探索。'),
    ('如何查看 App 的詳細資訊？', '從 App 專區選擇產品，即可進入對應介紹頁。產品說明與下載連結將在各自頁面更新。'),
    ('未來還會新增其他 App 嗎？', '會。本站以多 App 專區整理產品，未來可以加入更多類別的應用程式，每款 App 都有自己的介紹頁。')]
faq_html = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq)
filters = ''.join(f'<button class="filter" data-filter="{E(cat)}" aria-pressed="false">{E(cat)}</button>'
                  for cat in dict.fromkeys(a['category'] for a in listed_apps))
cards = ''.join(app_card(a, i + 1) for i, a in enumerate(listed_apps))
article_links = ''.join(f'<a class="article-link" href="/notes/{E(slug)}/"><div><small>{E(cat)} · 保養筆記</small><h3>{E(title)}</h3></div><span aria-hidden="true">↗</span></a>' for slug, cat, title, description, paragraphs in articles)
home = f'''<main class="wrap" id="main-content"><section class="hub-hero"><div class="eyebrow"><span class="dot"></span> EVERYDAY APPS / 生活裡的好幫手</div><div class="hero-top"><div><h1>生活的大小事，<br>找到<span>順手的 App。</span></h1><p>從汽車、機車的保養日常，到年度所得稅主題。<br>一起認識「汽機車保養」與「所得稅2027」。</p><div class="actions"><a class="btn" href="#apps">探索兩款 App ↓</a><a class="btn outline" href="/notes/">閱讀生活筆記 ↗</a></div></div><aside class="hero-side"><div class="number">02 /</div><strong>不同需求，同一個入口。</strong><p>為愛車多留一份關心，也為年度事務多做一點準備。</p></aside></div><div class="hub-ticker"><a href="/apps/vehicle-maintenance/">01　汽機車保養 <span>↗</span></a><a href="/apps/income-tax-2027/">02　所得稅2027 <span>↗</span></a></div></section>
<section id="apps" class="hub-apps"><div class="section-top"><div><div class="eyebrow">THE APP COLLECTION</div><h2>兩種日常，一起照顧。</h2></div><p>選擇你關心的主題，<br>找到對應 App 的完整介紹。</p></div><div class="filters" aria-label="App 主題篩選"><button class="filter" data-filter="all" aria-pressed="true">全部 App</button>{filters}<button class="filter" data-filter="coming" aria-pressed="false">更多 App</button></div><div class="app-grid" id="app-list">{cards}<article class="coming hub-coming" data-category="coming"><div><span class="plus">＋</span><h3>更多日常，也值得被照顧。</h3><p>未來在這裡發現更多不同主題的 App。</p><small>MORE APPS, MORE POSSIBILITIES</small></div></article></div><p id="filter-status" role="status" class="filter-status"></p></section>
<div class="knowledge" id="knowledge"><div><div class="eyebrow">THE EVERYDAY JOURNAL</div><h2>從實用筆記，<br>認識生活的小事。</h2><p>先從汽機車保養知識開始，<br>整理每一次照顧愛車的日常。</p><a class="text-link" href="/notes/">閱讀全部筆記 ↗</a></div><div>{article_links}</div></div>
<section class="faq-layout" id="faq"><div><div class="eyebrow">GOOD TO KNOW</div><h2>探索之前，<br>你可能想知道。</h2><p>App 專區與產品資訊。</p></div><div>{faq_html}</div></section><aside class="cta"><div><h2>讓關心的日常，有個專屬入口。</h2><p>汽機車保養與所得稅2027，從你需要的主題開始。</p></div><a class="btn light" href="#apps">探索 App ↑</a></aside></main>'''
item_list = {'@type': 'ItemList', 'name': '汽機車保養與所得稅2027 App', 'numberOfItems': len(listed_apps),
             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': a['name'],
                                  'url': ORIGIN + '/apps/' + a['slug'] + '/'} for i, a in enumerate(listed_apps)]}
write_page('/', '汽機車保養、所得稅2027 App｜日常 App 專區',
           '一次認識汽機車保養與所得稅2027 App。依用車生活與所得稅主題探索獨立產品介紹，閱讀保養筆記，發現更多生活應用。', home,
           [item_list, {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}])

for app in apps:
    path = '/apps/' + app['slug'] + '/'
    if not app.get('listed', True):
        # Preserve the original concept URL for links already shared.
        description = app['description']
        body = f'''<main class="detail" id="main-content"><a class="text-link" href="/#apps">← 返回 App 專區</a><p><span class="badge">獨立產品概念</span></p><h1>{E(app['name'])}</h1><p>{E(description)}</p><h2>概念功能規劃</h2><ul>{''.join('<li>'+E(x)+'</li>' for x in app['features'])}</ul><div class="disclaimer">這是原先展示的產品概念；相關功能與示意畫面不代表汽機車保養或所得稅2027 的實際產品。</div><p><a class="btn" href="/#apps">探索本站 App ↗</a></p></main>'''
        write_page(path, app['name'] + '｜獨立產品概念', description, body,
                   [breadcrumbs([('首頁', '/'), (app['name'], path)])])
        continue
    tax = app['slug'] == 'income-tax-2027'
    badge = '所得稅主題 App' if tax else '汽車與機車 · iOS App'
    if tax:
        sections = '''<h2>年度所得稅，從關心開始。</h2><p>每到處理年度事務的時刻，提早認識相關工具，是準備的第一步。這裡是「所得稅2027」的專屬產品介紹頁，集中整理 App 的相關資訊。</p><div class="release-panel tax-panel"><span class="tag">所得稅2027</span><h3>為年度事務，多留一點準備。</h3><p>讓所得稅主題與日常需求，在同一個 App 專區找到入口。</p></div><h2>關於年度與產品資訊</h2><p>「所得稅2027」為 App 名稱。使用相關工具前，請確認產品說明中的適用年度與地區；實際申報資訊以主管機關公告為準。</p><p><a class="btn outline" href="/apps/vehicle-maintenance/">也認識汽機車保養 ↗</a></p>'''
    else:
        sections = '''<h2>四輪與兩輪，都是生活的一部分。</h2><p>日常通勤、週末出遊，每一段路都有愛車相伴。「汽機車保養」以汽車與機車保養為主題，讓保養成為日常關心的一部分。</p><div class="release-panel"><span class="tag">汽機車保養 · iOS</span><h3>照顧愛車，也照顧生活的步調。</h3><p>從平日代步到假日遠行，四輪與兩輪都有各自的保養需求。認識汽機車保養，為愛車多留一份關心。</p></div><h2>從保養知識開始，照顧日常座駕。</h2><p>閱讀本站保養筆記，從基礎知識開始。各車款的保養週期與檢查項目，請依車主手冊及合格技師建議安排。</p><div class="actions"><a class="btn" href="/notes/">閱讀保養筆記 ↗</a><a class="btn outline" href="/apps/income-tax-2027/">也認識所得稅2027 ↗</a></div>'''
    feature_list = ('<h2>App 功能</h2><ul>' + ''.join('<li>' + E(x) + '</li>' for x in app.get('features', [])) + '</ul>') if app.get('features') else ''
    body = f'''<main class="detail" id="main-content"><nav class="breadcrumb" aria-label="麵包屑"><a href="/">首頁</a><span>／</span><a href="/#apps">App 專區</a><span>／</span><span>{E(app['name'])}</span></nav><p><span class="badge">{badge}</span></p><h1>{E(app['name'])}<span class="detail-subtitle">{E(app['tagline'])}</span></h1><p>{E(app['description'])}</p>{download_links(app)}{sections}{feature_list}<p class="detail-back"><a class="text-link" href="/#apps">← 探索全部 App</a></p></main>'''
    schema = {'@type': 'SoftwareApplication', '@id': ORIGIN + path + '#app', 'name': app['name'],
              'applicationCategory': app['schemaCategory'], 'description': app['description'],
              'url': ORIGIN + path, 'inLanguage': 'zh-Hant'}
    if app.get('platform'):
        schema['operatingSystem'] = app['platform']
    write_page(path, app['seoTitle'], app['description'], body,
               [breadcrumbs([('首頁', '/'), (app['name'], path)]), schema], '/drive.jpg' if not tax else None)

notes_body = f'''<main class="detail" id="main-content"><a class="text-link" href="/">← 返回首頁</a><p class="eyebrow">THE EVERYDAY JOURNAL</p><h1>生活筆記</h1><p>從汽機車保養的基礎知識開始，整理照顧愛車的日常。</p>{article_links}<h2>探索主題 App</h2><p><a class="text-link" href="/apps/vehicle-maintenance/">汽機車保養 ↗</a>　<a class="text-link" href="/apps/income-tax-2027/">所得稅2027 ↗</a></p></main>'''
write_page('/notes/', '生活筆記｜汽機車保養知識・日常 App', '閱讀汽機車保養週期、維修紀錄整理與用車花費的基礎筆記，並探索汽機車保養及所得稅2027 App。', notes_body,
           [breadcrumbs([('首頁', '/'), ('生活筆記', '/notes/')])])
for slug, category, title, description, paragraphs in articles:
    path = '/notes/' + slug + '/'
    body = f'''<main class="detail" id="main-content"><a class="text-link" href="/notes/">← 返回生活筆記</a><p><span class="badge">{E(category)} · 保養基礎知識</span></p><h1>{E(title)}</h1><p>{E(description)}</p>{''.join('<h2>'+E(h)+'</h2><p>'+E(p)+'</p>' for h, p in paragraphs)}<div class="disclaimer">本文提供一般保養資訊，實際檢查項目與週期請依車主手冊、原廠規範及合格技師建議安排。</div><p><a class="btn" href="/apps/vehicle-maintenance/">認識汽機車保養 App ↗</a></p></main>'''
    write_page(path, title + '｜日常 App 保養筆記', description, body,
               [breadcrumbs([('首頁', '/'), ('生活筆記', '/notes/'), (title, path)]),
                {'@type': 'Article', 'headline': title, 'description': description,
                 'inLanguage': 'zh-Hant', 'mainEntityOfPage': ORIGIN + path}])

privacy = '''<main class="detail" id="main-content"><a class="text-link" href="/">← 返回首頁</a><h1>隱私說明</h1><p>本頁適用於「日常 App」產品介紹網站。</p><h2>網站的資料使用</h2><p>本網站沒有註冊、聯絡表單、付款功能或分析與廣告追蹤程式。App 主題篩選僅在目前頁面中運作，不會儲存車輛、保養、所得或稅務資料。網站代管服務可能為安全與正常運作處理連線資訊，相關處理依代管平台政策辦理。</p><h2>字型與外部連結</h2><p>本網站透過 Google Fonts 載入字型，瀏覽器可能因此傳送 IP 位址及一般連線資訊。若點選外部產品或商店連結，請參閱該平台的隱私政策。</p><h2>各款 App 的隱私政策</h2><p>汽機車保養與所得稅2027 的資料使用方式，應以各 App 的專屬隱私政策為準。本頁只說明產品介紹網站的資料處理。</p></main>'''
write_page('/privacy/', '隱私說明｜日常 App', '日常 App 產品介紹網站的資料使用與外部服務說明，涵蓋汽機車保養及所得稅2027 介紹頁。', privacy,
           [breadcrumbs([('首頁', '/'), ('隱私說明', '/privacy/')])])
(OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + escape(ORIGIN + p) + '</loc></url>' for p in paths) + '</urlset>')
(OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap.xml\n')
(OUT / '404.html').write_text(shell('找不到頁面｜日常 App', '回到日常 App 專區探索汽機車保養與所得稅2027。', '<main class="detail" id="main-content"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>這個頁面還沒準備好。</h1><p>回到 App 專區，探索汽機車保養與所得稅2027。</p><p><a class="btn" href="/">返回首頁 ↗</a></p></main>', '/404.html').replace('content="index,follow"', 'content="noindex,follow"'))
print(f'Built {len(paths)} indexable pages for {ORIGIN}')
