WHAT
====

The goal of this repo is to document the basic file formats of the Rane Serato
Scratch Live databases.

The libraries generated from this work should eventually allow for read/write
actions against the SSL db/crate files

sslcrate.py
===========

Simple script that reads the crate file into a python mmap object. Data is 
parsed in sequential order, and spewed to console.

Meant for debugging and education purposes.

SeratoLib.py
============

Currently providing limited (add/delete columns/tracks) to the SSL crate 
library. 

TODO
====
Nothing. This is not active.

- generate read / write classes for library files
- s/mmap/construct/ libraries for cleaner parsing  of the binary structures
- dechipher "unknown" SSL tags (brev, ovct, tvcw). 
- run a test, and attempt to open with SSL ;-)
