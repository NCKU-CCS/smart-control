#!/bin/bash

DATE=$(date +"%Y-%m-%d")

DATED=$(date +"%Y-%m-%d_%T")

sudo rm /home/pi/smart/capture/*.jpg

sudo raspistill -o /home/pi/smart/capture/$DATED.jpg -n

mkdir -p /home/pi/smart/capture/$DATE

jpegoptim --size=1024k --dest=/home/pi/smart/capture/$DATE /home/pi/smart/capture/$DATED.jpg
