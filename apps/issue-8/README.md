# Issue #8: 我要尿尿 (Highway Rest Area Finder)

## 簡介

「我要尿尿」是一個專為高速公路駕駛設計的 Web 應用程式，幫助使用者快速找到最近的休息站或服務區，並即時顯示停車位狀態。

## 功能特色

- 📍 **定位功能**：使用 GPS 定位找到使用者當前位置
- 🛣️ **智慧搜尋**：依照行進方向（北上/南下）找到最近的服務區
- 🚗 **停車狀態**：即時顯示停車位剩餘情況（充足/稍滿/已滿）
- ⏱️ **預估時間**：根據距離和速度計算到達時間
- 🗺️ **導航整合**：一鍵開啟 Google Maps 導航
- 📱 **響應式設計**：完美支援手機、平板和桌面裝置

## 專案結構

```
apps/issue-8/
├── frontend/          # Angular 21 前端應用
│   ├── src/
│   │   └── app/
│   │       ├── app.ts              # 主元件
│   │       ├── app.html            # 主模板
│   │       ├── app.css             # 主樣式
│   │       └── location.service.ts # 定位服務
│   └── package.json
├── backend/           # Go 後端 API
│   ├── main.go       # API 伺服器
│   └── go.mod
└── README.md
```

## 安裝與執行

### 前端 (Angular)

```bash
# 進入前端目錄
cd apps/issue-8/frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm start

# 開啟瀏覽器訪問 http://localhost:4200
```

### 後端 (Go)

```bash
# 進入後端目錄
cd apps/issue-8/backend

# 安裝依賴
go mod tidy

# 啟動 API 伺服器
go run main.go

# 伺服器將在 http://localhost:8080 啟動
```

## API 端點

### GET /api/health
健康檢查端點

**回應範例：**
```json
{
  "status": "healthy",
  "time": "2026-02-17T14:30:00Z"
}
```

### POST /api/nearest-service-area
查詢最近的服務區

**請求格式：**
```json
{
  "latitude": 24.8251,
  "longitude": 121.0098,
  "heading": 0,
  "speed": 105
}
```

**成功回應範例：**
```json
{
  "id": "1",
  "name": "湖口服務區",
  "direction": "北上",
  "highway": "國道1號",
  "latitude": 24.9051,
  "longitude": 121.0398,
  "mileage": 97.0,
  "distance": 6.5,
  "eta": "4 分鐘",
  "parkingInfo": {
    "status": "充足",
    "availableSpaces": 128,
    "totalSpaces": 200,
    "colorCode": "#28a745"
  }
}
```

**錯誤回應範例：**
```json
{
  "error": "out_of_bounds",
  "message": "偵測到您目前不在高速公路上，本功能僅限國道急尿使用。"
}
```

## 停車狀態定義

- 🟢 **充足** (`#28a745`): 剩餘車位 > 50%
- 🟡 **稍滿** (`#ffc107`): 剩餘車位 20% - 50%
- 🔴 **已滿** (`#dc3545`): 剩餘車位 < 20% 或剩餘車位 < 10

## 測試

### 前端測試
```bash
cd apps/issue-8/frontend
npm test
```

### 後端測試
```bash
cd apps/issue-8/backend
go test ./...
```

### 手動測試範例

使用提供的測試座標進行測試：

**測試座標：** 24.8251, 121.0098 (國道1號北上 90.5K)

**預期結果：**
- 服務區名稱：湖口服務區 (北上)
- 距離：約 6.1 公里
- 預估時間：約 4 分鐘 (以時速 105km/h 計算)
- 停車狀態：顯示即時停車位資訊

## 驗收標準

### ✅ 範例一：成功獲取最近休息站資訊

**Given**: 使用者正行駛於國道一號北上 80km 處，且已授權網頁使用 GPS 高精確度定位。

**When**: 使用者點擊「我要尿尿」按鈕。

**Then**: 系統應顯示下一個服務區為「湖口服務區」，並準確顯示距離為 6.5 公里。

### ✅ 範例二：顯示停車場即時狀態

**Given**: 系統已成功辨識使用者前方的下一個休息站。

**When**: 系統獲取後端即時交通 API 資料後。

**Then**: 網頁應以顏色標示（綠色、黃色、紅色）顯示停車場狀態。

### ✅ 範例三：例外處理

**Given**: 使用者目前的 GPS 座標點不在高速公路範圍內。

**When**: 使用者點擊「我要尿尿」按鈕。

**Then**: 系統應顯示警示訊息：「目前偵測不到您在高速公路上」。

## 技術堆疊

### 前端
- **Framework**: Angular 21
- **語言**: TypeScript
- **樣式**: CSS
- **HTTP Client**: Angular HttpClient
- **定位 API**: Geolocation API

### 後端
- **語言**: Go 1.24+
- **框架**: net/http (標準庫)
- **CORS**: github.com/rs/cors

## 部署

### 前端部署 (GitHub Pages)

前端應用將部署到 GitHub Pages，可透過以下步驟建置：

```bash
cd apps/issue-8/frontend
npm run build
```

建置產物將產生在 `dist/` 目錄中。

### 後端部署 (Build Artifacts)

後端應用建置為可執行檔：

```bash
cd apps/issue-8/backend
go build -o rest-area-api main.go
```

## 未來改進 (V2+)

以下功能已規劃但不包含在 V1 版本：

- [ ] PWA 支援（可安裝到手機桌面）
- [ ] i18n 多國語系支援
- [ ] 整合真實 TDX API 資料
- [ ] 離線模式支援
- [ ] 非高速公路替代搜尋（加油站、公廁）
- [ ] 使用者帳號與偏好設定

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/8
- CI/CD Workflow: `.github/workflows/ci_8.yml`
- 資料來源：[交通部 TDX 平台](https://tdx.transportdata.tw/)

## 授權

MIT License

## 注意事項

⚠️ **安全駕駛提醒**：請勿邊開車邊使用手機。建議由副駕駛或乘客操作，或在安全停車後使用。
