import threading
import types
import warnings


class Pool(list):
    """Thread-safe stack of objects not currently in use, generates new object
    when empty. Objects have a release() method that reinserts them into the
    pool.

    Use as a decorator. Decorated classes must have init() method to
    prepare them for reuse.

    Currently renders pydoc useless.

    Example:

    @Pool
    class myClass(object):
        def __init__(self, ...):
            ...

        def init(self):
            ...

    obj = myClass()
    obj.release()
    """
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


def pool(klass):
    """Thread-safe pool of objects not currently in use, generates new object
    when empty.

    Use as a decorator. Decorated classes must have init() method to
    prepare them for reuse."""
    lock = threading.Lock()
    pool = set()

    orig_new = klass.__new__
    orig_init = klass.__init__

    def __new__(cls, *args, **kwargs):
        "Get object from pool, generating a new one if empty"
        with lock:
            if pool:
                obj = pool.pop()
                obj._used = True
                return obj
        return orig_new(cls, *args, **kwargs)
    klass.__new__ = classmethod(__new__)

    def __init__(self, *args, **kwargs):
        if hasattr(self, '_used'):
            self.init()
            del self._used
            return

        orig_init(self, *args, **kwargs)
    klass.__init__ = __init__

    def release(self):
        """Release for reuse"""
        if self in pool:
            warnings.warn(RuntimeWarning('Attempting double-release of ' +
                                         klass.__name__))
        else:
            pool.add(self)
    klass.release = release

    return klass


@Pool
class TestPooling(object):
    """Basic object that contains x attribute, default value 1"""
    def init(self):
        self.x = 1
