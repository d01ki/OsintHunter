# OsintHunter

Minimal MVP for an OSINT CTF agent based on the design in agent.md.

## Quick start

```bash
python -m osinthunter.main "Find the flag in this tweet from @sample_user"
```

Options:
- `--file`: Load the problem statement from a text file
- `--url`: Add one or more URLs to the context
- `--image`: Add one or more image paths for image OSINT pivots

### Docker / Compose

```bash
docker compose build
docker compose run --rm app python -m osinthunter.main "Find the flag in this tweet from @sample_user"
```

コンテナ内でシェルを開く場合:

```bash
docker compose run --rm app bash
```

### Web UI (FastAPI)

```bash
docker compose run --rm -p 8000:8000 app uvicorn osinthunter.web.app:app --host 0.0.0.0 --port 8000
```

ブラウザで http://localhost:8000/ を開くと、問題入力フォームと結果ビューが利用できます。Planner/Validator は OpenAI または OpenRouter のキーがある場合に LLM を活性化し、キーが無い場合はヒューリスティックで動作します。

## Configuration

Environment variables (optional):

- `OPENAI_API_KEY` – forwarded to downstream LLMs if you wire them in
- `SERPAPI_API_KEY` or `BING_API_KEY` – used by the search tool when network access is allowed
- `OSINTHUNTER_ALLOW_NETWORK=true` – enable tools that reach the network
- `OSINTHUNTER_MAX_ITERATIONS` – cap iterations (default: 6)
- `OSINTHUNTER_MODEL` – desired model name hint (default: gpt-4o-mini)

## Project layout

- `src/osinthunter/agent.py` – orchestrates the Phase 1 single agent
- `src/osinthunter/models.py` – shared dataclasses for inputs, plan, evidence
- `src/osinthunter/tools/` – individual tools (text analysis, URLs, SNS, web, geo, image)
- `src/osinthunter/main.py` – CLI entrypoint

## Next steps

- Swap the heuristic core with a LangChain agent + LangGraph loop
- Add real web search, WHOIS, OCR, EXIF, and SNS lookups behind API keys
- Persist evidence to a lightweight store (SQLite or JSONL)