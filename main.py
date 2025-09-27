import time

class NijaBot:
    def __init__(self, exchange=None):
        """
        exchange: an initialized ccxt exchange object (Coinbase, Binance, etc.)
        """
        self.exchange = exchange
        print("✅ NijaBot initialized")

    def run_live(self):
        """
        Compatibility wrapper for older/newer method names so main.py can do:
            for trade in nija.run_live():
        """
        candidate_names = (
            "start_trading_loop", "start_trading", "start", "run", "run_loop",
            "trade_loop", "execute_trades", "main_loop", "live_loop", "run_live"
        )

        for name in candidate_names:
            if name == "run_live":
                continue

            func = getattr(self, name, None)
            if not callable(func):
                continue

            try:
                res = func()
            except TypeError:
                continue
            except Exception as e:
                print(f"❌ Error when calling {name}: {e}")
                raise

            # If it returned a generator
            if hasattr(res, "__iter__") and not isinstance(res, (str, bytes, dict)):
                for item in res:
                    self._log_trade(item)
                    yield item
                return

            # If it returned None (blocking loop)
            if res is None:
                while True:
                    print("🔄 NijaBot heartbeat: still running, waiting for trades...")
                    time.sleep(5)
                    yield None

            # If it returned a single result
            self._log_trade(res)
            yield res
            return

        raise AttributeError(
            "NijaBot: no compatible live-run method found. Expected one of: "
            "start_trading_loop, start_trading, start, run, run_loop, trade_loop, execute_trades, main_loop."
        )

    def _log_trade(self, trade):
        """
        Helper to print clean trade logs.
        Expects trade to be a dict with keys like 'side', 'symbol', 'price', 'amount'
        """
        if not trade:
            return

        if isinstance(trade, dict):
            side = (trade.get("side") or trade.get("action") or trade.get("type") or "UNKNOWN").upper()
            symbol = trade.get("symbol") or trade.get("market") or trade.get("pair") or "UNKNOWN"
            price = trade.get("price") or trade.get("exec_price") or trade.get("filled_price") or "?"
            amount = trade.get("amount") or trade.get("size") or trade.get("qty") or "?"
            print(f"✅ Trade executed: {side} {amount} {symbol} @ {price}")

            # Optional: CCXT order execution placeholder
            # Uncomment and customize if you want to place actual orders
            # try:
            #     order = self.exchange.create_market_order(symbol, side.lower(), amount)
            #     print(f"✅ Order placed on exchange: {order}")
            # except Exception as e:
            #     print(f"❌ Failed to place order on exchange: {e}")

        else:
            print(f"✅ Trade event: {trade}")
