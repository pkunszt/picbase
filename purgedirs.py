#!/usr/bin/env python
import os, sys
from stat import *

def walktree(top):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    for f in os.listdir(top):
        pathname = os.path.join(top, f)
        if f.startswith('.') :  # ignore hidden files and directories
            if f == ".DS_Store" or f.startswith("._"):
                print "remove ", pathname
                os.remove(pathname)
            continue
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):
            # It's a directory, recurse into it
            walktree(pathname)
            try:
                os.removedirs(pathname)
            except (OSError):
                print "not empty " + pathname
#        elif S_ISREG(mode):
            
        else:
            # Unknown file type, print a message
            print 'Skipping %s' % pathname



if __name__ == '__main__':
    walktree(sys.argv[1])
