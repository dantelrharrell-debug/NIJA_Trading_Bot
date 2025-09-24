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
