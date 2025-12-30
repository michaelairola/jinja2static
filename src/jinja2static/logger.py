import logging
from logging import Formatter
import sys

bold_yellow = "\x1b[33;1m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"


# Custom formatter
class Formatter(Formatter):
    default_formatter = Formatter("%(msg)s")
    FORMATTERS = {
        logging.DEBUG: Formatter("%(asctime)s - %(message)s (%(name)s:%(lineno)d)"),
        logging.INFO: Formatter("%(msg)s"),
        logging.WARNING: Formatter(bold_yellow + "WARNING: %(msg)s" + reset),
        logging.ERROR: Formatter(bold_red + "ERROR: %(msg)s" + reset),
    }

    def format(self, record):
        formatter = self.FORMATTERS.get(record.levelno, self.default_formatter)
        return formatter.format(record)


def configure_logging(verbose: bool = False):
    fmt = Formatter()
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.DEBUG if verbose else logging.INFO)
