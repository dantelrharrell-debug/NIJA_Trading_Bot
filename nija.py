    # --- paste this inside class NijaBot in nija.py ---
    def run_live(self):
        """
        Compatibility wrapper for older/newer method names so main.py can do:
            for trade in nija.run_live():
        It will:
          - try common candidate methods on this object (callable)
          - if a candidate returns an iterable/generator, it yields each item
          - if a candidate is blocking and returns None, it yields heartbeat None periodically
          - if a candidate returns a single value, it yields it once
        If nothing compatible is found, it raises AttributeError with a clear message.
        """
        import time

        candidate_names = (
            "start_trading_loop", "start_trading", "start", "run", "run_loop",
            "trade_loop", "execute_trades", "main_loop", "live_loop", "run_live"
        )

        # Try candidates in order (skip calling this wrapper recursively)
        for name in candidate_names:
            if name == "run_live":
                # avoid recursion: if the class already defines run_live, calling getattr() would return this method
                # so check for another attribute with the same name defined on the class (i.e., skip self).
                # If user actually has a different run_live method, it will have been defined before this one,
                # but to be safe we skip to avoid infinite recursion.
                continue

            func = getattr(self, name, None)
            if not callable(func):
                continue

            try:
                res = func()
            except TypeError:
                # Method signature doesn't match (expects args) — skip and try next candidate
                continue
            except Exception:
                # If method raised an exception when we tried to probe it, re-raise so logs show the real issue
                raise

            # If it returned a generator/iterable (and not a plain str/bytes/dict), yield items
            if hasattr(res, "__iter__") and not isinstance(res, (str, bytes, dict)):
                for item in res:
                    yield item
                return

            # If it returned None, assume it is a blocking runner that handles trading itself.
            # Keep the for-loop alive by yielding periodic heartbeats (None).
            if res is None:
                while True:
                    # heartbeat to keep the for-loop alive without busy waiting
                    time.sleep(0.5)
                    yield None

            # Otherwise it returned a single result — yield it once so old code that expects an iterable still works
            yield res
            return

        # If we get here, no compatible method found — raise helpful error
        raise AttributeError(
            "NijaBot: no compatible live-run method found. Expected one of: "
            "start_trading_loop, start_trading, start, run, run_loop, trade_loop, execute_trades, main_loop."
        )
    # --- end paste ---
class NijaBot:
    def __init__(self, api_key, api_secret, live, tp_percent, sl_percent, trailing_stop, trailing_tp, smart_logic):
        self.api_key = api_key
        self.api_secret = api_secret
        self.live = live
        # etc... store your other params

    def run_bot(self):
        # your trading logic here
        pass

    def check_status(self):
        # return True if bot is running, False otherwise
        return True
