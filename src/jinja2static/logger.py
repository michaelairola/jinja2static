import logging
import sys
from logging import Formatter, Filter

bold_yellow = "\x1b[33;1m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"

ERROR_FMT = Formatter(bold_red + "ERROR: %(msg)s" + reset)
class Formatter(Formatter):
    default_formatter = Formatter("%(msg)s")
    FORMATTERS = {
        logging.DEBUG: Formatter("%(asctime)s - %(message)s (%(name)s:%(lineno)d)"),
        logging.INFO: Formatter("%(msg)s"),
        logging.WARNING: Formatter(bold_yellow + "WARNING: %(msg)s" + reset),
        logging.ERROR: ERROR_FMT,
    }

    def format(self, record):
        formatter = self.FORMATTERS.get(record.levelno, self.default_formatter)
        return formatter.format(record)

class IgnoreStdErrIfATTY(Filter):
    def filter(self, record):
        return not (record.levelno == logging.ERROR and sys.stderr.isatty())

def configure_logging(verbose: bool = False):
    fmt = Formatter()
    stdout_hdlr = logging.StreamHandler(sys.stdout)
    stdout_hdlr.setFormatter(fmt)
    stdout_hdlr.addFilter(IgnoreStdErrIfATTY())
    logger = logging.getLogger(__name__.split(".")[0])
    logger.addHandler(stdout_hdlr)

    stderr_hdlr = logging.StreamHandler(sys.stderr)
    stderr_hdlr.setFormatter(ERROR_FMT)
    stderr_hdlr.setLevel(logging.ERROR)
    logger.addHandler(stderr_hdlr)

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
