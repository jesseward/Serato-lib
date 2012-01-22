import mmap
import struct
import logging

log = logging.getLogger(__name__)

class SSLIoError(Exception):
    pass


class SSL(object):

    def __init__(self):
        self.ssldb = self.read_db_file()


    def read_db_file(self):
        """ loads the given file into an mmap object """

        try:
            f = open(self.crate_file, "r+b")
            log.info("Reading Serato file %s" % self.crate_file)
        except:
            raise SSLIoError("Unable to open %s" % self.crate_file)

        sslmap = mmap.mmap(f.fileno(), 0)
        f.close()

        return sslmap

    def _read_tag(self, tag):

        currpos = self.ssldb.tell()
        foundtag =  self.ssldb.read(len(tag))

        if foundtag == tag:
            return True
        else:
            self.ssldb.seek(currpos)

    def _read_bytes(self, numbytes):
        """ Reads a variable length of bytes from the ssldb """

        return self.ssldb.read(numbytes)

    def _readvarlenstr(self, pad=4):
        """ Reads and parses a variable length string field """

        varlen = self.ssldb.read(pad)
        varlen = struct.unpack(">L", varlen)
        return self.ssldb.read(varlen[0])

    @staticmethod
    def null_pad(instr):
        return "".join([ struct.pack("xc", i) for i in instr ])

