# GitHub Issue Analysis Report

Date: 2026-02-19
Status: Completed Analysis

## Overview
I have analyzed the current open issues in the repository `doggy8088/Apptopia`.
Due to the missing `GITHUB_TOKEN` in the execution environment, automated posting of comments was not possible.
Below are the generated comments and actions determined for each issue.

## Summary of Actions

| Issue # | Title | Status | Action |
| :--- | :--- | :--- | :--- |
| **#19** | [工具] 開源個人記帳理財工具（Open Moneybook） | **Clear** (Plan exists) | **Needs Checklist**: Converted V1 Plan to Markdown Checklist. |
| **#18** | [工具] Obsidian 筆記書籍編譯器 | **Clear** (Plan exists) | **Skipped**: Comprehensive checklist already exists. |
| **#11** | [工具] 美食地圖 | **Blocked** (Waiting for info) | **Needs Checklist**: Converted clarifying questions to Checklist for OP. |
| **#3** | [工具] 本機運作的私人知識庫 | **Clear** (Plan exists) | **Skipped**: Comprehensive checklist already exists. |

## Generated Comments

### Issue #19: [工具] 開源個人記帳理財工具（Open Moneybook）
**Proposed Comment:**
> 為了方便追蹤進度，我將上述的 V1 開發計畫整理為 Checklist：
>
> 依目前討論（含 5 點確認），需求已足夠規劃，先不開始開發。以下是 V1 開發計畫 checklist。
>
> ## V1 決策已凍結
> - [ ] 預算功能升級為 Must
> - [ ] 資料規則：`type=收入/支出`、`amount` 一律正數
> - [ ] 部署定位：純前端、無後端、IndexedDB + LocalStorage、GitHub Pages
> - [ ] V1 先單帳戶記錄，不做帳戶間轉帳
> - [ ] CSV 匯入先支援單一標準格式（欄位對映/銀行格式留到 V2）
> - [ ] 外部參考專案僅作功能對照，不納入本案架構（本案維持零登入、零雲端）
>
> ## 里程碑
> ### Phase 0（0.5~1 天）：規格凍結與資料樣本
> - [ ] 鎖定交易資料 schema、預算規則、CSV import/export 欄位
> - [ ] 準備 fixture（至少 100 筆）
>
> ### Phase 1（1 天）：專案與 CI
> - [ ] 建立 `apps/issue-19/` 前端專案
> - [ ] 建立 `.github/workflows/ci_19.yml`
>
> ### Phase 2（1.5~2 天）：核心資料層
> - [ ] IndexedDB repository（transactions / categories / budgets / settings）
> - [ ] CRUD + 資料驗證 + migration versioning
>
> ### Phase 3（2 天）：記帳與預算功能
> - [ ] 收支表單、列表、編輯刪除
> - [ ] 預算設定、進度計算、超支提示
>
> ### Phase 4（1.5~2 天）：報表與匯入匯出
> - [ ] 月摘要（收入 / 支出 / 結餘）
> - [ ] 圓餅圖 + 趨勢圖
> - [ ] CSV 匯出 + 單一標準格式 CSV 匯入
>
> ### Phase 5（1~1.5 天）：PWA、部署與驗收
> - [ ] 基本離線能力（service worker）
> - [ ] GitHub Pages build/deploy pipeline
> - [ ] 驗收測試與 README
>
> ## 驗收對照
> - [ ] 新增 $150 餐飲支出後可持久化並顯示
> - [ ] 30 天資料可正確計算月摘要與分類圖
> - [ ] 預算 $5000 超支時顯示提醒
> - [ ] 100 筆匯出 CSV 可被 Excel 開啟
> - [ ] 關閉重開瀏覽器資料仍在
> - [ ] 匯入標準 CSV 後資料完整映射

### Issue #11: [工具] 美食地圖
**Proposed Comment:**
> 為了方便樓主回覆，我將上述的待確認事項整理為 Checklist：
>
> 感謝提案，先不開始開發。要制定可執行計畫前，請樓主先補充以下關鍵資訊：
>
> 1. 資料來源與授權
> - [ ] 要使用 Google Places/Maps API，還是其他資料來源？
> - [ ] 若使用 Google API，是否可提供 API Key 與配額/預算上限？
> - [ ] 是否接受『僅用官方 API 查詢與顯示』，不做可能違反條款的爬蟲資料擷取？
>
> 2. 搜尋範圍與查詢條件
> - [ ] V1 要先支援單一城市，還是全球地區？
> - [ ] 使用者是否可輸入地點、半徑、關鍵字（例如「拉麵」）？
>
> 3. 地圖與清單的互動細節
> - [ ] 點選餐廳後要顯示哪些欄位（名稱、評分、評論數、地址、營業狀態、Google Map 連結）？
> - [ ] 需要哪些排序方式（評分、評論數、距離）？
> - [ ] 結果要分頁，還是一次載入全部？
>
> 4. 驗收樣本
> - [ ] 請提供 2~3 組測試查詢（地點 + 關鍵字）與預期結果範例。
> - [ ] 請確認評分條件是否固定為：rating >= 3.8 且 <= 4.8，且評論數 >= 1000。
