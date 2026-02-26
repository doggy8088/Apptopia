# Issue 42 V1 Skill/Agent Analyzer Generator

## Scope
- Build a Node.js + TypeScript CLI tool under `apps/issue-42/` for analyzing project docs, mapping capabilities, comparing registries, generating skill/agent definitions, and producing execution plans.
- Support subcommands: `analyze`, `compare`, `generate`, `init-registry`, `validate-registry`, `plan`, `export`.
- Provide JSON/YAML/Markdown outputs with file/dir output options and clear error handling with non-zero exit codes.
- Add tests, README, and CI workflow for issue-42.

## Acceptance criteria (verifiable)
- [ ] `analyze` returns structured project summary and required capabilities when provided valid docs.
- [ ] `compare` marks coverage as covered/partial/missing with a valid registry.
- [ ] `generate` produces at least one skill or agent definition for missing capabilities.
- [ ] `plan` outputs ordered steps with owners and dependencies.
- [ ] `validate-registry` rejects invalid schema with clear errors and non-zero exit code.

## Verification
- [x] `cd apps/issue-42 && npm test`
- [x] `cd apps/issue-42 && npm run build`

## Risks
- Low: heuristic-based parsing may misclassify edge cases; mitigated by clear warnings.

## Rollback notes
- Revert `apps/issue-42/`, `.github/workflows/ci_42.yml`, and this section in `tasks/todo.md`.

---

# Issue 27 V1 Todo

## Scope
- Implement a Telegram bot that downloads videos via `yt-dlp` and returns them if within limits.
- Enforce duration <= 60 minutes and file size <= Telegram Bot API limit.
- Persist conversation logs, downloads, queue status, and user settings under `apps/issue-27/data/`.
- Provide tests, README, and CI workflow.

## Acceptance criteria (verifiable)
- [ ] Valid URL triggers download via `yt-dlp` and returns a video to Telegram.
- [ ] Video duration > 60 minutes returns an error before sending the file.
- [ ] Video size above Telegram Bot API limit returns an error.
- [ ] Single-download queue processes one job at a time and reports queue position.
- [ ] Conversation logs, download logs, queue state, and user settings are persisted under `apps/issue-27/data/`.

## Verification
- [x] `cd apps/issue-27 && npm run lint`
- [x] `cd apps/issue-27 && npm test`
- [x] `cd apps/issue-27 && npm run build`

## Assumptions
- `yt-dlp` is installed and available on PATH (or `YT_DLP_PATH`).
- Telegram Bot API file size limit remains 50 MB per available Bot API references.

## Risks
- Medium: external tools (`yt-dlp`, `ffprobe`) required at runtime.

## Rollback notes
- Revert files under `apps/issue-27/`, `.github/workflows/ci_27.yml`, and `tasks/todo.md`.

---

# Issue 27 Oversize Azure Blob Fallback (2026-02-22)

## Scope
- When a downloaded file exceeds Telegram Bot size limit, optionally upload to Azure Blob Container via SAS URL and reply with the uploaded link instead of rejecting immediately.
- Keep original rejection behavior when the SAS URL env var is not configured.
- Return a human-readable error message when Azure upload is configured but fails.
- Document the new env var and 7-day retention behavior in `apps/issue-27/README.md`.

## Acceptance criteria (verifiable)
- [ ] `AZURE_BLOB_CONTAINER_SAS_URL` unset: oversized files still return the original Telegram-limit rejection message.
- [ ] `AZURE_BLOB_CONTAINER_SAS_URL` set and upload succeeds: bot replies with Azure Blob link for oversized files.
- [ ] `AZURE_BLOB_CONTAINER_SAS_URL` set and upload fails: bot replies with a human-readable reason.
- [ ] README documents the new env var and notes Azure lifecycle auto-delete after 7 days.

## Verification
- [x] `cd apps/issue-27 && npm test`
- [x] `cd apps/issue-27 && npm run build`

## Risks
- Medium: Blob upload requires correct container-level SAS permissions and expiry.

## Rollback notes
- Revert `apps/issue-27/src/azureBlob.ts`, `apps/issue-27/src/bot.ts`, `apps/issue-27/src/index.ts`, `apps/issue-27/src/types.ts`, `apps/issue-27/tests/azureBlob.test.ts`, `apps/issue-27/README.md`.

---

# Issue 18 V1 Obsidian Book Compiler

