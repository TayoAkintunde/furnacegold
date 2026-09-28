---
description: Produce the complete screen-recording package for a topic the owner approved
argument-hint: "<teaching item id>"
---
Produce the complete screen-recording package for teaching item: $ARGUMENTS

1. Check the item with `python -m aibos teaching show $ARGUMENTS`.
   - If its status is not SELECTED (or READY_TO_RECORD), stop and ask the owner whether to select it.
   - The command to select it is `python -m aibos teaching select <id> --by <name>`, and only the owner decides.
2. Run `python -m aibos record $ARGUMENTS`. Add `--regenerate` only if the owner asks for a new plan or script.
3. If model-backed agents report NO_MODEL, follow the same openly-labelled responses-file procedure described in `/teach-today`.
4. Show the owner `data/teaching/<id>/recording_package.md`:
   - the checklist of what to do before pressing record
   - the recording plan
   - the spoken script
   - the beginner, intermediate and advanced versions
   - the production details
   - any blocking checks
   If the item did not reach READY_TO_RECORD, explain exactly which checks blocked it.
