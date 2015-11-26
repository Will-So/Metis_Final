#!/bin/bash
killall distributed_tor_scraper.py
killall distributed_tor.sh
sudo killall tor

./distributed_tor.sh