## Scope
- Build a Node.js + TypeScript CLI that compiles Obsidian vault notes into a book-style Markdown manuscript.
- Support `--vault`, `--topic`, `--config`, `--output-format`, and `--dry-run` CLI options.
- Implement tag/folder/keyword filtering, wikilinks, embeds, callouts, and frontmatter parsing.
- Generate `book.md`, `book.yaml`, and copy assets into `output/assets/`.
- Provide tests, README, and CI workflow for issue-18.

## Acceptance criteria (verifiable)
- [ ] `--topic "#python"` selects tagged notes and produces `book.md` with linked chapters.
- [ ] `--topic "folder:Guides"` filters by directory and outputs only those notes.
- [ ] `--topic "keyword:kubernetes"` filters by keyword in content.
- [ ] Callout and wikilink conversions match the documented rules in output.
- [ ] `--dry-run` prints chapter order without writing output files.

## Verification
- [x] `cd apps/issue-18 && npm run lint`
- [x] `cd apps/issue-18 && npm test`
- [x] `cd apps/issue-18 && npm run build`

## Risks
- Low: simple graph ordering may differ from advanced PageRank ordering for dense vaults.

## Rollback notes
- Revert `apps/issue-18/`, `.github/workflows/ci_18.yml`, and `tasks/todo.md`.

---

# Issue 35 V1 Treadmill Pace Converter

## Scope
- Build a static web app under `apps/issue-35/` with pace <-> speed conversion.
- Support pace input formats: `mmss` (e.g. `610`) and `m:ss` (e.g. `6:10`).
- Provide conversion results in cards plus validation and reset actions.
- Implement dark green UI with system theme detection and PWA offline support.
- Add README and CI workflow for issue-35.

## Acceptance criteria (verifiable)
- [ ] Input speed 10.0 km/h converts to pace `6'00"`.
- [ ] Input speed 6.0 km/h converts to pace `10'00"`.
- [ ] Input speed 15.0 km/h converts to pace `4'00"`.
- [ ] Input pace `4'30"` (or `430`) converts to speed `13.3` km/h.
- [ ] Invalid pace input (e.g. `abc`) shows an error and does not crash.
- [ ] Offline refresh still loads the app and conversion works.
- [ ] Dark mode styling matches the deep-green theme and maintains AA contrast.

## Verification
- [x] `cd apps/issue-35 && npm test`
- [x] `cd apps/issue-35 && npm run build`

## Assumptions
- Static hosting on GitHub Pages is acceptable for offline PWA assets.

## Risks
- Low: service worker caching could stale assets during rapid iteration.

## Rollback notes
- Revert `apps/issue-35/`, `.github/workflows/ci_35.yml`, and this section in `tasks/todo.md`.

---

# Repo Policy: Remove GitHub Pages Jobs (2026-02-23)

## Scope
- Remove GitHub Pages deploy jobs from workflows in `.github/workflows/`.
- Ensure the example workflow template no longer includes GitHub Pages jobs.

## Acceptance criteria (verifiable)
- [x] No GitHub Pages-related actions (`actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`) appear in `.github/workflows/`.
- [x] No workflow permissions include `pages: write`.

## Verification
- [x] `rg -n "configure-pages|deploy-pages|upload-pages-artifact|pages: write|GitHub Pages" .github/workflows`

## Risks
- Low: Removing these jobs disables GitHub Pages deployments.

## Rollback notes
- Revert `.github/workflows/ci_8.yml`, `.github/workflows/ci_19.yml`, `.github/workflows/ci_example.yml.template`, and this section in `tasks/todo.md`.

---

# Issue 36 V1 LinguistFlow

## Scope
- Build a Chrome MV3 extension under `apps/issue-36/` for selecting YouTube captions and writing to Notion.
- Provide a Shadow DOM caption overlay, context menu action, and Notion API integration.
- Store settings and offline queue locally with retry.
- Provide README, tests, and CI workflow for issue-36.

## Acceptance criteria (verifiable)
- [ ] Selecting caption text and triggering "Add to Notion" creates a Notion payload with Word/Definition/Context/Grammar/Status.
- [ ] Overlay remains anchored when entering fullscreen and remains selectable.
- [ ] Offline failures enqueue items for retry and do not crash.

## Verification
- [x] `cd apps/issue-36 && npm test`
- [x] `cd apps/issue-36 && npm run build`

## Assumptions
- Users enable YouTube captions to populate the overlay.
- Notion database fields match the expected names.

## Risks
- Medium: YouTube DOM changes can affect caption scraping.

## Rollback notes
- Revert `apps/issue-36/`, `.github/workflows/ci_36.yml`, and this section in `tasks/todo.md`.
