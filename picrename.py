#!/usr/bin/env python
import os, sys, shutil, re
import struct
from datetime import datetime
from stat import *
import EXIF

# static strings

exif_dt = "EXIF DateTimeOriginal"	# exif tag name
exif_format = "%Y:%m:%d %H:%M:%S"	# exif format is with colons
out_format = "%Y-%m-%d %H-%M-%S"	# output format with dashes
ext_out = ".jpg" 			# always rename to .jpg

base_target = "/media/photos/01_DIGITAL-CAM/%Y/%m_%B/"

ATOM_HEADER_SIZE = 8
EPOCH_ADJUSTER = 2082844800   # difference between Unix epoch and QuickTime epoch, in seconds

# cache directory names so that we do not have to stat the same dir all the time
dirs_cache = []
# duplicate name pattern
pat = re.compile("\((\d+)\)$")
patdir = "%Y%m%d-%H%M%S"

def walktree(top):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    for f in os.listdir(top):
        if f.startswith('.') :  # ignore hidden files and directories
            continue
        pathname = os.path.join(top, f)
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):
            # It's a directory, recurse into it
            walktree(pathname)
        elif S_ISREG(mode):
            # Lowercase extension
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.jpeg','.jpg','.nef','.png','.gif','.tif','.tiff'] :   # now we only support these 3
                renamepic(pathname)
            elif ext in ['.mov','.mp4'] : # video
                renamemov(pathname)
            else :
                print "skipping %s - %s", [pathname, os.path.splitext(f)[1].lower()]
        else:
            # Unknown file type, print a message
            print 'Skipping %s' % pathname


# Move file safely from source to dest
# - If the dest directory tree does not exist, create it
# - If the dest already exists, add a running number to the file name _i before the extension
# - If files with same basename but different extensions exist, move those as well.
 
def safemove(source, dest) :

    destdir = os.path.dirname(dest)

    # check only once, then lookup from the cache
    if destdir not in dirs_cache :
        dirs_cache.append(destdir)

        # check if it exists, otherwise create recursively
        if not os.path.exists(destdir) :
            os.makedirs(destdir)

    if os.path.exists(dest) :
        base0, ext = os.path.splitext(dest)
        base = base0 + " (1)"  # start count with 1
        n = 1
        while os.path.exists(base + ext) :
            base = base0 + " ("+ str(n) +")"
            n = n + 1

        dest = base + ext
        print dest

    print "%s move to %s" % (source, dest)
    shutil.move(source, dest)


def renamepic(file):
#    print 'visiting', file

    f = open(file, 'rb')
    tags = EXIF.process_file(f)

    if exif_dt in tags :     # just look for the datetime original tag

        dt = datetime.strptime(str(tags[exif_dt]),exif_format)   # read in date format
        base, ext = os.path.splitext(file)

        # if NEF format, convert file first
        if ext.lower() == '.nef' :
            os.system("dcraw -c -w -T %s > %s" % (file, base + ".tif"))
            os.system("convert %s %s" % (base + ".tif", base + ext_out))
            os.remove(base + ".tif")
            safemove(base + ext_out, dt.strftime(base_target) + dt.strftime(out_format) + ext_out)
            safemove(base + ext, dt.strftime(base_target) + dt.strftime(out_format) + ext)

        elif ext.lower() in ['.png','.gif','.tif','.tiff'] :
            os.system("convert %s %s" % (file, base + ext_out))
            safemove(base + ext_out, dt.strftime(base_target) + dt.strftime(out_format) + ext_out)
            safemove(base + ext, dt.strftime(base_target) + dt.strftime(out_format) + ext)

        elif ext.lower() in ['.jpg','.jpeg'] :
            safemove(file, dt.strftime(base_target) + dt.strftime(out_format) + ext_out)

    else :
        print "No original date found in %s" % file
        # lets see if the last directory has a useful convention for datetime
        s1, s2 = os.path.split(file)
        s3, d = os.path.split(s1)
        try:
            dt = datetime.strptime(d,patdir)   # read in date format if possible
            safemove(file, dt.strftime(base_target) + dt.strftime(out_format) + ext_out)
        except ValueError :
            # did not manage to do it
            print "failed with %s" % file

def renamemov(file):

    # open file and search for moov item
    f = open(file, "rb")
    while 1:
        atom_header = f.read(ATOM_HEADER_SIZE)
        if len(atom_header) < 4:
            return
        if atom_header[4:8] == 'moov':
            break
        else:
            atom_size = struct.unpack(">I", atom_header[0:4])[0]
            f.seek(atom_size - 8, 1)

    # found 'moov', look for 'mvhd' and timestamps
    atom_header = f.read(ATOM_HEADER_SIZE)
    if atom_header[4:8] == 'cmov':
        print "moov atom is compressed"
    elif atom_header[4:8] != 'mvhd':
        print "expected to find 'mvhd' header"
    else:
        f.seek(4, 1)
        creation_date = struct.unpack(">I", f.read(4))[0]
        modification_date = struct.unpack(">I", f.read(4))[0]

    dat = datetime.utcfromtimestamp(creation_date - EPOCH_ADJUSTER)
    mod = datetime.utcfromtimestamp(modification_date - EPOCH_ADJUSTER)

    safemove(file, dat.strftime(base_target) +"filmchen/" + dat.strftime(out_format) + ".mov")     

if __name__ == '__main__':
    walktree(sys.argv[1])
