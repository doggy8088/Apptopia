# Issue 17 V1 Bootstrap Todo

## Scope (Initial implementation)
- Build a TypeScript CLI scaffold for `k8s-upgrade-validator`.
- Support version validation for Kubernetes minor versions 1.25+
- Implement offline scanning from local manifests (`--from-manifests`) for V1 bootstrap.
- Analyze resources against API deprecation/removal rules.
- Output reports in `text`, `json`, and `html`.
- Return non-zero exit code when breaking/warning findings exist; `0` when fully compatible.
- Add CI workflow `.github/workflows/ci_17.yml`.

## Acceptance criteria (verifiable)
- [x] Given a manifest using `policy/v1beta1` PDB and versions `1.28 -> 1.31`, report marks it as breaking and suggests `policy/v1`.
- [x] Given only compatible manifests, CLI exits with code `0` and text report states compatibility.
- [x] `--output json` writes schema-compliant report object.
- [x] Invalid target version returns a clear error and supported version range.

## Verification tasks
- [x] `cd apps/issue-17 && npm test`
- [x] `cd apps/issue-17 && npm run build`
- [x] `cd apps/issue-17 && npm run check`

## Risk level
- Medium: Kubernetes live-cluster scanning via kubeconfig is not fully implemented in this bootstrap slice.

## Rollback notes
- Revert only files under `apps/issue-17/`, `.github/workflows/ci_17.yml`, and `tasks/todo.md`.

## Working notes
- Prefer minimal in-repo deprecation rule dataset first, then expand.
- Keep analyzer pure and deterministic for fast unit tests.
- Keep report schema explicit to support CI integrations.
