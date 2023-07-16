#!/usr/bin/python3

import os
import math
import string
import time
import datetime
import pytz
from gi.repository import GExiv2
from astral import Astral, Location
from systemd.journal import JournalHandler
from PIL import Image, ImageDraw, ImageFont, ImageStat
import socket
import logging
import sys

import cameraconfig

# define our functions
def connectioncheck():
    try:
        # try to create a connection to a test URL
        host = socket.gethostbyname(cameraconfig.TEST_URL)
        s = socket.create_connection((host, 80), 2)
        log.debug('Connection found')
        return True
    except Exception as e:
        # no connection - leave it to script logic to decide what to do
        log.error('No connection:' + str(e))
        return False

def addwatermark(imageforwatermark, imagetime, logoimage):
    # open current image and get dimensions
    image = Image.open(imageforwatermark)
    width, height = image.size

    # create a canvas, create text and work out size in the specified font
    draw = ImageDraw.Draw(image)
    watermarkdate = time.strftime(cameraconfig.DISPLAY_DATE_PATTERN,imagetime)
    watermarktime = time.strftime(cameraconfig.DISPLAY_TIME_PATTERN,imagetime)
    datefont = ImageFont.truetype(cameraconfig.fontspath + 'droid/DroidSerif-Regular.ttf', 33)
    timefont = ImageFont.truetype(cameraconfig.fontspath + 'droid/DroidSerif-Regular.ttf', 45)
    datewidth, dateheight = draw.textsize(watermarkdate, datefont)
    timewidth, timeheight = draw.textsize(watermarktime, timefont)
    margin=25

    # work out positioning of text and place text there with specified font
    xtimepos = width - timewidth - margin
    ytimepos = height - timeheight - margin
    xdatepos = xtimepos
    ydatepos = height - dateheight - timeheight - (margin / 1.5)
    draw.text((xtimepos,ytimepos), watermarktime, font=timefont)
    draw.text((xdatepos,ydatepos), watermarkdate, font=datefont)

    #draw.line((xdatepos - (margin / 1.5), ydatepos + (margin / 2), xdatepos - (margin / 1.5), ytimepos + timeheight), width=2)

    # work out positioning of logo and paste it on
    #logo = Image.open(logoimage)
    #logowidth, logoheight = logo.size
    #xlogopos = xdatepos - logowidth - (2*margin)
    #ylogopos = height - logoheight - margin
    #image.paste(logo, (xlogopos, ylogopos), logo)

    # save the image
    image.save(imageforwatermark)

# set up logging
log = logging.getLogger('camera_script')
log_fmt = logging.Formatter('%(levelname)s %(message)s')
log_ch = JournalHandler()
log_ch.setFormatter(log_fmt)
log.addHandler(log_ch)
log.setLevel(cameraconfig.loglevel)
