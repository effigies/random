#!/usr/bin/env python3
import sys
import time
import psutil
import subprocess


def main(cmd, *argv):
    target = subprocess.Popen(argv)
    pid = str(target.pid)
    proc = psutil.Process(target.pid)
    with open('qprof.{}.tsv'.format(pid), 'w') as fobj:

        while target.poll() is None:
            ctime = time.ctime()
            mem = proc.memory_info()
            print(f'{ctime}\t{mem.rss}\t{mem.vms}', file=fobj)
            time.sleep(1)

    return 0


def run_main():
    sys.exit(main(*sys.argv))


if __name__ == '__main__':
    run_main()
