#!/bin/sh
DEST=~/db_backups/
mkdir $DEST
mongodump -h localhost -d Zillow -o $DEST
/usr/local/bin/acd_cli upload -o ~/db_backups/Zillow /ds/db_backups/
