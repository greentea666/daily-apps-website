import React, { useEffect, useState } from 'react';
import apps from '../apps.json';
import articles from '../notes.json';
import imageMetadata from '../image-metadata.json';

export const catalog = apps.filter(app => app.listed !== false);
export const faq = [
  ['日常 App 是什麼？', '日常 App 是獨立開發的產品介紹網站，整理吉他調音器、汽機車保養與所得稅2027。從音樂練習、用車生活到年度事務，每款產品都有自己的介紹頁與相關資訊。'],
  ['可以在哪裡下載 App？', '請查看各產品介紹頁的下載區。目前本站尚未提供已確認的商店連結；正式下載資訊會於確認後更新。支援裝置、價格與功能，請以正式商店頁面為準。'],
  ['生活筆記可以讀到什麼？', '這裡整理吉他標準調音、汽車保養週期、維修紀錄與用車支出等入門筆記。你可以先從自己的需求開始閱讀，再探索相關產品。'],
  ['頁面上的照片是 App 畫面嗎？', '首頁與產品封面使用生活情境照片；汽機車保養介紹頁另有標示清楚的 App 模擬器截圖，畫面中的車輛與紀錄均為範例資料。'],
];
const pathFor = app => `/apps/${app.slug}/`;
const topics = [
  ['01 / MUSIC', '給想好好練琴的你', '從 E A D G B E 開始，認識標準調音與練習前的準備。', '探索吉他調音', 'guitar-tuner'],
  ['02 / ON THE ROAD', '給在意每次出發的你', '讀懂保養週期，整理維修紀錄，慢慢建立照顧愛車的習慣。', '探索汽機車保養', 'vehicle-maintenance'],
  ['03 / YEARLY PLANS', '給喜歡提早準備的你', '認識所得稅2027，查看產品介紹與年度資訊說明。', '探索年度事務', 'income-tax-2027'],
];
function Photo({ src, alt, sizes = '(max-width: 800px) 100vw, 50vw', priority = false, ...props }) {
  const meta = imageMetadata[src] || { width: 1200, height: 800 };
  const srcSet = meta.variants?.map(v => `${v.src} ${v.width}w`).join(', ');
  return <img {...props} src={src} alt={alt} width={meta.width} height={meta.height} srcSet={srcSet || undefined} sizes={srcSet ? sizes : undefined} decoding="async" loading={priority ? 'eager' : 'lazy'} fetchPriority={priority ? 'high' : undefined}/>;
}
function Brand() { return <a className="brand" href="/" aria-label="日常 App 首頁"><span className="brand-mark" aria-hidden="true">＋</span>日常 App <small>EVERYDAY TOOLS</small></a>; }
function Header() {
  const [open, setOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => { setHydrated(true); }, []);
  useEffect(() => {
    const close = event => { if (event.key === 'Escape') { setOpen(false); document.querySelector('.menu-button')?.focus(); } };
    if (open) document.addEventListener('keydown', close);
    return () => document.removeEventListener('keydown', close);
  }, [open]);
  return <header className="wrap"><div className="nav"><Brand/><nav className="navlinks" aria-label="主要導覽">{catalog.map(a => <a key={a.slug} href={pathFor(a)}>{a.name}</a>)}<a href="/notes/">生活筆記</a><a className="btn" href="/#apps">探索 App ↗</a></nav><button type="button" hidden={!hydrated} className="menu-button" aria-expanded={open} aria-controls="mobile-menu" onClick={() => setOpen(!open)}>{open ? '關閉 −' : '選單 ＋'}</button></div><nav id="mobile-menu" className="mobile-menu" aria-label="手機導覽" hidden={hydrated && !open}>{catalog.map(a=><a key={a.slug} href={pathFor(a)}>{a.name} ↗</a>)}<a href="/notes/">生活筆記 ↗</a></nav></header>;
}
function Footer() { return <footer className="wrap footer"><div className="footer-top"><div><Brand/><p>練一首歌，照顧愛車。讓工具，剛好融入生活。</p></div><nav className="footer-links" aria-label="頁尾導覽">{catalog.map(a=><a key={a.slug} href={pathFor(a)}>{a.name}</a>)}<a href="/notes/">生活筆記</a><a href="/privacy/">隱私說明</a></nav></div><div className="copyright"><span>© 2026 日常 App</span><span>獨立開發，從自己的日常出發。</span></div></footer>; }
function Eyebrow({ children }) { return <div className="eyebrow">{children}</div>; }
function ArticleLinks({ items = articles }) { return <>{items.map(([slug,category,title])=><a key={slug} className="article-link" href={`/notes/${slug}/`}><div><small>{category} · 生活筆記</small><h3>{title}</h3></div><span aria-hidden="true">↗</span></a>)}</>; }
function Breadcrumb({ items }) { return <nav className="breadcrumb" aria-label="麵包屑">{items.map(([name,url],i)=><React.Fragment key={name}>{i>0 && <span aria-hidden="true">／</span>}{url ? <a href={url}>{name}</a> : <span aria-current="page">{name}</span>}</React.Fragment>)}</nav>; }
function AppCard({ app, index }) { return <article className={`app-card photo-card theme-${app.slug}`}><a className="card-image-link" href={pathFor(app)} aria-label={`認識${app.name}`}><Photo src={app.image} alt={app.imageAlt} sizes="(max-width: 800px) 100vw, 33vw"/><span className="photo-card-number">0{index+1}</span></a><div className="app-content"><span className="tag">{app.category}</span><h3><a href={pathFor(app)}>{app.name}</a></h3><p>{app.tagline}</p><div className="app-bottom"><small>{app.platform || '獨立開發 App'}</small><a className="text-link" href={pathFor(app)} aria-label={`了解${app.name}`}>認識一下 ↗</a></div></div></article>; }
function AppCollection() {
  const [category,setCategory] = useState('全部 App');
  const categories=['全部 App',...new Set(catalog.map(a=>a.category))];
  const visible=catalog.filter(a=>category==='全部 App'||a.category===category);
  return <section id="apps" className="hub-apps"><div className="section-top"><div><Eyebrow>THE COLLECTION / APP 選集</Eyebrow><h2>小事，也值得用心。</h2></div><p>從每天會遇到的事開始，<br/>做一些自己也想用的工具。</p></div><div className="filters" role="group" aria-label="App 主題篩選">{categories.map(c=><button type="button" key={c} aria-controls="app-list" className="filter" aria-pressed={category===c} onClick={()=>setCategory(c)}>{c}</button>)}</div><div className="app-grid" id="app-list">{visible.map(a=><AppCard key={a.slug} app={a} index={catalog.indexOf(a)}/>)}</div><p className="filter-status" role="status" aria-live="polite">{category==='全部 App' ? ` ${catalog.length} 款作品，從日常慢慢長出來。` : `顯示 ${visible.length} 款${category} App`}</p><aside className="collection-note"><span>＋</span><div><h3>下一個日常靈感，慢慢做。</h3><p>有新的作品，就在這裡和你分享。</p></div><small>MORE TO COME</small></aside></section>;
}
function Home() { return <main className="wrap" id="main-content"><section className="editorial-hero"><div className="editorial-copy"><Eyebrow><span className="dot"/> SMALL TOOLS, GOOD DAYS.</Eyebrow><h1>讓日常，<br/>多一點<span>剛剛好。</span></h1><p>吉他調音器、汽機車保養、所得稅2027。<br/>從練琴、用車到年度事務，找到適合你的日常 App。</p><div className="actions"><a className="btn" href="#apps">看看我們的 App ↓</a><a className="editorial-note" href="/notes/">讀一點生活筆記 ↗</a></div><div className="hero-signature"><span/>獨立開發，從自己的日常出發。</div></div><a href="/apps/guitar-tuner/" className="editorial-image"><Photo src="/images/guitar.jpg" alt="暖色光線下的木吉他與彈奏雙手" priority/><div className="editorial-image-caption"><small>IN TUNE WITH YOUR DAY</small><h2>留一點時間，<br/>給喜歡的聲音。</h2><span>吉他調音器　↗</span></div></a></section><nav className="collection-index" aria-label="三款 App 快速導覽">{catalog.map((a,i)=><a key={a.slug} href={pathFor(a)}><small>0{i+1}</small>{a.name}<span>↗</span></a>)}</nav><section className="purpose-section"><div className="section-top"><div><Eyebrow>MADE AROUND YOUR LIFE</Eyebrow><h2>從你在意的小事開始。</h2></div><p>三個主題，三種生活節奏。</p></div><div className="purpose-grid">{topics.map(([number,title,text,cta,slug])=><a href={`/apps/${slug}/`} key={slug}><span>{number}</span><h3>{title}</h3><p>{text}</p><b>{cta} ↗</b></a>)}</div></section><AppCollection/><section className="knowledge"><div><Eyebrow>A FEW GOOD NOTES</Eyebrow><h2>工具之外，<br/>也聊聊日常。</h2><p>從六條琴弦，到每次出發。<br/>把值得記住的小事，寫下來。</p><a className="text-link" href="/notes/">讀全部筆記 ↗</a></div><div><ArticleLinks/></div></section><section className="about-studio"><Eyebrow>SMALL, WITH INTENTION</Eyebrow><h2>工具可以很小，<br/>對生活的在意不用。</h2><div><p>日常 App 從一個簡單的想法開始：把生活裡反覆遇到的小事，做成自己也想用的工具。練琴前先調音，出發前多關心愛車，忙碌前為年度事務留一點時間。</p><p>這裡整理每款作品的介紹，也分享相關的入門筆記。你可以慢慢看，從剛好需要的那一個開始。</p></div></section><section className="faq-layout"><div><Eyebrow>GOOD TO KNOW</Eyebrow><h2>你可能想問的。</h2><p>關於這裡的 App 與後續更新。</p></div><div>{faq.map(([q,a])=><details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div></section><aside className="cta"><div><h2>找到一個，剛好用得上的。</h2><p>吉他調音器、汽機車保養、所得稅2027。</p></div><a className="btn light" href="#apps">探索 App ↑</a></aside></main>; }
const stories = {
  'guitar-tuner': [
    ['拿起吉他，先不急著彈。','聽聽每條弦，慢慢轉一下旋鈕。把音調好，再回到那首一直想練會的歌。吉他調音器的起點，就是讓練琴前這件小事，有一個簡單的工具可以陪你完成。'],
    ['六條弦，是每次練習的起點。','一般六弦吉他的標準調音，從最粗的第六弦到最細的第一弦，依序是 E、A、D、G、B、E。第一弦與第六弦雖然音名相同，卻在不同八度。先認識目標音名，再開始調音，練習更有方向。'],
    ['把準備，也變成練習的一部分。','從一條空弦開始，在安靜的環境中逐條確認。搬動吉他、換弦或練習一段時間後，都可以再檢查一次。調好音，不必急著彈得完美；先讓每次開始，都多一點從容。'],
  ],
  'vehicle-maintenance': [
    ['四輪與兩輪，都是生活的一部分。','平日代步，假日兜風。愛車陪你走了不少路，也值得被好好照顧。「汽機車保養」關注用車日常，讓每一次出發之前，都多一份對車況的在意。'],
    ['先了解車，再安排照顧它的節奏。','保養沒有適用所有車款的單一答案。先閱讀車主手冊，確認時間、里程與檢查項目；平常多留意儀表警示、胎壓與燈具。本站的保養筆記，從這些容易開始的小事整理起。'],
    ['把每次保養，留成下次的參考。','保養日期、當時里程、施作項目、零件規格與費用，都是值得保存的資訊。保留工單與收據，讓下一次與技師討論時，更容易回顧車輛的維護歷程。'],
  ],
  'income-tax-2027': [
    ['年度的事，早一點放進計畫裡。','有些事，提早留一點時間，心裡就多一點空間。「所得稅2027」從關心自己的年度事務開始，讓準備成為生活節奏的一部分。這裡整理這款 App 的產品介紹，後續資訊將在本頁更新。'],
    ['先確認年度，再使用工具。','「所得稅2027」是 App 名稱。使用前，請查看產品說明中的適用地區與年度，並留意所得年度和申報年度的區別。實際申報資訊，仍以主管機關公告為準。'],
    ['讓資料與官方資訊，一起準備好。','年度事務牽涉不同來源的文件與說明，可以先整理自己的資料，並確認主管機關發布的最新資訊。本頁目前沒有提供稅額試算、申報指引或稅率資料；具體產品功能將以正式介紹為準。'],
  ],
};
function Product({ app }) {
  if (app.listed===false) return <main className="detail" id="main-content"><Breadcrumb items={[[ '首頁','/'],[app.name]]}/><span className="badge">獨立產品概念</span><h1>{app.name}</h1><p>{app.description}</p><h2>概念功能規劃</h2><ul>{app.features.map(f=><li key={f}>{f}</li>)}</ul><div className="disclaimer">這是早期產品概念，規劃內容不代表本站其他 App 的實際功能。</div><a className="btn" href="/#apps">探索本站 App ↗</a></main>;
  const guitar=app.slug==='guitar-tuner', tax=app.slug==='income-tax-2027', vehicle=app.slug==='vehicle-maintenance';
  const related=articles.filter(a=>guitar ? a[0]==='guitar-standard-tuning' : vehicle && a[0]!=='guitar-standard-tuning');
  const status = app.platform ? `${app.platform} App` : '獨立開發 App';
  const productStories = stories[app.slug] || [['從自己的日常需要開始。', app.description]];
  return <main className={`product-page theme-${app.slug}`} id="main-content"><div className="wrap"><Breadcrumb items={[[ '首頁','/'],['App 選集','/#apps'],[app.name]]}/><section className="product-hero"><div><Eyebrow>{app.category} / IN YOUR EVERYDAY</Eyebrow><h1>{app.name}</h1><p className="product-tagline">{app.tagline}</p><p className="product-intro">{app.description}</p><div className="product-status"><span className="dot"/>{status}</div><div className="actions">{[['iosUrl','前往 App Store'],['androidUrl','前往 Google Play']].filter(([key])=>app[key]).map(([key,label])=><a className="btn" key={key} href={app[key]} target="_blank" rel="noopener noreferrer">{label} ↗</a>)}<a className="text-link" href="#app-story">多認識一點 ↓</a></div></div><Photo src={app.image} alt={app.imageAlt} priority/></section></div><div className="detail product-story" id="app-story"><aside className="product-facts"><div><small>產品主題</small><strong>{app.category}</strong></div><div><small>產品資訊</small><strong>{status}</strong></div><div><small>適合先了解</small><strong>{guitar ? '標準調音與練習前準備' : tax ? '產品資訊與適用年度說明' : vehicle ? '保養週期、紀錄與用車支出' : '產品用途與使用方式'}</strong></div></aside>{productStories.map(([h,p],i)=><section className="story-section" key={h}><span className="story-number">0{i+1}</span><h2>{h}</h2><p>{p}</p></section>)}{app.slug==='vehicle-maintenance' && <section className="screenshot-section"><Eyebrow>INSIDE THE APP</Eyebrow><h2>打開 App，看見用車日常。</h2><div className="screenshot-grid" tabIndex="0" role="region" aria-label="汽機車保養 App 範例畫面，可左右捲動">{[['garage','車庫'],['records','保養紀錄'],['reminders','保養計畫']].map(([file,label])=><figure key={file}><Photo src={`/images/vehiclecare-${file}.png`} alt={`汽機車保養 App ${label}畫面，含範例資料與測試廣告`} sizes="(max-width: 520px) 65vw, 230px"/><figcaption>{label}</figcaption></figure>)}</div><p className="screenshot-caption">實際 App 模擬器畫面，使用範例資料；上方為測試廣告。</p></section>}{app.features.length>0&&<><h2>App 功能</h2><ul>{app.features.map(f=><li key={f}>{f}</li>)}</ul></>}<section className={`release-panel ${tax?'tax-panel':guitar?'guitar-panel':''}`}><span className="tag">GOOD TO KNOW</span><h2>下載前，先了解這些事。</h2><p>商店連結會在確認後提供。支援裝置、版本、價格與實際功能，請以正式商店頁面的最新說明為準。</p><p>封面照片呈現生活情境；另有標示的 App 畫面使用範例資料。你可以先閱讀產品介紹與相關筆記，再選擇適合自己的工具。</p></section>{related.length>0&&<aside className="related-notes"><h2>{guitar?'從調音開始，讀一點小知識。':'從保養知識開始，照顧日常座駕。'}</h2><ArticleLinks items={related}/></aside>}<aside className="more-apps"><Eyebrow>ALSO MADE FOR YOUR DAY</Eyebrow><h2>也看看其他作品。</h2><div>{catalog.filter(a=>a.slug!==app.slug).map(a=><a key={a.slug} className="text-link" href={pathFor(a)}>{a.name} ↗</a>)}</div></aside></div></main>;
}
function Notes() { return <main className="wrap journal" id="main-content"><Breadcrumb items={[[ '首頁','/'],['生活筆記']]}/><header className="journal-heading"><Eyebrow>THE EVERYDAY JOURNAL</Eyebrow><h1>工具之外，<br/>留一點生活的筆記。</h1><p>調好六條弦，照顧每一段路。<br/>從容易開始的小知識，慢慢建立自己的日常習慣。</p></header><div className="journal-grid">{articles.map(([slug,category,title,description],i)=><article key={slug} className="journal-card"><a href={`/notes/${slug}/`}><div className="journal-image"><Photo src={slug==='guitar-standard-tuning'?'/images/guitar.jpg':'/drive.jpg'} alt={slug==='guitar-standard-tuning'?'木吉他彈奏情境':'綠意道路旁的汽車'} sizes="(max-width: 800px) 100vw, 50vw"/><span>0{i+1}</span></div><small>{category} / 生活筆記</small><h2>{title}</h2><p>{description}</p><b>閱讀筆記 ↗</b></a></article>)}</div></main>; }
function Article({ article }) { const [slug,category,title,description,paragraphs]=article; const guitar=slug==='guitar-standard-tuning';return <main className="detail article-page" id="main-content"><Breadcrumb items={[[ '首頁','/'],['生活筆記','/notes/'],[category]]}/><Eyebrow>{category} / EVERYDAY NOTES</Eyebrow><h1>{title}</h1><p className="article-lead">{description}</p><div className="article-byline">日常 App 編輯 · 入門筆記</div><nav className="article-toc" aria-label="文章目錄"><strong>這篇筆記會聊到</strong>{paragraphs.map(([h],i)=><a key={h} href={`#section-${i}`}>{String(i+1).padStart(2,'0')}　{h}</a>)}</nav>{paragraphs.map(([h,p],i)=><section className="story-section" key={h}><h2 id={`section-${i}`}>{h}</h2><p>{p}</p></section>)}<div className="disclaimer">{guitar?'本文介紹一般六弦吉他的標準調音。不同樂曲與樂器可能使用其他定弦方式。':'本文提供一般保養資訊，實際檢查項目與週期請依車主手冊、原廠規範及合格技師建議安排。'}</div><p><a className="btn" href={`/apps/${guitar?'guitar-tuner':'vehicle-maintenance'}/`}>認識{guitar?'吉他調音器':'汽機車保養'} App ↗</a></p><aside className="related-notes"><h2>繼續讀一點</h2><ArticleLinks items={articles.filter(a=>a[0]!==slug)}/></aside></main>; }
function Privacy() { return <main className="detail" id="main-content"><Breadcrumb items={[[ '首頁','/'],['隱私說明']]}/><Eyebrow>YOUR PRIVACY</Eyebrow><h1>隱私說明</h1><p>本頁適用於「日常 App」產品介紹網站。</p><h2>網站的資料使用</h2><p>本網站沒有註冊、聯絡表單、付款功能或分析與廣告追蹤程式。App 主題篩選與手機選單只在目前頁面中運作，不會儲存車輛、保養、所得或稅務資料。網站代管服務可能為安全與正常運作處理連線資訊，相關處理依代管平台政策辦理。</p><h2>字型與外部連結</h2><p>本網站透過 Google Fonts 載入字型，瀏覽器可能因此傳送 IP 位址及一般連線資訊。若點選外部產品或商店連結，請參閱該平台的隱私政策。</p><h2>各款 App 的隱私政策</h2><p>吉他調音器、汽機車保養與所得稅2027 的資料使用方式，應以各 App 的專屬隱私政策為準。本頁只說明產品介紹網站的資料處理。</p></main>; }
export default function App({ path='/' }) {
  let content;
  if(path==='/') content=<Home/>;
  else if(path==='/notes/') content=<Notes/>;
  else if(path==='/privacy/') content=<Privacy/>;
  else if(path.startsWith('/apps/') && apps.some(a=>pathFor(a)===path)) content=<Product app={apps.find(a=>pathFor(a)===path)}/>;
  else if(articles.some(a=>`/notes/${a[0]}/`===path)) content=<Article article={articles.find(a=>`/notes/${a[0]}/`===path)}/>;
  else content=<main className="detail" id="main-content"><Eyebrow>404 / A LITTLE LOST</Eyebrow><h1>找不到這個頁面。</h1><p>回到 App 選集，繼續找一個剛好用得上的工具。</p><a className="btn" href="/">返回首頁 ↗</a></main>;
  return <><a className="skip-link" href="#main-content">跳至主要內容</a><Header/>{content}<Footer/></>;
}
