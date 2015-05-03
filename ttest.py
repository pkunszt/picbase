#!/usr/bin/env python
import os,sys
import EXIF

f = open(sys.argv[1], 'rb')
tags = EXIF.process_file(f)
if "EXIF DateTimeOriginal" not in tags :
    print "No original date found"
else :
    print "Original Date = %s" % tags["EXIF DateTimeOriginal"]


for tag in tags.keys():
    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename',
                   'EXIF MakerNote'):
        print "%s = %s" % (tag, tags[tag])
