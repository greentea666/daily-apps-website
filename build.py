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
                  f'<meta name="twitter:image" content="{E(ORIGIN + image)}"><meta property="og:image:alt" content="{E(title)}">') if image else ''
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
<nav class="navlinks" aria-label="主要導覽"><a href="/apps/vehicle-maintenance/">汽機車保養</a><a href="/apps/income-tax-2027/">所得稅2027</a><a href="/apps/guitar-tuner/">吉他調音器</a><a href="/notes/">生活筆記</a><a class="btn" href="/#apps">探索 App ↗</a></nav></header></div>
{body}<footer class="wrap footer"><div class="footer-top"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">＋</span>日常 App <small>EVERYDAY TOOLS</small></a><p>練一首歌，照顧愛車。讓工具，剛好融入生活。</p></div><nav class="footer-links" aria-label="頁尾導覽"><a href="/apps/vehicle-maintenance/">汽機車保養</a><a href="/apps/income-tax-2027/">所得稅2027</a><a href="/apps/guitar-tuner/">吉他調音器</a><a href="/notes/">生活筆記</a><a href="/privacy/">隱私說明</a></nav></div><div class="copyright"><span>© 2026 日常 App</span><span>吉他調音器 · 汽機車保養 · 所得稅2027</span></div></footer><script src="/app.js" defer></script></body></html>'''


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
    platform = E(app.get('platform') or '獨立開發 App')
    return f'''<article class="app-card photo-card" data-category="{E(app['category'])}"><a class="card-image-link" href="/apps/{E(app['slug'])}/" aria-label="認識{E(app['name'])}"><img src="{E(app['cardImage'])}" alt="{E(app['imageAlt'])}" width="640" height="420" loading="lazy" decoding="async"><span class="photo-card-number">0{index}</span></a><div class="app-content"><span class="tag">{E(app['category'])}</span><h3><a href="/apps/{E(app['slug'])}/">{E(app['name'])}</a></h3><p>{E(app['tagline'])}</p><div class="app-bottom"><small>{platform}</small><a class="text-link" href="/apps/{E(app['slug'])}/" aria-label="了解{E(app['name'])}">認識一下 ↗</a></div></div></article>'''


faq = [
    ('這裡可以找到哪些 App？', '這裡介紹吉他調音器、汽機車保養與所得稅2027。每款 App 都有獨立介紹頁，可以依音樂練習、用車生活與所得稅主題探索。'),
    ('如何查看 App 的詳細資訊？', '從 App 專區選擇產品，即可進入對應介紹頁。產品說明與下載連結將在各自頁面更新。'),
    ('未來還會新增其他 App 嗎？', '會。本站以多 App 專區整理產品，未來可以加入更多類別的應用程式，每款 App 都有自己的介紹頁。')]
faq_html = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq)
filters = ''.join(f'<button class="filter" data-filter="{E(cat)}" aria-pressed="false">{E(cat)}</button>'
                  for cat in dict.fromkeys(a['category'] for a in listed_apps))
