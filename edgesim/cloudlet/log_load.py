import atexit
import os
import sys
import time

import psutil

fp = open(sys.argv[1], "w")

def on_close():
    print "syncing log and shutting down"
    fp.flush()
    os.fsync(fp.fileno())
    fp.close()

atexit.register(on_close)

while True:
    load = psutil.cpu_percent()
    fp.write("%s\n" % load)
    time.sleep(1)
