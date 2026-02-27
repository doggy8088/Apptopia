# Issue #42: 專案 Skill/Agent 分析產生器

## 簡介

此專案提供 `project-orchestrator` CLI，可讀取 PRD/spec/plan 等文件，產出結構化的 capability analysis，並比對既有 registry、生成缺失的 skill/agent 定義與 execution plan。支援 JSON/YAML/Markdown 輸出，適合離線或本地工作流使用。

## 安裝

```bash
cd apps/issue-42
npm install
```

## 使用

分析專案文件：

```bash
node dist/index.js analyze \
  --prd ./docs/prd.md \
  --spec ./docs/spec.md \
  --plan ./docs/plan.md \
  --format json \
  --output ./out/analysis.json
```

比對 registry 覆蓋：

```bash
node dist/index.js compare \
  --analysis ./out/analysis.json \
  --registry ./registry/registry.json \
  --format md
```

產生缺失的 skill/agent 定義：

```bash
node dist/index.js generate \
  --analysis ./out/analysis.json \
  --registry ./registry/registry.json \
  --format yaml \
  --output-dir ./out/generated
```

產出 execution plan：

```bash
node dist/index.js plan \
  --analysis ./out/analysis.json \
  --format md \
  --output ./out/execution-plan.md
```

初始化與驗證 registry：

```bash
node dist/index.js init-registry --format json --output ./registry/registry.json
node dist/index.js validate-registry --registry ./registry/registry.json
```

## 測試

```bash
cd apps/issue-42
npm test
```

## 建置

```bash
cd apps/issue-42
npm run build
```

## 部署

此專案為 CLI 工具，建置後可透過 GitHub Actions Artifacts 下載產物。

## 相關連結

- 原始 Issue: https://github.com/doggy8088/Apptopia/issues/42
- CI/CD Workflow: `.github/workflows/ci_42.yml`
