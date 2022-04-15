import os
import sys
from time import sleep

pid = str(os.getpid())
pidfile = "/tmp/mydaemon.pid"

if os.path.isfile(pidfile):
    print ("%s already exists, exiting" % pidfile)
    sys.exit()

with open(pidfile,"w") as file_object:
    file_object.write(pid)
    
try:
    sleep(300)
finally:
    os.unlink(pidfile)