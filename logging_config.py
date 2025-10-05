# logging_config.py
import logging
import logging.handlers
import sys
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": int(record.created),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, default=str)

def setup_logging(app_name="nija-bot", log_file="/tmp/nija-bot.log"):
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # stdout handler (platform-friendly)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(JsonFormatter())
    root.addHandler(sh)

    # rotating file for local debugging / retention
    fh = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=7)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JsonFormatter())
    root.addHandler(fh)

    # reduce noisy libs
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# call at app startup
