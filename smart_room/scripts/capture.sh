#!/bin/bash

# Capture Path
# This can be change to anywhere you want
CAPTURE_PATH=$(pwd)/../capture

# Name for save folder
DATE=$(date +"%Y-%m-%d_%p")

# Name for new image
DATED=$(date +"%Y-%m-%d_%T")

# Get old image
OLD_IMAGE=$(find $CAPTURE_PATH -maxdepth 1 -name "*.jpg")

# Capture image
sudo raspistill -o $CAPTURE_PATH/$DATED.jpg -n

# Remove old image
rm -f $OLD_IMAGE

# Create folder if not exist
mkdir -p $CAPTURE_PATH/$DATE

# Compress image to 1MB and save in folders
jpegoptim --size=1024k --dest=$CAPTURE_PATH/$DATE $CAPTURE_PATH/$DATED.jpg
