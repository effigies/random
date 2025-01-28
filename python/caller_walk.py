import inspect
from pathlib import Path

def find_from_path(predicate, path):
    res = predicate(path)
    if res.exists():
        return res

    if path.parent == path:
        return None

    return find_from_path(predicate, path.parent)


def find(predicate, depth=1):
    frame = inspect.currentframe()
    for _ in range(depth):
        frame = frame.f_back

    caller_fname = frame.f_locals["__file__"]
    return find_from_path(predicate, Path.cwd() / caller_fname)
