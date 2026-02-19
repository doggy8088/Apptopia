# Issue #17: Kubernetes 升級驗證器（K8s Upgrade Validator）

## 簡介

`k8s-upgrade-validator` 是一個 CLI 工具，用於在 Kubernetes 升級前比對資源的 API 相容性，找出 deprecated/removed API，並輸出結構化報告。

目前此版本為「第一階段 MVP」，重點放在：

- 版本區間驗證（支援 `v1.25 ~ v1.34`）
- 以 YAML/JSON manifest 掃描資源
- 比對 API 規則並產生風險報告（text/json/html）
- 提供升級步驟建議與 CI 可用的 exit code

## 安裝

```bash
cd apps/issue-17
npm install
```

## 使用方式

### 基本用法（從 manifests 掃描）

```bash
npm start -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --from-manifests ./tests/fixtures/breaking/pdb.yaml
```

### 掃描多個 manifest 路徑

```bash
npm start -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --from-manifests ./k8s/base,./k8s/overlays/prod
```

### 指定 namespace 過濾

```bash
npm start -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --from-manifests ./k8s \
  --namespace production \
  --namespace default
```

### JSON / HTML 輸出

```bash
# JSON
npm start -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --from-manifests ./k8s \
  --output json

# HTML
npm start -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --from-manifests ./k8s \
  --output html
```

### 輸出到檔案

```bash
npm start -- \
  --current-version 1.28 \
  --target-version 1.31 \
  --from-manifests ./k8s \
  --output json \
  --output-file ./reports/upgrade-report.json
```

## 輸出與退出碼

- `0`: 所有資源相容目標版本（無 breaking/warning）
- `1`: 發現 breaking 或 warning，需處理後再升級
- `2`: 參數錯誤或執行錯誤

JSON 報告結構可參考：`docs/report.schema.json`

## 規則覆蓋（MVP）

目前已內建以下常見升級風險規則：

- `PodDisruptionBudget` `policy/v1beta1` → `policy/v1`
- `CronJob` `batch/v1beta1` → `batch/v1`
- `Ingress` `extensions/v1beta1` / `networking.k8s.io/v1beta1` → `networking.k8s.io/v1`
- `FlowSchema` `flowcontrol.apiserver.k8s.io/v1beta2` → `flowcontrol.apiserver.k8s.io/v1`
- `PriorityLevelConfiguration` `flowcontrol.apiserver.k8s.io/v1beta2` → `flowcontrol.apiserver.k8s.io/v1`
- `HorizontalPodAutoscaler` `autoscaling/v2beta2` → `autoscaling/v2`

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

此專案屬於 CLI 工具，CI 會在 `main` 分支 push 且測試通過後，上傳 `dist/` 為 GitHub Actions Artifacts。

## 目前限制

- `--kubeconfig`（直接連線叢集掃描）仍在規劃中，現階段先支援 `--from-manifests` 模式
- 尚未支援 CRD 自訂規則載入
- 尚未提供 sandbox（kind/minikube）自動驗證流程

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/17
- CI/CD Workflow: `.github/workflows/ci_17.yml`
