#!/bin/bash
while true; do
    killall distributed_tor_scraper.py
    killall distributed_tor.sh
    killall tor
    ./distributed_tor.sh

    #sleep 4 hours then repeat the python programs seem
    # to be taking more and more memory need to restart the program to prevent running out
    sleep 3h

done