cards = ''.join(app_card(a, i + 1) for i, a in enumerate(listed_apps))
article_links = ''.join(f'<a class="article-link" href="/notes/{E(slug)}/"><div><small>{E(cat)} · 生活筆記</small><h3>{E(title)}</h3></div><span aria-hidden="true">↗</span></a>' for slug, cat, title, description, paragraphs in articles)
ticker = ''.join(f'<a href="/apps/{E(a["slug"])}/"><small>0{i+1}</small>{E(a["name"])}<span>↗</span></a>' for i, a in enumerate(listed_apps))
home = f'''<main class="wrap" id="main-content"><section class="editorial-hero"><div class="editorial-copy"><div class="eyebrow"><span class="dot"></span> SMALL TOOLS, GOOD DAYS.</div><h1>讓日常，<br>多一點<span>剛剛好。</span></h1><p>練一首歌，照顧一台車，準備一年的大小事。<br>簡單的工具，放在剛好需要的地方。</p><div class="actions"><a class="btn" href="#apps">看看我們的 App ↓</a><a class="editorial-note" href="/notes/">讀一點生活筆記 ↗</a></div><div class="hero-signature"><span></span> 獨立開發，從自己的日常出發。</div></div><a href="/apps/guitar-tuner/" class="editorial-image"><img src="/images/guitar.jpg" width="1600" height="1067" alt="暖色光線下的木吉他與彈奏雙手" fetchpriority="high"><div class="editorial-image-caption"><small>IN TUNE WITH YOUR DAY</small><h2>留一點時間，<br>給喜歡的聲音。</h2><span>吉他調音器　↗</span></div></a></section><nav class="collection-index" aria-label="三款 App 快速導覽">{ticker}</nav>
<section id="apps" class="hub-apps"><div class="section-top"><div><div class="eyebrow">THE COLLECTION / APP 選集</div><h2>小事，也值得用心。</h2></div><p>從每天會遇到的事開始，<br>做一些自己也想用的工具。</p></div><div class="filters" aria-label="App 主題篩選"><button class="filter" data-filter="all" aria-pressed="true">全部 App</button>{filters}<button class="filter" data-filter="coming" aria-pressed="false">更多 App</button></div><div class="app-grid" id="app-list">{cards}<article class="coming hub-coming" data-category="coming"><div><span class="plus">＋</span><h3>下一個日常靈感，慢慢做。</h3><p>有新的作品，就在這裡和你分享。</p><small>MORE TO COME</small></div></article></div><p id="filter-status" role="status" class="filter-status"></p></section>
<div class="knowledge" id="knowledge"><div><div class="eyebrow">A FEW GOOD NOTES</div><h2>工具之外，<br>也聊聊日常。</h2><p>從六條琴弦，到每次出發。<br>把值得記住的小事，寫下來。</p><a class="text-link" href="/notes/">讀全部筆記 ↗</a></div><div>{article_links}</div></div>
<section class="faq-layout" id="faq"><div><div class="eyebrow">GOOD TO KNOW</div><h2>你可能想問的。</h2><p>關於這裡的 App 與後續更新。</p></div><div>{faq_html}</div></section><aside class="cta"><div><h2>找到一個，剛好用得上的。</h2><p>吉他調音器、汽機車保養、所得稅2027。</p></div><a class="btn light" href="#apps">探索 App ↑</a></aside></main>'''
item_list = {'@type': 'ItemList', 'name': '吉他調音器、汽機車保養與所得稅2027 App', 'numberOfItems': len(listed_apps),
             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': a['name'], 'url': ORIGIN + '/apps/' + a['slug'] + '/'} for i, a in enumerate(listed_apps)]}
write_page('/', '吉他調音器・汽機車保養・所得稅2027｜日常 App',
           '練一首歌，照顧愛車，準備年度事務。認識獨立開發的吉他調音器、汽機車保養與所得稅2027 App，找到剛好用得上的日常工具。', home,
           [item_list, {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}], '/images/guitar.jpg')

for app in apps:
    path = '/apps/' + app['slug'] + '/'
    if not app.get('listed', True):
        # Preserve the original concept URL for links already shared.
        description = app['description']
        body = f'''<main class="detail" id="main-content"><a class="text-link" href="/#apps">← 返回 App 專區</a><p><span class="badge">獨立產品概念</span></p><h1>{E(app['name'])}</h1><p>{E(description)}</p><h2>概念功能規劃</h2><ul>{''.join('<li>'+E(x)+'</li>' for x in app['features'])}</ul><div class="disclaimer">這是原先展示的產品概念；相關功能與示意畫面不代表本站其他 App 的實際產品。</div><p><a class="btn" href="/#apps">探索本站 App ↗</a></p></main>'''
        write_page(path, app['name'] + '｜獨立產品概念', description, body,
                   [breadcrumbs([('首頁', '/'), (app['name'], path)])])
        continue
    tax = app['slug'] == 'income-tax-2027'
    guitar = app['slug'] == 'guitar-tuner'
    badge = '音樂練習 · 獨立開發' if guitar else ('所得稅主題 App' if tax else '汽車與機車 · iOS App')
    if guitar:
        sections = '''<h2>拿起吉他，先不急著彈。</h2><p>聽聽每條弦，慢慢轉一下旋鈕。把音調好，再回到那首一直想練會的歌。</p><div class="release-panel guitar-panel"><span class="tag">吉他調音器</span><h3>今天，就從一個好聽的和弦開始。</h3><p>這是我自己做的吉他調音器。想把練琴前的小事，做成一個簡單的工具。</p></div><h2>六條弦，是每次練習的起點。</h2><p>一般六弦吉他的標準調音，從最粗到最細依序是 E、A、D、G、B、E。每次練習前，先留一點時間給調音，也留一點時間給自己。</p><p><a class="btn" href="/notes/guitar-standard-tuning/">認識吉他標準調音 ↗</a></p>'''
    elif tax:
        sections = '''<h2>年度所得稅，從關心開始。</h2><p>有些事，早一點放進計畫裡，心裡就多一點空間。「所得稅2027」，從關心自己的年度事務開始。</p><div class="release-panel tax-panel"><span class="tag">所得稅2027</span><h3>為年度事務，多留一點準備。</h3><p>不用等到忙起來，才想起這件事。留一點時間，慢慢準備。</p></div><h2>關於年度與產品資訊</h2><p>「所得稅2027」為 App 名稱。使用相關工具前，請確認產品說明中的適用年度與地區；實際申報資訊以主管機關公告為準。</p><p><a class="btn outline" href="/apps/vehicle-maintenance/">也認識汽機車保養 ↗</a></p>'''
    else:
        sections = '''<h2>四輪與兩輪，都是生活的一部分。</h2><p>平日代步，假日兜風。愛車陪你走了不少路，也值得被好好照顧。「汽機車保養」，從關心每次出發開始。</p><div class="release-panel"><span class="tag">汽機車保養 · iOS</span><h3>照顧愛車，也照顧生活的步調。</h3><p>從平日代步到假日遠行，四輪與兩輪都有各自的保養需求。認識汽機車保養，為愛車多留一份關心。</p></div><h2>從保養知識開始，照顧日常座駕。</h2><p>閱讀本站保養筆記，從基礎知識開始。各車款的保養週期與檢查項目，請依車主手冊及合格技師建議安排。</p><div class="actions"><a class="btn" href="/notes/">閱讀保養筆記 ↗</a><a class="btn outline" href="/apps/income-tax-2027/">也認識所得稅2027 ↗</a></div>'''
    feature_list = ('<h2>App 功能</h2><ul>' + ''.join('<li>' + E(x) + '</li>' for x in app.get('features', [])) + '</ul>') if app.get('features') else ''
    body = f'''<main class="product-page" id="main-content"><div class="wrap"><nav class="breadcrumb" aria-label="麵包屑"><a href="/">首頁</a><span>／</span><a href="/#apps">App 選集</a><span>／</span><span>{E(app['name'])}</span></nav><section class="product-hero"><div><div class="eyebrow">{badge}</div><h1>{E(app['name'])}</h1><p class="product-tagline">{E(app['tagline'])}</p><p class="product-intro">{E(app['description'])}</p>{download_links(app)}<a class="text-link" href="#app-story">多認識一點 ↓</a></div><img src="{E(app['image'])}" width="1200" height="800" alt="{E(app['imageAlt'])}" fetchpriority="high"></section></div><div class="detail product-story" id="app-story">{sections}{feature_list}<div class="more-apps"><span class="eyebrow">ALSO MADE FOR YOUR DAY</span><h2>也看看其他作品。</h2><div>{''.join('<a class="text-link" href="/apps/'+E(other['slug'])+'/">'+E(other['name'])+' ↗</a>' for other in listed_apps if other['slug']!=app['slug'])}</div></div><p class="detail-back"><a class="text-link" href="/#apps">← 探索全部 App</a></p></div></main>'''

    schema = {'@type': 'SoftwareApplication', '@id': ORIGIN + path + '#app', 'name': app['name'],
              'applicationCategory': app['schemaCategory'], 'description': app['description'],
              'url': ORIGIN + path, 'inLanguage': 'zh-Hant', 'image': ORIGIN + app['image']}
    if app.get('platform'):
        schema['operatingSystem'] = app['platform']
    write_page(path, app['seoTitle'], app['description'], body,
               [breadcrumbs([('首頁', '/'), (app['name'], path)]), schema], app['image'])

notes_body = f'''<main class="detail" id="main-content"><a class="text-link" href="/">← 返回首頁</a><p class="eyebrow">THE EVERYDAY JOURNAL</p><h1>生活筆記</h1><p>調好六條弦，照顧每一段路。記下一些生活裡用得上的小知識。</p>{article_links}<h2>探索主題 App</h2><p><a class="text-link" href="/apps/vehicle-maintenance/">汽機車保養 ↗</a>　<a class="text-link" href="/apps/income-tax-2027/">所得稅2027 ↗</a>　<a class="text-link" href="/apps/guitar-tuner/">吉他調音器 ↗</a></p></main>'''
write_page('/notes/', '生活筆記｜吉他調音與汽機車保養・日常 App', '閱讀吉他標準調音、汽機車保養週期與日常紀錄的小筆記，認識吉他調音器、汽機車保養和所得稅2027 App。', notes_body,
           [breadcrumbs([('首頁', '/'), ('生活筆記', '/notes/')])])
for slug, category, title, description, paragraphs in articles:
    path = '/notes/' + slug + '/'
    is_guitar = slug == 'guitar-standard-tuning'
    article_note = '本文介紹一般六弦吉他的標準調音。不同樂曲與樂器可能使用其他定弦方式。' if is_guitar else '本文提供一般保養資訊，實際檢查項目與週期請依車主手冊、原廠規範及合格技師建議安排。'
    article_app = 'guitar-tuner' if is_guitar else 'vehicle-maintenance'
    article_app_name = '吉他調音器' if is_guitar else '汽機車保養'
    body = f'''<main class="detail" id="main-content"><a class="text-link" href="/notes/">← 返回生活筆記</a><p><span class="badge">{E(category)} · 生活筆記</span></p><h1>{E(title)}</h1><p>{E(description)}</p>{''.join('<h2>'+E(h)+'</h2><p>'+E(p)+'</p>' for h, p in paragraphs)}<div class="disclaimer">{article_note}</div><p><a class="btn" href="/apps/{article_app}/">認識{article_app_name} App ↗</a></p></main>'''
    write_page(path, title + '｜日常 App 生活筆記', description, body,
               [breadcrumbs([('首頁', '/'), ('生活筆記', '/notes/'), (title, path)]),
                {'@type': 'Article', 'headline': title, 'description': description,
                 'inLanguage': 'zh-Hant', 'mainEntityOfPage': ORIGIN + path}])

privacy = '''<main class="detail" id="main-content"><a class="text-link" href="/">← 返回首頁</a><h1>隱私說明</h1><p>本頁適用於「日常 App」產品介紹網站。</p><h2>網站的資料使用</h2><p>本網站沒有註冊、聯絡表單、付款功能或分析與廣告追蹤程式。App 主題篩選僅在目前頁面中運作，不會儲存車輛、保養、所得或稅務資料。網站代管服務可能為安全與正常運作處理連線資訊，相關處理依代管平台政策辦理。</p><h2>字型與外部連結</h2><p>本網站透過 Google Fonts 載入字型，瀏覽器可能因此傳送 IP 位址及一般連線資訊。若點選外部產品或商店連結，請參閱該平台的隱私政策。</p><h2>各款 App 的隱私政策</h2><p>吉他調音器、汽機車保養與所得稅2027 的資料使用方式，應以各 App 的專屬隱私政策為準。本頁只說明產品介紹網站的資料處理。</p></main>'''
write_page('/privacy/', '隱私說明｜日常 App', '日常 App 產品介紹網站的資料使用與外部服務說明，涵蓋吉他調音器、汽機車保養及所得稅2027 介紹頁。', privacy,
           [breadcrumbs([('首頁', '/'), ('隱私說明', '/privacy/')])])
(OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>' + escape(ORIGIN + p) + '</loc></url>' for p in paths) + '</urlset>')
(OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap.xml\n')
(OUT / '404.html').write_text(shell('找不到頁面｜日常 App', '回到日常 App 專區探索吉他調音器、汽機車保養與所得稅2027。', '<main class="detail" id="main-content"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>這個頁面還沒準備好。</h1><p>回到 App 專區，探索吉他調音器、汽機車保養與所得稅2027。</p><p><a class="btn" href="/">返回首頁 ↗</a></p></main>', '/404.html').replace('content="index,follow"', 'content="noindex,follow"'))
print(f'Built {len(paths)} indexable pages for {ORIGIN}')
