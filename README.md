# Binance Futures Testnet Trading Bot (Colab-Friendly)

A small Python application for the Python Developer intern assignment. It places `MARKET` and `LIMIT` orders on Binance Futures Testnet (USDT-M), supports both `BUY` and `SELL`, validates CLI input, logs API requests/responses/errors, and separates the client layer from the CLI layer.

## Project structure

```text
trading_bot_colab_submission/
├── bot/
│   ├── __init__.py
│   ├── cli.py
│   ├── client.py
│   ├── exceptions.py
│   ├── logging_config.py
│   ├── orders.py
│   └── validators.py
├── logs/
├── .env.example
├── README.md
└── requirements.txt
```

## Why this version works well in Google Colab

- You can run the CLI with `!python -m bot.cli ...` directly in notebook cells.
- API credentials can be set through environment variables in Colab.
- The `--log-file` option makes it easy to generate one log file for a market order and another for a limit order.
- A companion notebook is included: `Trading_Bot_Assignment_Colab.ipynb`.

## Setup in Google Colab

1. Upload the project zip or the notebook to Colab.
2. Install dependencies:

```python
!pip install -r requirements.txt
```

3. Set credentials:

```python
import os
from getpass import getpass

os.environ["BINANCE_API_KEY"] = getpass("Binance Testnet API Key: ")
os.environ["BINANCE_API_SECRET"] = getpass("Binance Testnet API Secret: ")
```

4. Optional: set the base URL explicitly:

```python
os.environ["BINANCE_BASE_URL"] = "https://testnet.binancefuture.com"
```

## Run examples

### MARKET order example

```python
!python -m bot.cli   --symbol BTCUSDT   --side BUY   --order-type MARKET   --quantity 0.002   --log-file logs/market_order.log
```

### LIMIT order example

```python
!python -m bot.cli   --symbol BTCUSDT   --side SELL   --order-type LIMIT   --quantity 0.002   --price 120000   --log-file logs/limit_order.log
```

### Dry-run example (validation only)

```python
!python -m bot.cli   --symbol BTCUSDT   --side BUY   --order-type MARKET   --quantity 0.002   --dry-run
```

## Output behaviour

The app prints:

- order request summary
- order response details (`orderId`, `status`, `executedQty`, `avgPrice` if available)
- success/failure message

The app logs:

- API requests
- API responses
- network errors
- Binance API errors

## Assumptions

- The user has valid Binance Futures Testnet API credentials.
- The account is in one-way mode (default behaviour for this simple assignment).
- The chosen symbol is available on testnet.
- The quantity and price satisfy the exchange filters for the chosen symbol.
- The assignment states `https://testnet.binancefuture.com`; current Binance docs also reference `https://demo-fapi.binance.com` for USDⓈ-M testnet/demo REST. The CLI keeps the base URL configurable so either can be used if needed.

## Submission notes

After placing one market order and one limit order, include the generated files from `logs/` in your submission.

In Colab you can package everything with:

```python
!zip -r trading_bot_submission_ready.zip .
```
