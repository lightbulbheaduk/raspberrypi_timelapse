#!/usr/bin/python3

import datetime
import os
import pytz
import subprocess
import time

from astral import Astral, Location
from gi.repository import GExiv2
from PIL import Image, ImageDraw, ImageFont, ImageStat

import camera_common
import cameraconfig

def copyimagefortimelapse(imagepath, imagetime):
    # get concatenated current month and year of image (for folder name)
    foldername = time.strftime(cameraconfig.FOLDER_DATE_PATTERN,imagetime)
    yearfoldername = time.strftime(cameraconfig.YEAR_FOLDER_DATE_PATTERN,imagetime)

    # does a month folder exist with the correct name?
    if not os.path.isdir(cameraconfig.filepath + foldername):

        # nope, so make the folder
        os.makedirs(cameraconfig.filepath + foldername)
        camera_common.log.info('Created new month directory: ' + foldername)

    # does a year folder exist with that name?
    if not os.path.isdir(cameraconfig.filepath + yearfoldername):

        # nope, so make the folder
        os.makedirs(cameraconfig.filepath + yearfoldername)
        camera_common.log.info('Created new year directory: ' + yearfoldername)

    # set the image name to be the date and time
    imagename = cameraconfig.filename + time.strftime(cameraconfig.FILENAME_DATE_PATTERN, imagetime) + '.jpg'

    # copy the current image to the month folder
    os.system('cp ' + imagepath + ' ' + cameraconfig.filepath + foldername + '/' + imagename)
    camera_common.log.info('Copied image to timelapse month directory')

    imagetime = time.strftime(cameraconfig.DISPLAY_TIME_PATTERN, imagetime)
    camera_common.log.debug('Image time is ' + imagetime)

    premidday = "11:" + str(60 - cameraconfig.photointervalmin)
    postmidday = "12:" + str(cameraconfig.photointervalmin)

    # take the photo at midday and one either side of midday and place in the "year" folder
    if (imagetime == premidday or imagetime == "12:00" or imagetime == postmidday):
        os.system('cp ' + imagepath + ' ' + cameraconfig.filepath + yearfoldername + '/' + imagename)
        camera_common.log.info('Copied image to timelapse year directory')


# set up location for sunrise / sunset times
webcamloc = Location()
webcamloc.latitude = cameraconfig.cameralocationlat
webcamloc.longitude = cameraconfig.cameralocationlon
webcamloc.timezone = cameraconfig.cameratimezone

loop_number = 0

# infinite loop
while True:
          
    loop_number += 1
    camera_common.log.info('Starting loop ' +str(loop_number))

    # take the picture, loading settings from config file
    # then save - this will overwrite the current picture by default
    camera_common.log.info('Taking picture')
    os.system('fswebcam -c ' + cameraconfig.fswebcamconfig + ' ' + cameraconfig.currentimage)
    imagetime = time.localtime(os.path.getmtime(cameraconfig.currentimage))

    datetimenow = datetime.datetime.now()

    # get sunrise and sunset times 
    sun = webcamloc.sun(date=datetimenow, local=True)
    
    # only upload photos between sunrise and sunset
    if (sun['sunrise'] < pytz.timezone(cameraconfig.cameratimezone).localize(datetimenow) < sun['sunset']) :
        image = Image.open(cameraconfig.currentimage)
        width, height = image.size
    
        # add exif data to image - see exiv2.org/tags.html for options
        exif = GExiv2.Metadata(cameraconfig.currentimage)
        exif['Exif.Image.DateTime'] = time.strftime(cameraconfig.EXIF_DATE_PATTERN,imagetime)
        exif['Exif.Image.Copyright'] = 'Copyright, ' + cameraconfig.copyrightowner + ', ' + time.strftime('%Y',imagetime) + '. All rights reserved '
        exif['Exif.Photo.PixelXDimension'] = str(width)
        exif['Exif.Photo.PixelYDimension'] = str(height)
        #exif.set_gps_info(cameraconfig.cameralocationlon, cameraconfig.cameralocationlat, cameraconfig.cameralocationlat)
        exif.save_file()

        # copy image to appropriate timelapse folder
        copyimagefortimelapse(cameraconfig.currentimage, imagetime)

        # add date and time data to image
        camera_common.addwatermark(cameraconfig.currentimage, imagetime, cameraconfig.logopath)

        # upload image (after check for internet connection)
        if camera_common.connectioncheck():
        
            # scp the image to the relevant server
            # NB: prior to this working, generate key on pi (ssh-keygen), then copy it to ftphost
            # into ~/.ssh/authorized_keys so that no password is necessary
            camera_common.log.info('Uploading file')
            cmd = os.popen('scp ' + cameraconfig.filepath + 'latest/' + cameraconfig.filename + '.jpg ' + cameraconfig.ftpuser + '@' + cameraconfig.ftphost + ':' + cameraconfig.ftpfolder)
            cmd.read()

        # get the current time, and work out how long until it's either a multiple of "photointervalmin" minutes past hour
        now = time.localtime()
        nowminute = now.tm_min
        nowsecond = now.tm_sec

        # wait until it's "photointerval" minutes past the hour
        # done this way rather than sleeping for a set number of seconds, to avoid time creep
        if nowminute % cameraconfig.photointervalmin == 0:
            nextphotoin = (cameraconfig.photointervalmin * 60) - nowsecond
        else:
            nextphotoin = ((cameraconfig.photointervalmin - (nowminute % cameraconfig.photointervalmin))*60) - nowsecond 
    else:
        if (pytz.timezone(cameraconfig.cameratimezone).localize(datetimenow) > sun['sunset']) :

            camera_common.log.info('Image deemed after sunset: moving to processing phase')

            # work out the date of starting the processing
            processingstartdate = datetime.date.today()        
            tomorrowdate = processingstartdate + datetime.timedelta(days=1)

            #camera_common.log.debug('Processing start date is ' + str(processingstartdate) + ' so tomorrow\'s date is ' + str(tomorrowdate))
            camera_common.log.debug('Tomorrow will be day number ' + str(tomorrowdate.day) + ' of the month')           

            # Calculate how long until tomorrow's sunrise in seconds 
            tomorrowsun = webcamloc.sun(date=tomorrowdate, local=True)
            camera_common.log.info('Tomorrow sunrise: ' + str(tomorrowsun['sunrise']))
            nextphotoindelta = tomorrowsun['sunrise'] - pytz.timezone(cameraconfig.cameratimezone).localize(datetime.datetime.now())
            nextphotoin = nextphotoindelta.total_seconds()
	
        else:
            camera_common.log.info('Image deemed before sunrise: waiting until sunrise')
            camera_common.log.info('Today sunrise: ' + str(sun['sunrise']))
            nextphotoindelta = sun['sunrise'] - pytz.timezone(cameraconfig.cameratimezone).localize(datetime.datetime.now())
            nextphotoin = nextphotoindelta.total_seconds()

        # Add fifteen minutes, just to be on the safe side light-wise
        nextphotoin = nextphotoin + (15*60)

        # if processing over-runs for any reason, "nextphotoin" could be negative, so set to take photo immediately
        if nextphotoin <= 0:
            nextphotoin = 0
        
        camera_common.log.info('Sunrise will be in ' + str(nextphotoin - (15*60)) + ' seconds')
       
    # now sleep my little one 
    camera_common.log.info('Waiting for ' + str(nextphotoin) + ' seconds until next photo')
    time.sleep(nextphotoin)  

