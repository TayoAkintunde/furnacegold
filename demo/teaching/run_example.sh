#!/usr/bin/env bash
# Reproduces the screen-recorded-teaching example end to end in an isolated, git-ignored data dir.
# Model-backed agent outputs come from *_responses.json (authored by the Claude Code session operator,
# see build_responses.py); every deterministic check runs for real.
set -euo pipefail
cd "$(dirname "$0")/../.."
export AIBOS_DATA_DIR="$PWD/demo/teaching/data"
rm -rf "$AIBOS_DATA_DIR" demo/teaching/output
python3 demo/teaching/build_responses.py >/dev/null
mkdir -p demo/teaching/output

python3 -m aibos /teach-today --sources demo/teaching/sources.json \
  --responses demo/teaching/teach_today_responses.json | tee demo/teaching/output/1_teach_today_console.txt
ID=$(python3 -m aibos teaching list --status RESEARCHED | grep recommended | awk '{print $1}')

echo "--- /record before approval (must refuse) ---" | tee demo/teaching/output/2_record_console.txt
python3 -m aibos /record "$ID" --responses demo/teaching/record_responses.json | tee -a demo/teaching/output/2_record_console.txt || true
# In YOUR workflow only you select topics. Here a demo operator selects, and the history records it.
python3 -m aibos teaching select "$ID" --by "demo-operator (illustration only, not the owner)" | tee -a demo/teaching/output/2_record_console.txt
python3 -m aibos /record "$ID" --responses demo/teaching/record_responses.json | tee -a demo/teaching/output/2_record_console.txt

python3 -m aibos /content-from-recording "$ID" \
  --transcript demo/teaching/SCRIPT_READTHROUGH_NOT_A_REAL_RECORDING.vtt \
  --by "demo-operator (script read-through, NOT a real recording)" \
  --responses demo/teaching/content_responses.json | tee demo/teaching/output/3_content_console.txt

python3 -m aibos teaching list > demo/teaching/output/teaching_db.txt
python3 -m aibos approvals list > demo/teaching/output/approval_queue.txt
python3 -m aibos teaching show "$ID" > demo/teaching/output/teaching_item.json
cp demo/teaching/data/runs/*/teach_today.md demo/teaching/output/1_teach_today.md
cp demo/teaching/data/teaching/"$ID"/recording_package.md demo/teaching/output/2_recording_package.md
cp demo/teaching/data/teaching/"$ID"/content_package.md demo/teaching/output/3_content_package.md
sed -i "s#$PWD/##g" demo/teaching/output/*.txt demo/teaching/output/*.md demo/teaching/output/*.json
echo "outputs in demo/teaching/output/"
