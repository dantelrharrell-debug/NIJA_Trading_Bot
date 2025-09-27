import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class NijaBot:
    def __init__(self, exchange=None):
        """
        exchange: an initialized ccxt exchange object (Coinbase, Binance, etc.)
        """
        self.exchange = exchange
        logging.info("✅ NijaBot initialized")

    def run_live(self):
        """
        Universal live-run wrapper so you can do:
            for trade in nija.run_live()
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
                logging.error(f"❌ Error when calling {name}: {e}")
                raise

            if hasattr(res, "__iter__") and not isinstance(res, (str, bytes, dict)):
                for item in res:
                    self._log_trade(item)
                    yield item
                return

            if res is None:
                while True:
                    logging.info("🔄 NijaBot heartbeat: still running, waiting for trades...")
                    time.sleep(5)
                    yield None

            self._log_trade(res)
            yield res
            return

        raise AttributeError(
            "NijaBot: no compatible live-run method found. Expected one of: "
            "start_trading_loop, start_trading, start, run, run_loop, trade_loop, execute_trades, main_loop."
        )

    def _log_trade(self, trade):
        """
        Logs trades cleanly for easy reading
        """
        if not trade:
            return

        if isinstance(trade, dict):
            side = (trade.get("side") or trade.get("action") or trade.get("type") or "UNKNOWN").upper()
            symbol = trade.get("symbol") or trade.get("market") or trade.get("pair") or "UNKNOWN"
            price = trade.get("price") or trade.get("exec_price") or trade.get("filled_price") or "?"
            amount = trade.get("amount") or trade.get("size") or trade.get("qty") or "?"
            logging.info(f"✅ Trade executed: {side} {amount} {symbol} @ {price}")

            # Optional: Uncomment to place real orders with CCXT
            # try:
            #     order = self.exchange.create_market_order(symbol, side.lower(), amount)
            #     logging.info(f"✅ Order placed on exchange: {order}")
            # except Exception as e:
            #     logging.error(f"❌ Failed to place order on exchange: {e}")

        else:
            logging.info(f"✅ Trade event: {trade}")

def start_trading(nija=None):
    """
    Fully upgraded trading loop
    """
    if nija is None:
        try:
            nija = NijaBot()
        except Exception as e:
            logging.exception(f"Failed to init NijaBot: {e}")
            return

    logging.info("Starting trading runner (listening for trades)...")

    try:
        for trade in nija.run_live():
            try:
                if trade is None:
                    continue

                logging.info(f"RAW TRADE: {repr(trade)}")

                if isinstance(trade, dict):
                    side = (trade.get("side") or trade.get("action") or trade.get("type") or "UNKNOWN").upper()
                    symbol = trade.get("symbol") or trade.get("market") or trade.get("pair") or "UNKNOWN"
                    price = trade.get("price") or trade.get("exec_price") or trade.get("filled_price") or "?"
                    amount = trade.get("amount") or trade.get("size") or trade.get("qty") or "?"
                    logging.info(f"✅ Trade processed: {side} {amount} {symbol} @ {price}")
                else:
                    logging.info(f"✅ Trade processed (non-dict): {trade}")

            except Exception as inner_e:
                logging.exception(f"Error processing trade payload: {inner_e}")

    except Exception as outer_e:
        logging.exception(f"Live trading runner crashed: {outer_e}")
        try:
            time.sleep(2)
        except Exception:
            pass

    logging.info("start_trading ended.")

# If you want it to start automatically when you run this file:
if __name__ == "__main__":
    nija = NijaBot()
    start_trading(nija)
