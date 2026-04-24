#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/openclaw/openclaw_workspace/TradingAgents"
DEFAULT_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/27e5a830-6400-4bdd-942e-130b71e19e5e"
ANALYSIS_DATE="$(date +%F)"
TICKER=""
MODE_NEWS=false

for arg in "$@"; do
  case "$arg" in
    --news)
      MODE_NEWS=true
      ;;
    --date=*)
      ANALYSIS_DATE="${arg#*=}"
      ;;
    --ticker=*)
      TICKER="${arg#*=}"
      ;;
    --*)
      if [[ -z "$TICKER" ]]; then
        TICKER="${arg#--}"
      fi
      ;;
    *)
      ;;
  esac
done

if [[ -z "$TICKER" ]]; then
  echo "Usage: ./run_analysis.sh --tsla --news [--date=YYYY-MM-DD]"
  echo "Or:    ./run_analysis.sh --ticker=TSLA --news [--date=YYYY-MM-DD]"
  exit 1
fi

if [[ "$MODE_NEWS" != true ]]; then
  echo "Currently only --news mode is supported."
  exit 1
fi

if [[ -x "/Users/openclaw/miniforge3/bin/conda" ]]; then
  CONDA_BIN="/Users/openclaw/miniforge3/bin/conda"
elif [[ -x "/Users/openclaw/miniconda3/bin/conda" ]]; then
  CONDA_BIN="/Users/openclaw/miniconda3/bin/conda"
else
  echo "Conda not found in /Users/openclaw/miniforge3 or /Users/openclaw/miniconda3"
  exit 1
fi

cd "$PROJECT_DIR"

"$CONDA_BIN" run -n tradingagents python scripts/run_news_and_notify.py \
  --ticker "$TICKER" \
  --date "$ANALYSIS_DATE" \
  --webhook "$DEFAULT_WEBHOOK"
