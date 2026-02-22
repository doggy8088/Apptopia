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
