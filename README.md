# bybitFuturesClient
This is an interface for Bybit Perpetual USDT Futures API (v5) for the following utilities:

1. Get account's balance (USDT)
2. List exchange pairs
3. Get necessary trading params:  
    min_size, price, price_precision,  
    quantity_precision, step_size
4. Set leverage & margin
5. Place market & stop loss order
6. Get open positions
7. Get filled orders
8. Close all open positions
9. Cancel all pending orders

# Useful links:
1. [pybit](https://github.com/bybit-exchange/pybit)
2. [Bybit Futures API](https://bybit-exchange.github.io/docs/v5/intro)
3. [Bybit Futures Testnet](https://testnet.bybit.com/trade/usdt/BTCUSDT)

# Installation
Python version >= 3.10 is required.  
  
`pip3 install pybit`

# Usage:
```python
client = BybitUniFutures(apikey= <BYBIT_FUTURES_APIKEY>, apisecret= <BYBIT_FUTURES_APISECRET>, testnet= False)

params = client.get_pair_parameters("BTCUSDT")

market_order = client.market_order("BTCUSDT", "long", 0.010)

sl_order = client.sltp_order("BTCUSDT", <TP_PRICE>, <SL_PRICE>)

client.close_all_positions("BTCUSDT)
```
