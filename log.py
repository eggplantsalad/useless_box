import config
import time


def log(s: str, level=1):
    if level <= config.loglevel:
        t = time.monotonic_ns() / (1000 * 1000 * 1000)

        print('%03.3f: %s' % (t, s))
