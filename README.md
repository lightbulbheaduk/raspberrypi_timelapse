# raspberrypi_timelapse

A little project from a few years ago that in daylight hours takes a photo every x minutes and uploads it to an online location, then once a month during night hours, creates a timelapse of the images from that month (after normalising white balance across all images for that month to minimise flicker) and uploads that to an online location via SCP

To avoid the need for a password, prior to setting this to run, generate an SSH key on pi (using the ssh-keygen command), then copy it to ftphost into ~/.ssh/authorized_keys

Requires:
- fswebcam (https://github.com/fsphil/fswebcam) - for capturing the images
- avconv (https://github.com/binarykitchen/avconv) - for creating the timelapse video


## fswebcam.conf
Contains settings for the webcam, number of frames per second etc - feel free to leave these as is

## cameraconfig.py
Contains the settings for the script - at a minimum add in ftphost, ftpuser and ftpfolder.  Change the locale options to where the camera will be located, so that sunrise and sunset times can be calculated (this could also be used to set gps info in the EXIF of the image)

## camera_common.py
Contains functions to add a watermark to the image (used to put the time and date on and optionally a logo), check the wifi connection and set up the logging

## camera_script.py
Does the main bulk of the work in an infinite loop (NB: you may wish to set something to restart the script every so often, as after a few months I think there might be a memory leak) to take the pictures, move them to the right folder locations, upload the images and kick off the creation of the timelapse

## create_upload_timelapse.py
Normalises the RGB values across a folder of images (iterating over each pixel in turn, so this is expensive!) based on deviation from the average, then creates an mp4 timelapse of the images using avconv before uploading it to an online location
