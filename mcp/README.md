# MCP Server 

## Overview

This MCP server provides tools to manage a stock portfolio, enabling an LLM to analyze market strategies based on current holdings. It supports reading portfolio data, adding new purchase lots, and recording stock sales.

## Original Prompts

### Implementation Tasks

Complete the implementation of `mcp_server.py` by finishing the two MCP tools. The portfolio file is stored in `my_portfolio.json`.

#### read_stock_portfolio

Retrieves stock information from the portfolio. If no `stock_id` is provided, list all stocks. If a `stock_id` is specified but not found, return an empty result (not an error). The tool description should clarify that `stock_id` is optional.

#### add_stock_portfolio

Adds a new purchase lot to the portfolio with the following parameters:
- `name` — stock ticker
- `quantity` — number of shares
- `purchase_price` — price per share
- `purchase_date` — purchase date in YYYY-MM-DD format

#### sold_stock_portfolio

Records a stock sale. Deducts quantity from the lot with the highest purchase price that is lower than the sale price. If the sale price is higher than multiple purchase prices, prioritize the highest purchase price first. Handle multi-lot deductions if the sale quantity exceeds a single lot. After all profitable lots are exhausted, deduct from non-profitable lots if needed. Remove fully-sold lots from the portfolio.

Parameters:
- `name` — stock ticker
- `quantity` — number of shares sold
- `sold_price` — sale price per share

## Prerequisites

- Python 3.9+
- uv

## Setup

### Step 1: Configure the environment variables

1. Edit the `.env` file in the project root and verify that the following variables are set correctly:

```
MY_PORTOFOLIO="/{your_path}/mcp/my_portfolio.json"
```

### Step 2: Install dependencies

Setup with uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Test the project

```bash
mcp dev mcp_server.py
```

## Install it on Claude

Set the MCP configuration:

```json
  {                                                                                                                     
    "mcpServers": {                                                                                                     
      "StockPortfolioMCP": {                                                                                            
        "command": "uv",                                    
        "args": [                                                                                                       
          "run",                                            
          "--project",                                                                                                  
          "/{your_path}/mcp",                      
          "/{your_path}/mcp/mcp_server.py"                                                                     
        ]
      }                                                                                                                 
    }                                                       
  }
```