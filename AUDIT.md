# 程式與 SEO 稽核結果

## 使用的版本

以 Sites 已發布的 React v6 原始碼為準進行檢查；先前 GitHub 仍是較舊 Python 版本。本次將最新 React 原始碼、資源、測試及部署程式完整同步回 GitHub。

## 已修正

- 建置不再直接遞迴刪除指定輸出目錄；先在獨立暫存區完成建置，再替換完整檔案。只移除上次建置清單記錄的舊檔，保留其他檔案。拒絕原始碼路徑、來源父目錄與符號連結跳轉。
- 驗證 HTTPS 正式網址、App/文章 slug 唯一性、欄位型別、圖片路徑與商店網址；無效設定在修改輸出前就失敗。新增 App 沒有專用故事文案時會使用產品介紹，不再中斷建置。
- Cloudflare 正式建置需明確設定 SITE_ORIGIN；預覽可用 SITE_NOINDEX=1，避免將預覽站誤當正式網址。ZIP 以固定排序、權限和時間資訊重複產生相同內容，失敗時保留舊 ZIP。
- 10 個可索引頁面具有唯一 title/description、canonical、繁體中文語言標記、可讀靜態 HTML、站內連結與對應 sitemap；舊概念頁及 404 不收錄。404 不宣告正式 canonical 或 WebPage 結構化資料。
- 保留 Google 驗證標記，建立文章/產品與 WebPage 的 mainEntity 關聯。分享圖片補上真實尺寸、類型與圖說；sitemap 包含主要圖片網址。
- 保留可見 FAQ，移除不再適用的 FAQPage 宣告。沒有為取得富摘要而捏造售價、下載數或星級評分。
- 主圖、卡片及 App 截圖使用實際尺寸與響應式 WebP；Google Fonts 改為 HTML 直接載入，減少 CSS @import 的額外等待。
- 修正手機選單切回桌面後重複顯示、無 JavaScript 時的手機導覽、Escape 關閉與焦點恢復；改善操作區大小、鍵盤焦點、文字對比與減少動畫設定。
- 依先前明確要求移除「審核中」公開標示。汽機車保養介紹補上已查證的四項功能與三張真實模擬器截圖，清楚標示範例資料和測試廣告。

## 驗證結果

- `npm run build`：成功。
- `npm run check`：10 個可索引頁面通過；涵蓋 metadata、canonical、JSON-LD、站內連結、片段錨點、圖片 srcset、robots 與 sitemap。
- `npm test`：16 項建置／打包整合測試、4 項 React DOM 行為測試全部通過。8 種代表頁面 hydration 保留原內容，未出現 recoverable 或 console 錯誤。
- `npm audit`：0 個已知漏洞（包含開發依賴；僅代表此次掃描的已知套件公告）。
- CSS 解析：0 警告。

## 產品內容的依據

汽機車保養功能依使用者專案 [VehicleCare README](https://github.com/greentea666/VehicleCare/blob/main/README.md) 核對：多車管理、保養紀錄與收據照片、月份/公里數計畫、依車輛與年度檢視費用。通知須授權，里程由使用者更新，不宣稱自動讀取車輛。

吉他調音器與所得稅2027 尚無已確認的商店連結和完整規格；網站未臆造支援平台、偵測精度、免費售價、稅率或適用的申報年度。所得稅頁為產品介紹，不是稅務試算或申報服務。

## 仍需正式環境確認

- Sites API 回報網站為 public、active；錯誤日誌沒有事件。但本檢測環境匿名讀取首頁、robots.txt、sitemap.xml 仍收到 HTTP 403，本文 error code: 1010。這表示這次連線遭阻擋，不能據此判定 Googlebot 或一般訪客也遭阻擋。需要 Search Console「測試實際網址」確認，若 Google 同樣收到 403，需由代管平台處理。
- 目前沒有 Search Console 授權，尚未讀取索引/搜尋成效報表，也未代為提出索引申請。使用搜尋工具沒有取得本站結果，不能取代 URL Inspection 的索引判定。
- 目前沒有可用的瀏覽器控制工具；已做 DOM 互動與 CSS 分析，尚未完成真實瀏覽器的畫面、Core Web Vitals 或實機測試。
- 新 Cloudflare Pages 正式網址與帳號發布狀態尚未確認。網站仍以目前已知的 Sites 網址產生正式 canonical；更換網域後需重新建置並在 Search Console 驗證新資源。
- HTTP 404 狀態由代管平台控制；程式已提供 404.html，正式平台必須避免全站回首頁的 HTTP 200 SPA fallback。

SEO 設定不保證立即收錄或排名；外部存取與真實產品資訊是後續改善的重要前提。

## 官方參考

- [Google Search Essentials](https://developers.google.com/search/docs/essentials)
- [SoftwareApplication 規範](https://developers.google.com/search/docs/appearance/structured-data/software-app)
- [Google Search 文件更新](https://developers.google.com/search/updates)
- [Cloudflare 1010 錯誤說明](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)
