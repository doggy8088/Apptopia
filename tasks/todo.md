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
