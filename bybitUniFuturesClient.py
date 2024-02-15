import time, math, traceback
from pprint import pprint

from pybit.unified_trading import HTTP



class BybitUniFutures():
    """
    This is an interface for Bybit Perpetual USDT Futures API for the following basic utils:
    1) Get account's balance (USDT)
    2) List exchange pairs
    3) Get necessary trading params:
        min_size, price, price_precision, 
        quantity_precision, step_size
    4) Set leverage & margin
    5) Place market & stop loss order
    6) Get open positions
    7) Get filled orders
    8) Close all open positions
    9) Cancel all pending orders


    base_url = "https://api.bybit.com"
    testnet = False

    Useful links:
        https://github.com/bybit-exchange/pybit
        https://bybit-exchange.github.io/docs/futuresV2/linear/#t-introduction
        https://testnet.bybit.com/trade/usdt/BTCUSDT
    
    For testnet usage set:
        base_url = "https://api-testnet.bybit.com"
        testnet = True
    """


    def __init__(self, apikey= None, apisecret= None, testnet= False, account_type= "UNIFIED", **kwargs):
        """account_type = ["UNIFIED", "CONTRACT"]"""
        self.client = HTTP(testnet= testnet, api_key= apikey, api_secret= apisecret, **kwargs)
        self.account_type = account_type
        self.get_precisions()


    
    def round_decimals_down(self, number:float, decimals):
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)

        factor = 10 ** decimals
        return math.floor(number * factor) / factor

    # Get USDT Balance
    def get_balance(self, coin= "USDT"):
        balance = 0
        try:
            wallet = self.client.get_wallet_balance(accountType= self.account_type, coin= coin)['result']['list'][0]['coin']
            balance = float(next(c for c in wallet if c['coin'] == coin)['equity'])            
            return({"success": balance})
        except Exception as e:
            ex = f"Error: Get futures balance:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
    

    # Get list of exchange pairs
    def get_pairs(self, coin= "USDT"):
        try:
            all_futures = [pair['name'] for pair in self.client.query_symbol()['result'] if pair['name'][-4:] == coin]
            all_futures.sort()
            return({"success": all_futures})
        except Exception as e:
            ex = f"Error: Get futures pairs:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})


    # Load pair informations
    def get_precisions(self):
        try:
            self.symbols_info = self.client.get_instruments_info(category="linear")['result']['list']
        except Exception as e:
            print(f"Error: Get futures precisions:\n{traceback.format_exc()}\n{e}")
    

    # Get useful pair parameters
    def get_pair_parameters(self, pair= "BTCUSDT"):
        try:
            info = next(s for s in self.symbols_info if s['symbol'] == pair)
            lotsize_filter = info['lotSizeFilter']
            price_filter = info['priceFilter']
            min_size = lotsize_filter['minOrderQty']
            step_size = lotsize_filter['qtyStep']
            tick_size = price_filter['tickSize']
            quantity_precision = 0 if len(step_size.split(".")) == 1 else len(step_size.split(".")[1])
            price_precision = 0 if len(tick_size.split(".")) == 1 else len(tick_size.split(".")[1])
            price = self.client.get_tickers(category="linear", symbol= pair)['result']['list'][0]['lastPrice']

            params = {
                "min_size": float(min_size),
                "price": float(price),
                "quantity_precision": int(quantity_precision),
                "price_precision": int(price_precision),
                "step_size": float(step_size)
            }
            return(params)
        except Exception as e:
            ex = f"Error: Get pair parameters:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
    

    # Set leverage
    def set_leverage(self, pair, leverage= 1):
        try:
            lev_resp = "No need to change leverage"
            position = None
            position = self.client.get_positions(category= "linear", symbol= pair)['result']['list'][0]
            
            if position:
                lev = float(position['leverage'])

                if leverage != lev:
                    lev_resp = self.client.set_leverage(category= "linear", symbol= pair, buyLeverage= str(leverage), sellLeverage= str(leverage))

            return({"success": lev_resp})
        except Exception as e:
            ex = f"Error: Set leverage:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
    

    # Set margin type
    def set_margin_type(self, pair, margin_type= "ISOLATED", leverage= None):
        """ margin_type = ["CROSSED", "ISOLATED"] """
        try:
            symbol_position = self.client.my_position(symbol= pair)['result'][0]
            lev = symbol_position['leverage'] if not leverage else leverage

            margin_resp = "No need to change margin type"
            if symbol_position['is_isolated'] and margin_type == "CROSSED":
                margin_resp = self.client.cross_isolated_margin_switch(symbol= pair, is_isolated=False, buy_leverage=lev, sell_leverage=lev)
            elif not symbol_position['is_isolated'] and margin_type == "ISOLATED":
                margin_resp = self.client.cross_isolated_margin_switch(symbol= pair, is_isolated=True, buy_leverage=lev, sell_leverage=lev)

            return({"success": margin_resp})
        except Exception as e:
            ex = f"Error: Set futures margin type:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
    

    # Place order
    def make_order(self, pair, side, quantity, market):
        orderObj = {
            "category": "linear",
            "positionIdx": 0, # if hedge mode remove it
            "symbol": pair,
            "side": side,
            "orderType": market,
            "qty": quantity,
            "timeInForce": "GoodTillCancel",
            "reduceOnly": False,
            "closeOnTrigger": False,
        }
            
        try:
            order = self.client.place_order(**orderObj)['result']

            time.sleep(0.5)

            amount = quantity
            order_price = 0
            order_side = "none"
            order_id = "none"


            if "orderId" in order:
                new_order = self.get_order(pair, order['orderId'])
                if "success" in new_order:
                    amount = new_order['success']['amount']
                    order_price = new_order['success']['price']
                    order_side = new_order['success']['side']
                    order_id = order['orderId']

            params = {
                "id": order_id,
                "pair": pair,
                "side": order_side,
                "amount": amount,
                "price": order_price
            }

            return({"success": params})
        except Exception as e:
            return({"error": str(e)})
    

    # Place market order
    def market_order(self, pair, side, precized_quantity):
        """ This is for one-way mode """
        try:
            if side == "long":
                order = self.make_order(pair, "Buy", precized_quantity, "Market")
            else:
                order = self.make_order(pair, "Sell", precized_quantity, "Market")

            return(order)
        except Exception as e:
            ex = f"Error: Place market order:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
        
    
    # Place stop loss order
    def sltp_order(self, pair, tp_price, sl_price):
        """ This is for one-way mode """
        try:
            orderObj = {
                "category": "linear",
                "positionIdx": 0, # if hedge mode remove it
                "symbol": pair,
                "takeProfit": tp_price,
                "stopLoss": sl_price
            }

            order = self.client.set_trading_stop(**orderObj)

            return(order)
        except Exception as e:
            ex = f"Error: Place sltp order:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
        

    # Cloase all positions
    def close_all_positions(self):
        try:
            positions = [pos['data'] for pos in self.client.my_position()['result'] if pos['data']['size'] > 0]

            for pos in positions:
                if pos['side'] == "Buy":
                    order = self.market_order(pos['symbol'], "short", pos['size'])
                elif pos['side'] == "Sell":
                    order = self.market_order(pos['symbol'], "long", pos['size'])
            
            message = "close-done"
            print(message)
            return({"success": message})
        except Exception as e:
            ex = f"Error: Close all positions:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
        

    # Cancel all open orders
    def cancel_all_orders(self, pair= "BTCUSDT"):
        try:
            result = self.client.cancel_all_active_orders(symbol= pair)
            message = "cancel-done"
            if result['ret_msg'] != "OK":
                message = "cancel-failed"
                    
            print(message)
            return({"success": message})
        except Exception as e:
            ex = f"Error: Cancel all orders:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})


    # Get pair position
    def get_position(self, pair= "BTCUSDT"):
        try:
            symbol = pair
            amount = 0
            price = 0
            leverage = 0

            position = None
            position = self.client.get_positions(category= "linear", symbol= pair)['result']['list'][0]
            
            if position:
                amount = float(position['size']) if position['side'] == "Buy" else -float(position['size'])
                price = float(position['avgPrice'])
                leverage = float(position['leverage'])

            params = {
                "pair": symbol,
                "amount": amount,
                "price": price,
                "leverage": leverage
            }

            return({"success": params})
        except Exception as e:
            ex = f"Error: Get active positions:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})


    # Get filled order
    def get_order(self, pair, order_id):
        try:
            symbol = pair
            side = "none"
            amount = 0
            price = 0
            
            order = None
            got_order = False

            while not got_order:
                userOrders = self.client.get_open_orders(category= "linear", symbol= symbol, orderId= order_id)['result']['list']
                if userOrders:
                    order = userOrders[0]
                    got_order = True
                time.sleep(0.5)

            if order:
                side = order['side'].lower()
                amount = float(order['qty'])
                price = float(order['avgPrice'])
            
            params = {
                "pair": symbol,
                "side": side,
                "amount": amount,
                "price": price
            }

            return({"success": params})
        except Exception as e:
            ex = f"Error: Get order:\n{traceback.format_exc()}\n"
            print(ex)
            return({"error": ex + str(e)})
    
