#!/bin/bash
# getting data from ecdc

DDIR=covid/data/
DFILE=covid19-worldwide.csv
DLOG=covid19-worldwide.log
TODAY=$(date +"%Y-%m-%d")
OLDFILE=covid19-worldwide-${TODAY}.csv

mv $DDIR$DFILE $DDIR$OLDFILE

if ! wget https://opendata.ecdc.europa.eu/covid19/casedistribution/csv -O $DDIR$DFILE -o $DDIR$DLOG; then
    mv $DIR$OLDFILE $DIR$FILE 
    echo error: rollback to old data file >> $DDIR$DLOG
fi
