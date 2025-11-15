import logging

type Logger = logging.Logger

file = logging.FileHandler("app.log", mode="a")
file.setLevel(logging.DEBUG)

fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file.setFormatter(fmt)


def create_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file)
    return logger
