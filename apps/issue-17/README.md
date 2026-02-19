# Issue #17: Kubernetes 升級驗證器（K8s Upgrade Validator）

## 簡介

`k8s-upgrade-validator` 是一個 CLI 工具，用於在 Kubernetes 升級前掃描叢集資源，辨識已棄用或已移除 API，並產出升級相容性報告。

目前為 MVP（初始可運作版本），已完成：

- 版本參數驗證（支援範圍：`1.25` 到 `1.34`）
- 依規則比對 API deprecated/removed 風險
- 報告輸出格式：`text`、`json`、`html`
- 升級步驟建議與 exit code
- 測試覆蓋核心流程

## 安裝

```bash
cd apps/issue-17
npm install
```

## 使用方式

### 基本掃描

```bash
npm run dev -- --current-version 1.28 --target-version 1.31
```

### 指定 kubeconfig 與 namespace

```bash
npm run dev -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --kubeconfig ~/.kube/config \
  --namespace production
```

### JSON / HTML 輸出

```bash
# JSON
npm run dev -- --current-version 1.28 --target-version 1.31 --output json

# HTML
npm run dev -- --current-version 1.28 --target-version 1.31 --output html
```

### 將報告寫入檔案

```bash
npm run dev -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --output json \
  --report-file ./report.json
```

### 使用本地測試資料（不連線叢集）

```bash
npm run dev -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --input-file ./fixtures/resources.json
```

## 輸出與退出碼

- `0`: 無 critical findings（可升級或僅 warning）
- `1`: 發現 critical findings（目標版本會移除 API）
- `2`: 參數錯誤或執行錯誤

JSON 報告格式可參考：`docs/report.schema.json`

## 已實作的規則（MVP）

- `Ingress` `extensions/v1beta1` → `networking.k8s.io/v1`
- `PodDisruptionBudget` `policy/v1beta1` → `policy/v1`
- `CronJob` `batch/v1beta1` → `batch/v1`
- `PodSecurityPolicy` `policy/v1beta1`（已移除，無直接替代）
- `Event` `events.k8s.io/v1beta1` → `events.k8s.io/v1`
- `FlowSchema` `flowcontrol.apiserver.k8s.io/v1beta2` → `flowcontrol.apiserver.k8s.io/v1`
- `PriorityLevelConfiguration` `flowcontrol.apiserver.k8s.io/v1beta2` → `flowcontrol.apiserver.k8s.io/v1`

## 測試

```bash
cd apps/issue-17
npm test
```

## 建置

```bash
cd apps/issue-17
npm run build
```

## 部署

此專案屬於 CLI 工具，CI 會在 `main` 分支 push 且測試通過後，將 `dist/` 上傳為 GitHub Actions Artifacts。

## 已知限制（MVP）

- 尚未實作自動建立沙盒叢集（`--sandbox` 目前僅保留旗標）
- 尚未支援 CRD 與 Helm Chart 深度相容性分析
- 規則庫目前為內建靜態清單，後續可外部化更新

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/17
- CI/CD Workflow: `.github/workflows/ci_17.yml`
