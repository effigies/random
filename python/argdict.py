"""Key-dependent defaultdict"""
import collections

class argdict(collections.defaultdict):
    """argdict(default_factory[, ...]) --> dict with default factory

    The default factory is called with the key as argument to produce
    a new value when a key is not present, in __getitem__ only. An
    argdict compares equal to a dict with the same items. All
    remaining arguments are treated the same as if they were passed
    to the dict constructor, including keyword arguments.
    """
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError((key,))
        self[key] = value = self.default_factory(key)
        return value
