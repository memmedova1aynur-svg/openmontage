#!/usr/bin/env bash
# Cut, transcribe, align and pause-trim one project in one go (no denoiser anywhere):
#   keep.json -> cut.mp4 -> transcript -> words.json (corrected.txt) -> find_pauses -> tighten (KEEPWORDS) -> cut.mp4
# Usage: templates/expert-reels/scripts/prep_cut.sh <project-id> [source=flipped.mp4]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
S="$ROOT/templates/expert-reels/scripts"
P="$ROOT/projects/$1"
SRC="$P/assets/source/${2:-flipped.mp4}"
python3 "$S/cut_takes.py" "$SRC" "$P/artifacts/speech_16k_transcript.json" "$P/artifacts/keep.json" "$P/assets/video/cut.mp4" "$P/artifacts/cut_words_rough.json" | tail -1
ffmpeg -v error -y -i "$P/assets/video/cut.mp4" -vn -ac 1 -ar 16000 "$P/assets/audio/cut16k.wav"
python3 "$S/transcribe.py" "$P/assets/audio/cut16k.wav" "$P/artifacts/cut16k_transcript.json" > /dev/null 2>&1
python3 "$S/align_words.py" "$P/artifacts/cut16k_transcript.json" "$P/artifacts/corrected.txt" "$P/artifacts/words.json" | tail -1
REM="$(python3 "$S/find_pauses.py" "$P/assets/video/cut.mp4")"
echo "pauses: $REM"
if [ "$REM" != "[]" ]; then
  KEEPWORDS=1 REMOVE="$REM" python3 "$S/tighten.py" "$P" "$SRC"
  python3 "$S/cut_takes.py" "$SRC" "$P/artifacts/speech_16k_transcript.json" "$P/artifacts/keep.json" "$P/assets/video/cut.mp4" "$P/artifacts/cut_words_rough.json" | tail -1
fi
