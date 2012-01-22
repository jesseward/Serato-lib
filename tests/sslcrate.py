#!/usr/bin/env python

import mmap
import struct
import sys
from optparse import OptionParser

def readtag(tag):
    """ Returns true of the requested tag was found at the next position in the 
        the mssldb """

    currpos = ssldb.tell()
    foundtag =  ssldb.read(len(tag))

    if foundtag == tag:
        return True
    else:
        ssldb.seek(currpos)
     
def readbytes(numbytes):
    """ Reads a variable length of bytes from the mssldb """

    return ssldb.read(numbytes)

def readvarlenstr(pad=4):
    """ Reads and parses a variable length string field """
    
    varlen = ssldb.read(4)
    varlen = struct.unpack(">L", varlen)
    return ssldb.read(varlen[0])


p = OptionParser()
p.add_option("-f", "--file", dest="dbfile",
             help="Serate Create .db file to read")

(opt, args) = p.parse_args()

if not opt.dbfile:
    p.error("Please specify the SSL crate file to read.")

f = open(opt.dbfile, 'r+b')

ssldb = mmap.mmap(f.fileno(), 0)

while ssldb.tell() < ssldb.size():

    # read VRSN header data
    if readtag('vrsn'):
        vrsn = (ssldb.tell(), readbytes(60))
        print "vrsn %.5d : %s" % (vrsn[0], vrsn[1])

    # handle column sorting tags
    elif readtag('osrt'):
        osrt = (ssldb.tell(), readbytes(4))
        print "osrt %.5d : %s" % (osrt[0], osrt[1])
        
        # read sorted column name header
        if readtag('tvcn'):
            tvcn = (ssldb.tell(), readvarlenstr())
            print "tvcn %.5d : %s" % (tvcn[0], tvcn[1])

        if readtag('brev'):
            brev = (ssldb.tell(), readbytes(5))
            print brev

    # read in the remaining available column data.
    elif readtag('ovct'):
        ovct = (ssldb.tell(), readbytes(4))
        print ovct

        if readtag('tvcn'):
            tvcn = (ssldb.tell(), readvarlenstr())
            print "tvcn %.5d : %s" % (tvcn[0], tvcn[1])

        if readtag('tvcw'):
            tvcw = (ssldb.tell(), readbytes(6))
            print tvcw

    # read in track data.
    elif readtag('otrk'):
        otrk = (ssldb.tell(), readbytes(4))
        tracksize = struct.unpack(">L", otrk[1])
        print "otrk %.5d : %s" % (otrk[0], otrk[1])

        if readtag('ptrk'):
            ssldb.read(4)
            track = (ssldb.tell(), readbytes(tracksize[0]-8))
            print "track %.5d : %s" % (track[0], track[1])
