import os
import time
from errno import EEXIST


class DirectoryBasedLock(object):
    def __init__(self, path):
        self.path = path
        self._have_lock = False

    def acquire(self, blocking=True, delay=0.01, max_delay=0.1, timeout=None):
        tic = time.time()
        if timeout is not None:
            init = tic
            finish = init + timeout

        inc = delay
        while blocking:
            try:
                os.makedirs(self.path)
                self._have_lock = True
                return True
            except OSError as err:
                if err.errno != EEXIST:
                    raise

            if not blocking:
                break

            toc = tic + delay
            if timeout is not None and finish < toc:
                toc = finish
                blocking = False

            delay = min(delay + inc, max_delay)
            time.sleep(max(toc - time.time(), 0))

        return False

    def release(self, *args, **kwargs):
        if not self._have_lock:
            raise RuntimeError("Can't release unowned lock")
        self._have_lock = False
        os.rmdir(self.path)

    __enter__ = acquire
    __exit__ = release


def test():
    pid = os.fork()
    lock = DirectoryBasedLock('/tmp/dirlock.lock')
    with lock:
        print(pid)
        time.sleep(5)
    if pid:
        os.waitpid(pid, 0)
    else:
        # Correctly exits in Python shell, not IPython
        import sys
        sys.exit(0)
