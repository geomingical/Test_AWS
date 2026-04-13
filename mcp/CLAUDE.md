# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

Requires Python 3.10+ and a `.env` file with:

```
MY_PORTOFOLIO="/{your_path}/mcp/my_portfolio.json"
```

```bash
uv venv && source .venv/bin/activate
uv pip install -e .
```

## Running

```bash
uv run mcp_server.py   # stdio transport
```

## Claude Desktop installation

In `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "StockPortfolioMCP": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/Users/samson/Desktop/mcp",
        "/Users/samson/Desktop/mcp/mcp_server.py"
      ]
    }
  }
}
```

## Architecture

Single-file FastMCP server (`mcp_server.py`) backed by a JSON portfolio file (`my_portfolio.json`).

### MCP surface

| Type | Name | Purpose |
|------|------|---------|
| Tool | `read_stock_portfolio` | Read one stock by ticker, or all if `stock_id` is empty |
| Tool | `add_stock_portfolio` | Add a purchase lot (`name`, `quantity`, `purchase_price`, `purchase_date` YYYY-MM-DD) |
| Tool | `sold_stock_portfolio` | Record a sale; see sell logic below |
| Prompt | `short_term_stock_recommendation` | Buy/sell recommendation; requires Yahoo-Finance MCP and Discord MCP at runtime, posts to Discord channel `nvda-daily-brief` |

### Data model

`my_portfolio.json` holds a `portfolio` array of purchase lots:
```json
{ "name": "NVDA", "quantity": 10, "purchase_price": 188.00, "purchase_date": "2026-01-15" }
```
Multiple lots per ticker are allowed (e.g. different buy dates).

### Sell logic (`sold_stock_portfolio`)

Deduction order across lots for the same ticker:
1. Profitable lots (`sold_price > purchase_price`), highest purchase price first
2. Non-profitable lots as fallback, highest purchase price first

Lots reduced to zero quantity are removed from the portfolio.
