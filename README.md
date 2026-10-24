# 日常 App 產品介紹網站

同一個入口介紹「汽機車保養」與「所得稅2027」。使用靜態 HTML，不需要付費 API、資料庫或前端框架。

## 更新內容

- `apps.json` 集中管理名稱、類別、介紹、平台、SEO 標題、功能與商店網址。尚未確認的功能與連結留空，不會顯示假下載按鈕。
- `listed: true` 的 App 顯示於首頁與篩選；`listed: false` 仍保留獨立頁面供既有連結使用。
- `notes.json` 管理現有保養文章。
- 修改後執行 `python build.py`，產生頁面、JSON-LD、robots.txt、sitemap.xml 與 404 頁面。
- 實際介面尚未提供，因此網站不展示兩款 App 的虛構截圖。所得稅2027 目前僅依產品名稱介紹，沒有推定稅率、適用年度、試算或報稅功能。

## 部署網址

預設產生目前公開 Sites 網址。遷移到其他主機時，使用 `SITE_ORIGIN` 指定已確認的 HTTPS 網址，可用 `SITE_OUTPUT_DIR` 指定輸出路徑：

```sh
SITE_ORIGIN=https://your-project.pages.dev python build.py
```

部署目錄為 `dist/`。Cloudflare Direct Upload 的 ZIP 必須直接包含 `index.html` 等內容，不能多包一層 `dist/`。

## 搜尋與社群資訊

首頁涵蓋兩款 App，各產品有獨立 title、description、canonical、Open Graph、Twitter metadata、SoftwareApplication 與 BreadcrumbList。首頁另有 App ItemList。保留原 Google 驗證標記；更換網域後仍需在 Search Console 新增並驗證新資源，提交新 sitemap。SEO 設定不保證排名或收錄。

Google Fonts 用於字型載入；本網站沒有分析追蹤、表單或登入。

## 專案結構

```text
apps.json                    App 資料與 SEO 文案
notes.json                   保養文章
build.py                     靜態頁面與 SEO 檔案產生程式
scripts/package-cloudflare.py  Cloudflare Direct Upload 打包程式
dist/                        完整網站輸出與圖片、CSS、JavaScript
ASSETS.md                    圖片及字型來源
```

## 本機執行

需要 Python 3，沒有額外套件需要安裝。

```sh
python build.py
python -m http.server 8000 --directory dist
```

開啟 `http://localhost:8000/`。

## Cloudflare Pages：連接 GitHub

1. 在 Cloudflare 的 Workers & Pages 建立 Pages 專案，選擇連接此 GitHub 儲存庫，允許 Cloudflare 讀取。
2. Production branch：`main`；Framework preset：`None`；Build command：`python build.py`；Build output directory：`dist`；Root directory：留空。
3. 在 Cloudflare 設定 `SITE_ORIGIN` 為實際的正式網址，例如 `https://實際專案名稱.pages.dev`。
4. 部署完成後，如果 Cloudflare 指派的正式網址與預期不同，修正 `SITE_ORIGIN` 並重新部署，以更新 canonical 與 sitemap。
5. 在 Google Search Console 新增並驗證正式網址、提交 `/sitemap.xml`。本儲存庫內原有的 Google 驗證標記不代表新網址已完成驗證。

連接 GitHub 需要在你的 Cloudflare 帳號中操作。本儲存庫未包含 Cloudflare API 金鑰或部署憑證。

## Cloudflare Pages：直接上傳 ZIP

已建立 Pages 專案、取得正式網址後，可產生對應的 ZIP：

```sh
python scripts/package-cloudflare.py --origin https://實際專案名稱.pages.dev
```

上傳 `.artifacts/cloudflare-pages.zip` 至 Pages Direct Upload 即可。打包時會重新產生對應網址的 SEO 資料，並將 `index.html` 直接放在 ZIP 根目錄。Direct Upload 專案無法切換成 Git 整合專案。
