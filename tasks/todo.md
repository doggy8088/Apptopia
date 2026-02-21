# Issue 27 Telegram Bot Todo

## Scope (V1 implementation)
- Build a Telegram bot (Node.js + TypeScript) that accepts a video URL and downloads via `yt-dlp`.
- Enforce a 60-minute duration limit (metadata first; download+probe fallback).
- Enforce Telegram bot file size limit; reject oversized files.
- Process downloads sequentially via a single-worker queue.
- Persist conversation logs, download logs, queue state, and user settings under `data/`.
- Provide README and CI workflow for Issue #27.

## Acceptance criteria (verifiable)
- [x] When given a valid URL <= 1000 bytes, the bot queues the request and processes in order.
- [x] Videos longer than 60 minutes are rejected with a clear error message.
- [x] Downloads exceeding Telegram's file size limit are rejected with a clear error message.
- [x] Queue state and logs are written to `apps/issue-27/data/`.
- [x] `npm test` and `npm run build` succeed in `apps/issue-27`.

## Verification tasks
- [x] `cd apps/issue-27 && npm test`
- [x] `cd apps/issue-27 && npm run build`

## Risk level
- Medium: relies on external tools (`yt-dlp`, optional `ffprobe`) and Telegram API constraints.

## Rollback notes
- Revert only files under `apps/issue-27/`, `.github/workflows/ci_27.yml`, and `tasks/todo.md`.

## Working notes
- Use `yt-dlp --dump-single-json` to read metadata; fallback to probing downloaded files if needed.
- Store logs as JSONL and queue/user settings as JSON for simplicity.
- Ensure clear, user-facing error messages for invalid input and limits.
