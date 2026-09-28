---
description: Turn a completed screen recording (transcript) into the full repurposed content package
argument-hint: "<teaching item id> <transcript file (.srt/.vtt/.txt)>"
---
Arguments: $ARGUMENTS (a teaching item id, then the path to the owner's transcript).

1. Confirm the transcript file exists and came from the owner's actual recording. Never write or invent a transcript.
2. Run `python -m aibos content-from-recording <id> --transcript <file> --by <owner name>`.
3. If model-backed agents report NO_MODEL, follow the openly-labelled responses-file procedure described in `/teach-today`.
4. Show the owner `data/teaching/<id>/content_package.md`. It contains all 14 formats, each with its purpose, value statement and quality status.
5. Every piece waits in `python -m aibos approvals list`. Never publish. The owner advances the workflow (EDITING → READY_TO_PUBLISH → PUBLISHED --url) themselves.
