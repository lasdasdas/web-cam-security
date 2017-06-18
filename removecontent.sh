#!/usr/bin/bash

#Automating the removal of the movement detection entries
echo Removing detections.txt content
> detections.txt
echo Removing detection image folder content
rm -rf static/frame/detec*
