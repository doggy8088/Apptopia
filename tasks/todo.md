# Issue 27 plan

## Scope
- Implement Telegram bot that downloads videos via yt-dlp and returns them if within limits.
- Enforce duration <= 60 minutes and file size <= Telegram limit.
- Persist conversation, downloads, queue status, and user settings under apps/issue-27/data.
- Provide tests, README, and CI workflow.

## Checklist
- [x] Scaffold apps/issue-27 Node + TypeScript project with build/test scripts
- [x] Implement URL validation, duration parsing, size limit checks
- [x] Implement queue with persistence
- [x] Implement yt-dlp integration and Telegram bot handlers
- [x] Add JSON storage helpers and data folder setup
- [x] Add tests for validation, limits, and queue
- [x] Add README and CI workflow

## Verification
- [x] npm test (apps/issue-27)
- [x] npm run build (apps/issue-27)

## Risks
- Medium: external tools (yt-dlp, ffprobe) required at runtime
- Rollback: revert apps/issue-27 and ci_27 workflow changes
