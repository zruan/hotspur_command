import chimera 
import sys
from chimera import runCommand

id = int(sys.argv[1])

runCommand("open run_it%03d*.mrc" % id)
runCommand("turn x 90")
runCommand("volume all level 0.02")
runCommand("volume all step 1")
runCommand("tile")
runCommand("background solid white")
runCommand("export preview%03d.html" % id)


