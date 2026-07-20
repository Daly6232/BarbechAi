import logging
import sys
import contextvars

# Set by the request-ID middleware in main.py at the start of each request,
# read here so every log line emitted while handling that request carries
# the same ID — makes it possible to grep one request's full story out of
# otherwise-interleaved concurrent request logs.
request_id_var = contextvars.ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [req:%(request_id)s] %(name)s: %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(_RequestIdFilter())

    logger.addHandler(handler)

    return logger
