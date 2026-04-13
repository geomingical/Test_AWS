import json
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

load_dotenv()

PORTFOLIO_PATH = os.getenv("MY_PORTOFOLIO")

mcp = FastMCP("StockPortfolioMCP", log_level="ERROR")


def _load_portfolio() -> dict:
    with open(PORTFOLIO_PATH, "r") as f:
        return json.load(f)


def _save_portfolio(data: dict) -> None:
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(data, f, indent=4)


@mcp.tool(
    name="read_stock_portfolio",
    description=(
        "Read stocks from the portfolio and return them as a JSON string. "
        "Pass a stock ticker symbol (e.g. 'NVDA') to retrieve that specific stock. "
        "If stock_id is empty or not provided, all stocks in the portfolio are returned."
    ),
)
def read_stock_portfolio(
    stock_id: str = Field(default="", description="Ticker symbol of the stock to read. Leave empty to list all stocks."),
) -> str:
    data = _load_portfolio()
    if not stock_id:
        return json.dumps(data["portfolio"], indent=2)

    matches = [s for s in data["portfolio"] if s["name"].upper() == stock_id.upper()]
    if not matches:
        return json.dumps({"message": f"No stock with id '{stock_id}' found in the portfolio."})
    return json.dumps(matches, indent=2)


@mcp.tool(
    name="add_stock_portfolio",
    description="Add a new stock purchase lot to the portfolio. Multiple entries for the same ticker are allowed (e.g. different purchase dates).",
)
def add_stock_portfolio(
    name: str = Field(description="Ticker symbol of the stock (e.g. 'NVDA')"),
    quantity: float = Field(description="Number of shares purchased"),
    purchase_price: float = Field(description="Price per share at purchase"),
    purchase_date: str = Field(description="Date of purchase in YYYY-MM-DD format"),
) -> str:
    data = _load_portfolio()
    entry = {
        "name": name.upper(),
        "quantity": quantity,
        "purchase_price": purchase_price,
        "purchase_date": purchase_date,
    }
    data["portfolio"].append(entry)
    _save_portfolio(data)
    return json.dumps({"message": f"Added {quantity} shares of {name.upper()} at ${purchase_price} on {purchase_date}."})


@mcp.tool(
    name="sold_stock_portfolio",
    description=(
        "Record a sale of shares. Quantity is deducted from profitable lots first "
        "(sold_price > purchase_price, highest purchase price first), then from non-profitable lots "
        "if needed. Can span multiple lots. Fully sold lots are removed from the portfolio."
    ),
)
def sold_stock_portfolio(
    name: str = Field(description="Ticker symbol of the stock to sell (e.g. 'NVDA')"),
    quantity: float = Field(description="Number of shares to sell"),
    sold_price: float = Field(description="Price per share at sale"),
) -> str:
    data = _load_portfolio()
    ticker = name.upper()

    holdings = [s for s in data["portfolio"] if s["name"].upper() == ticker]
    if not holdings:
        return json.dumps({"message": f"No holdings found for '{ticker}'."})

    total_held = sum(s["quantity"] for s in holdings)
    if quantity > total_held:
        return json.dumps({
            "message": f"Cannot sell {quantity} shares of {ticker}: only {total_held} shares held."
        })

    # Profitable lots (sold_price > purchase_price) are deducted first,
    # highest purchase price first. Non-profitable lots follow the same ordering
    # as a fallback when profitable shares are exhausted.
    profitable = sorted(
        [s for s in holdings if sold_price > s["purchase_price"]],
        key=lambda s: s["purchase_price"], reverse=True
    )
    non_profitable = sorted(
        [s for s in holdings if sold_price <= s["purchase_price"]],
        key=lambda s: s["purchase_price"], reverse=True
    )

    remaining_to_sell = quantity
    for lot in profitable + non_profitable:
        if remaining_to_sell <= 0:
            break
        if lot["quantity"] <= remaining_to_sell:
            remaining_to_sell -= lot["quantity"]
            lot["quantity"] = 0
        else:
            lot["quantity"] -= remaining_to_sell
            remaining_to_sell = 0

    # Rebuild portfolio: keep other tickers, plus non-zero lots of this ticker
    other = [s for s in data["portfolio"] if s["name"].upper() != ticker]
    remaining_lots = [s for s in holdings if s["quantity"] > 0]
    data["portfolio"] = other + remaining_lots

    _save_portfolio(data)
    return json.dumps({
        "message": f"Sold {quantity} shares of {ticker} at ${sold_price}.",
        "remaining_shares": sum(s["quantity"] for s in remaining_lots),
    })


@mcp.prompt(
    name="short_term_stock_recommendation",
    description="Provides a short-term stock recommendation based on the current portfolio.",
)
def short_term_stock_recommendation(
    stock_id: str = Field(description="Id of the stock to analyze"),
) -> list[base.Message]:
    prompt = f"""
    Make sure you are using the most recent stock prices data (with Yahoo-Finance MCP if needed).
    Base on the price changes during the last week,
    if I want to take a strategy to do buy-and-sell in short time to make small gain.
    I want control my investment budget under $1000. Base on the latest price of

    <stock_id>
    {stock_id}
    </stock_id>

    What is my buy or sell price?

    If I already have the stock, what is the best price to sell it? The price must be higher than the purchase price.

    If I don't have the stock, get me the best price to buy it based on the price changes in the most recent 5 trading days.
    If buying, how many shares can I buy with $1000?

    Also make a brief of the most important recent market and finance news about this stock.
    Send the news brief and analysis report to the discord channel "nvda-daily-brief".
    """

    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
