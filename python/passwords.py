#!/usr/bin/env python3
import numpy as np
import re

dictionary = '/usr/share/dict/words'

word = re.compile(r'^[a-z]+$')

with open(dictionary) as f:
    valid = np.asarray([x for x in map(str.strip, f) if word.match(x)])

print(' '.join(valid[np.random.randint(len(valid), size=(3,))]))
