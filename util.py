import uuid
import time


def get_random_filename(ext=None):
    tmp_filename = uuid.uuid4()
    return str(tmp_filename) + '.{}'.format(ext) if ext else str(tmp_filename)


def get_datetime():
    return time.time()


def get_random_filename_with_datetime(ext=None, sep='-'):
    tmp_filename = uuid.uuid4()
    filename = str(tmp_filename) + '{}{}'.format(sep, time.time()) + '.{}'.format(ext) if ext else ''
    return filename

