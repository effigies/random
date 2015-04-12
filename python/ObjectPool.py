import threading
import types

class Pool(list):
    """Thread-safe stack of objects not currently in use, generates new object
    when empty.

    Use as a decorator. Decorated classes must have init() method to
    prepare them for reuse."""
    def __init__(self, klass):
        super(Pool, self).__init__()

        self.lock = threading.Lock()
        klass.release = types.MethodType(self.append, None, klass)
        self.klass = klass

    def __call__(self):
        "Get object from pool, generating a new one if empty"
        with self.lock:
            obj = self.pop() if self else self.klass()
        obj.init()
        return obj
