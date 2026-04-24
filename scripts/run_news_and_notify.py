import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib import request

from dotenv import load_dotenv

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


def chunk_text(text: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunk = remaining[:split_at].rstrip()
        chunks.append(chunk)
        remaining = remaining[split_at:].lstrip("\n")
    return chunks


def send_feishu_text(webhook_url: str, text: str) -> str:
    payload = {
        "msg_type": "text",
        "content": {"text": text},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description="Run news analyst and send Feishu webhook.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. TSLA")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Analysis date YYYY-MM-DD")
    parser.add_argument("--webhook", required=True, help="Feishu webhook URL")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "deepseek"
    config["deep_think_llm"] = "deepseek-chat"
    config["quick_think_llm"] = "deepseek-chat"
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "alpha_vantage",
    }

    agent = TradingAgentsGraph(selected_analysts=["news"], debug=False, config=config)
    state, decision = agent.propagate(args.ticker.upper(), args.date)

    out_dir = project_root / "reports" / f"{args.ticker.upper()}_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "news_report.md"
    decision_path = out_dir / "decision.txt"

    news_report = state.get("news_report", "")
    news_text = news_report if isinstance(news_report, str) else str(news_report)
    report_path.write_text(news_text, encoding="utf-8")
    decision_path.write_text(str(decision), encoding="utf-8")

    feishu_intro = (
        f"[TradingAgents News Analyst]\n"
        f"Ticker: {args.ticker.upper()}\n"
        f"Date: {args.date}\n"
        f"Decision: {decision}\n"
        f"Report: {report_path}\n"
        f"Sending full report in chunks..."
    )
    feishu_responses = [send_feishu_text(args.webhook, feishu_intro)]

    report_chunks = chunk_text(news_text, max_chars=2800)
    for idx, chunk in enumerate(report_chunks, start=1):
        chunk_message = (
            f"[TSLA News Report {idx}/{len(report_chunks)}]\n"
            f"{chunk}"
        )
        feishu_responses.append(send_feishu_text(args.webhook, chunk_message))

    print(f"REPORT_PATH={report_path}")
    print(f"DECISION_PATH={decision_path}")
    print(f"DECISION={decision}")
    print(f"FEISHU_CHUNKS={len(report_chunks)}")
    print(f"FEISHU_RESPONSES={feishu_responses}")


if __name__ == "__main__":
    main()
