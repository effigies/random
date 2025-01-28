from caller_walk import find
from pathlib import Path

res = find(lambda x: x / "config.yml")
if res:
    print(res)
else:
    print("Could not find!")
