#!/bin/bash

find /data/dbbackup -name otrs.stackato.com* -mtime +30 -exec rm -f {} \;
#find /data/dbbackup -name otrs.stackato.com* -mtime +30 -print

exit
