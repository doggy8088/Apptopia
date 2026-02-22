# Issue 19 V1 Todo

## Scope
- Build a pure frontend Open Moneybook app in `apps/issue-19/` (HTML/CSS/JS, no framework).
- Persist data in IndexedDB (transactions, budgets, categories seed).
- Provide CSV import/export with the standard format (YYYY-MM-DD, income/expense, positive amount).
- Provide dashboard summary, budget progress + over-budget alert, and basic charts.
- Add PWA basics (manifest + service worker) and GitHub Pages-ready build.
- Add README and CI workflow.

## Acceptance criteria (verifiable)
- [ ] Adding a $150 expense persists to IndexedDB and appears after reload.
- [ ] Monthly summary totals (income, expense, balance) are correct for the selected month.
- [ ] Budget $5000 for a category triggers an over-budget warning when exceeded.
- [ ] CSV export matches the standard header and can be re-imported to restore records.
- [ ] Data remains after closing and reopening the browser.

## Verification
- [x] `cd apps/issue-19 && npm test`
- [x] `cd apps/issue-19 && npm run build`

## Assumptions
- Node.js 20+ is available for tests/build.
- Browser supports IndexedDB and modern ES modules.

## Risks
- Low: CSV parsing edge cases with quoted commas.

## Rollback notes
- Revert files under `apps/issue-19/`, `.github/workflows/ci_19.yml`, and `tasks/todo.md`.
