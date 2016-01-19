#!/bin/sh

# The backup account needs SELECT and LOCK TABLES granted on each db to be
# backed up.

DATE=`date +%F`
TIME=`date +%R`

echo Processing otrs.stackato.com-$DATE-$TIME
ssh backups@otrs.stackato.com '/usr/bin/mysqldump -u otrs -pbug99300 -h west2-mysql-otrs.cfaikxnuj1in.us-west-2.rds.amazonaws.com --max_allowed_packet=1G otrs' > /data/dbbackup/otrs.stackato.com-$DATE-$TIME.sql
bzip2 -9v /data/dbbackup/otrs.stackato.com-$DATE-$TIME.sql
