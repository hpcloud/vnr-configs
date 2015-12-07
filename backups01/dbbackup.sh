#!/bin/sh

# The backup account needs SELECT and LOCK TABLES granted on each db to be
# backed up.

for i in otrs3; do
	DATE=`date +%F`
	TIME=`date +%R`
	echo Processing otrs.stackato.com-$DATE-$TIME
	mysqldump $i -h otrs.stackato.com -u backup -pyoucanttouchthisdoodoodoodoo --max_allowed_packet=1G > /data/dbbackup/otrs.stackato.com-$DATE-$TIME.sql
	bzip2 -9v /data/dbbackup/otrs.stackato.com-$DATE-$TIME.sql
done
