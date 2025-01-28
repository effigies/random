import os
from pathlib import Path


def abbreviate_name(name, chars):
    if len(name) <= chars:
        return name
    startchars = chars // 2 - 2
    endchars = chars - (startchars + 3)
    return f"{name[:startchars]}...{name[-endchars:]}"


def find_skip(counts, limit, replace=4):
    skips = []
    for stop in range(len(counts) - 1, 1, -1):
        print(stop)
        for start in range(1, stop):
            print(start)
            if sum(counts[:start] + counts[stop:]) + replace <= limit:
                skips.append((start, stop))

    print(skips)
    if skips:
        return min(skips, key=lambda skip: skip[1] - skip[0])
    return None


def abbreviate_path(pathlike, softmax=50, hardmax=60):
    path = Path(pathlike)
    if len(str(path)) > softmax:
        if len(path.name) + 4 >= hardmax:
            return f".../{abbreviate_name(path.name, hardmax - 4)}"

        dirlens = [len(part) + 1 for part in path.parts[1:-1]]  # Add sep
        counts = [len(path.parts[0])] + dirlens + [len(path.name)]
        print(path.parts)
        print(counts)
        skips = find_skip(counts, softmax)
        if not skips:
            skips = find_skip(counts, hardmax)
        parts = path.parts[:skips[0]] + ("...",) + path.parts[skips[1]:]
        path = os.path.join(*parts)
    return str(path)
