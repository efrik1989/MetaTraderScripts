import logging
import logging.handlers
import core.global_vars as gv

_log_format = f"[%(asctime)s] - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"

def get_file_handler(filename):
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(_log_format))
    return file_handler

def get_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.flush()
    stream_handler.setStream(stream=None)
    stream_handler.setLevel(logging.ERROR)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler

def get_rotate_handler(filename):
    rotate_handler = logging.handlers.TimedRotatingFileHandler(filename, when='H', interval=1, 
                         backupCount=7, encoding=None, 
                         delay=False, utc=False, atTime=None)
    return rotate_handler

def get_logger(name):
    log_filename = gv.global_args.logfile
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_file_handler(log_filename))
    logger.addHandler(get_rotate_handler(log_filename))
    # Стоит ли ошибки выводить в консоль ошибки? Вопрос...
    # logger.addHandler(get_stream_handler())
    logger.propagate = False
    return logger

