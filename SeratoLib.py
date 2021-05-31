import mmap
import struct
import shutil
import logging

log = logging.getLogger(__name__)

class SSLCrateError(Exception):
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
            raise SSLCrateError("Unable to open %s" % self.crate_file)

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
        """ Reads a variable length of bytes from the mself.ssldb """

        return self.ssldb.read(numbytes)

    def _readvarlenstr(self, pad=4):
        """ Reads and parses a variable length string field """

        varlen = self.ssldb.read(pad)
        varlen = struct.unpack(">L", varlen)
        return self.ssldb.read(varlen[0])

    @staticmethod
    def backup_db(file_name):
        log.info("Backing up Serato library file '%s' to '%s.bak'" \
                        % (file_name, file_name))
        try:
            shutil.copy(file_name, "%s.bak" % file_name)
        except IOError, e:
            log.warn("Skipping back-up due to '%s'" % e)

    @staticmethod
    def null_pad(instr):
        return "".join([ struct.pack("xc", i) for i in instr ])

class Crate(SSL):

    TAG_DEFAULTS = {
        'ovct' : '\x00\x00\x00\x1c', # ???
        'brev' : 0x00, # ???
        'tvcw' : '\x00\x00\x00\x02\x000', # column width
        }

    def __init__(self, crate_file):
        self.crate_file = crate_file
        SSL.__init__(self)
        self.contents = self._parse_crate()

    def _parse_crate(self):
        """ steps through an SSL crate mmap object byte-by-byte, building a
            data structure along the way. Not an exact representation of the
            binary file, as the length (UInt32) has been stripped from the
            varchar fields. """

        crate = {}

        while (self.ssldb.tell() < self.ssldb.size()):

            # read VRSN header data
            if self._read_tag('vrsn'):
                vrsn = self._read_bytes(60)
                crate['vrsn'] = vrsn
                log.debug("Reading create, found VRSN tag '%s'" % vrsn)

            # handle column sorting tags
            elif self._read_tag('osrt'):
                log.debug("Reading crate, found OSRT tag")
                osrt = self._read_bytes(4)
                crate['sort'] = {'osrt': osrt}

                # read sorted column name header
                if self._read_tag('tvcn'):
                    tvcn = self._readvarlenstr()
                    log.debug("Reading crate, found TVCN tag '%s'" % tvcn)
                    crate['sort'].update({'tvcn': tvcn})

                if self._read_tag('brev'):
                    log.debug("Reading crate, found BREV tag")
                    brev = self._read_bytes(5)
                    crate['sort'].update({'brev': brev})

            # read in the remaining available column data.
            elif self._read_tag('ovct'):
                log.debug("Reading crate, found OVCT tag")
                ovct = self._read_bytes(4)
                try:
                    crate['columns'].append({'ovct': ovct})
                except KeyError:
                    crate['columns'] = [{'ovct': ovct}]

                if self._read_tag('tvcn'):
                    tvcn = self._readvarlenstr()
                    log.debug("Reading crate, found TVCN tag '%s'" % tvcn)
                    crate['columns'][-1].update({'tvcn': tvcn})

                if self._read_tag('tvcw'):
                    log.debug("Reading crate, found TVCW tag")
                    tvcw = self._read_bytes(6)
                    crate['columns'][-1].update({'tvcw': tvcw})

            # parse track data.
            elif self._read_tag('otrk'):
                log.debug("Reading crate, found OTRK tag")
                otrk = self._read_bytes(4)
                tracksize = struct.unpack(">L", otrk)

                try:
                    crate['tracks'].append({'otrk': otrk})
                except KeyError:
                    crate['tracks'] = [{'otrk': otrk}]

                if self._read_tag('ptrk'):
                    self.ssldb.read(4)
                    ptrk = self._read_bytes(tracksize[0] - 8)
                    log.debug("Reading crate, found PTRK tag '%s'" % ptrk)
                    crate['tracks'][-1].update({'ptrk': ptrk})
            else:
                raise SSLCrateError("Unexpected binary file format, unable to parse")

        return crate

    def add_column(self, column_name):
        """ Adds a column header to the Serato Crate dict """

        column_name = SSL.null_pad(column_name)
        exist = self._column_exist(column_name)

        if exist:
            raise SSLCrateError("Column header already exists.")
        else:
            self.contents['columns'].append({'ovct': Crate.TAG_DEFAULTS['ovct']})
            self.contents['columns'][-1].update({'tvcn': column_name})
            self.contents['columns'][-1].update({'tvcw': Crate.TAG_DEFAULTS['tvcw']})

    def delete_column(self, column_name):
        """ Removes a column name from the crate dict """

        column_name = SSL.null_pad(column_name)
        exist = self._column_exist(column_name)

        if not exist:
            raise SSLCrateError("Column name does not exist.")
        else:
            del(self.contents['columns'][exist[0]])

    def _column_exist(self, column_name):
        """ Returns column position if present in dict """

        return [ i for i, x in enumerate(self.contents['columns']) \
                    if x['tvcn'] == column_name ]

    def add_track(self, file_name):
        """ Appends the binary packed track data to dict """

        file_name = SSL.null_pad(file_name)

        if self._track_exist(file_name):
            raise SSLCrateError("File already exists in crate.")

        otrk = struct.pack(">L", len(file_name) + 8)

        self.contents['tracks'].append({'otrk': otrk})
        self.contents['tracks'][-1].update({'ptrk': file_name})

    def _track_exist(self, file_name):
        """ Returns position if track is already present in the given crate """

        return [ i for i, x in enumerate(self.contents['tracks']) \
                    if x['ptrk'] == file_name ]

    def delete_track(self, file_name):
        """ Remove a track from the crate """

        file_name = SSL.null_pad(file_name)

        exist = self._track_exist(file_name)

        if not exist:
            raise SSLCrateError("File does not exist in crate")
        else:
            del(self.contents['tracks'][exist[0]])

    def save_crate(self, file_name=None):
        """ Dumps crate file to disk. """

        if file_name is None:
            file_name = self.crate_file

        SSL.backup_db(file_name)

        try:
            f = open(file_name, 'wb')
            log.info("Writing Serato crate file '%s' to disk" % file_name)
        except IOError:
            raise SSLCrateError("Unable to write crate file.")

        # vrsn tag
        f.write(struct.pack("4s%ds" % len(self.version), \
                            "vrsn", \
                            self.version))

        # sorted colum : osrt, tvcn, brev
        f.write(struct.pack(">4s4s4sL%ds4s5s" % len(self.contents['sort']['tvcn']),  \
                            "osrt", \
                            self.contents['sort']['osrt'], \
                            "tvcn", \
                            len(self.contents['sort']['tvcn']), \
                            self.contents['sort']['tvcn'], \
                            "brev", \
                            self.contents['sort']['brev']))

        # available columns : ovct, tvcn, tvcw
        for i, x in enumerate(self.contents['columns']):
            f.write(struct.pack(">4s4s4sL%ds4s%ds" % \
                    (len(self.contents['columns'][i]['tvcn']),
                     len(self.contents['columns'][i]['tvcw'])), \
                    "ovct", \
                    self.contents['columns'][i]['ovct'], \
                    "tvcn", \
                    len(self.contents['columns'][i]['tvcn']), \
                    self.contents['columns'][i]['tvcn'], \
                    "tvcw",
                    self.contents['columns'][i]['tvcw']))

        # available tracks : otrk, ptrk
        for i, x in enumerate(self.contents['tracks']):
            f.write(struct.pack(">4s4s4sL%ds" % \
                    len(self.contents['tracks'][i]['ptrk']), \
                    "otrk", \
                    self.contents['tracks'][i]['otrk'], \
                    "ptrk", \
                    len(self.contents['tracks'][i]['ptrk']), \
                    self.contents['tracks'][i]['ptrk']))

        f.close()

    @property
    def tracks(self):
        return [ t['ptrk'] for t in self.contents['tracks'] ]

    @property
    def version(self):
        return self.contents['vrsn']

    @property
    def columns(self):
        return [ c['tvcn'] for c in self.contents['columns'] ]

class Library(SSL):
    """ TODO: Placeholder for the SSL library file format. """
    pass
