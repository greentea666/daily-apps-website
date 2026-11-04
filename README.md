# 日常 App｜JavaScript + React

繁體中文 App 介紹網站，包含吉他調音器、汽機車保養、所得稅2027 與生活筆記。以奶油白、森林綠、陶土橘為主色，搭配情境攝影、襯線標題、響應式卡片與手機導覽。

## 執行

需要 Node.js 22.12+。

```sh
npm ci
npm run build
npm run dev
```

`npm run dev` 開啟本機 Vite 伺服器；`npm run preview` 預覽已產生的 `dist/`。`python3 build.py` 僅保留舊部署設定相容入口，內部呼叫 JavaScript 建置程式。

## 架構

- `src/App.jsx`：React 元件、首頁、分類篩選、手機導覽、產品介紹、文章與隱私說明。
- `src/client.jsx`：React hydration，為已渲染的內容加上互動。
- `scripts/build.mjs`：JavaScript 靜態預先渲染，產生每個網址的完整 HTML、SEO metadata、JSON-LD、robots 與 sitemap；esbuild 打包含雜湊的瀏覽器 JavaScript。
- `public/`：CSS、照片、favicon。請修改這裡的素材，`dist/` 是建置輸出；建置只清理由產生檔案清單記錄的舊檔，不刪除其他檔案。
- `apps.json`：產品資訊。`listed: false` 保留概念頁，但標記 noindex 並排除 sitemap。
- `notes.json`：文章內容。
- `scripts/check-seo.py`：檢查唯一標題與描述、canonical、JSON-LD、索引指令、圖片、內部連結及 sitemap 一致性。

所有主要內容在伺服器回傳的 HTML 中已可閱讀，Google 不需要先執行 JavaScript 才能取得文案。頁面使用單一 H1、繁體中文語言標記、麵包屑、站內連結、社群分享 metadata。沒有編造評分、價格或商店連結；汽機車保養的四項功能與三張模擬器截圖，已依使用者的 VehicleCare 專案核對。吉他與所得稅 App 尚未提供詳細規格，不推定支援平台、精度、稅率或適用年度。

## 正式網址與驗證

預設為目前既有網站：`https://autocare-app-studio.t410002246.chatgpt.site`。更換網域時必須重新建置：

```sh
SITE_ORIGIN=https://your-real-domain.example npm run build
```

`SITE_ORIGIN` 必須是完整 HTTPS origin，不可包含路徑、帳密、空白、query 或 fragment。Cloudflare Pages 建置必須明確設定這個變數，避免將部署預覽網址誤當正式 canonical。可設定 `SITE_OUTPUT_DIR` 改變輸出位置；只能使用預設 `dist` 或專案外的輸出目錄，會拒絕覆蓋原始碼或透過符號連結跳轉。`GOOGLE_SITE_VERIFICATION` 可覆寫保留的 Google 驗證標記；原有標記不代表目前帳號已完成驗證。

## Google 收錄流程

1. 發布網站，確保訪客和 Googlebot 不需登入就能取得 HTTP 200 的完整內容。
2. 在 [Google Search Console](https://search.google.com/search-console) 加入正式 HTTPS 網址的「網址前置字元」資源。
3. 使用 HTML 標記驗證；必要時將 Search Console 提供的 content 值設定為 `GOOGLE_SITE_VERIFICATION`，重新建置並部署後驗證。
4. 在「Sitemap」提交 `sitemap.xml`。
5. 以「網址審查」檢查首頁與三個產品頁，測試線上網址並要求建立索引。
6. 後續查看「頁面索引」與「成效」報表。搜尋結果出現時間與排名由 Google 決定，sitemap 與設定不保證收錄。

不要使用已淘汰的 sitemap ping 或將一般產品頁提交到限定用途的 Indexing API。正式網域穩定後，從自己的 App 商店頁面、開發者介紹或其他真實相關頁面連回網站，幫助使用者與搜尋引擎找到內容。

## 驗證與部署

```sh
npm run build
npm run check
```

部署輸出目錄為 `dist/`，需保留真正的 404 狀態；不要設定將所有不存在網址回傳首頁 HTTP 200 的 SPA fallback。Sites 發布識別與靜態目錄由 `.openai/hosting.json` 定義。

Cloudflare Pages Git 整合使用 build command `npm run build`、output directory `dist`，並設定正確的 `SITE_ORIGIN`。Direct Upload 可以使用：

```sh
python3 scripts/package-cloudflare.py --origin https://your-real-project.pages.dev
```

圖片來源見 `ASSETS.md`。Google Fonts 用於字型載入；本網站不使用分析追蹤、表單或登入。

## 回歸檢查與部署安全

```sh
npm test
npm run check
npm audit
```

`npm test` 執行實際建置／打包整合測試與 React DOM 行為測試。測試包含無 JavaScript 時的手機導覽、hydration、篩選、Esc 關閉選單，以及錯誤輸入不破壞既有輸出。測試不取代實機瀏覽器的排版檢查。

- `SITE_NOINDEX=1` 可用於預覽環境，所有頁面標記 noindex 且 sitemap 不列出預覽頁面。打包正式 Cloudflare ZIP 時會明確關閉此設定。
- `image-metadata.json` 包含圖片真實尺寸與 WebP 版本；新增圖片時同步更新，避免錯誤尺寸或失效的 srcset。
- 新增 App 只需在 apps.json 加入正確欄位；若沒有專用故事文案，會以產品描述作為簡介，不會讓建置失敗。商店網址僅接受 apps.apple.com 與 play.google.com 的 HTTPS 網址。
- 原本的車序概念頁仍可直接開啟，但標記 noindex 並排除 sitemap；404 頁不宣告 canonical 與 WebPage 結構化資料。
- 保留可讀的 FAQ，但不宣稱可取得 Google FAQ 或 App 星級富摘要。實際排名和收錄狀態需以 Search Console 為準。

最近一次程式與 SEO 稽核結果、驗證限制和待補產品資料見 [AUDIT.md](AUDIT.md)。
