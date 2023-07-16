#!/usr/bin/python3
import logging

# constants
EXIF_DATE_PATTERN = '%Y:%m:%d %H:%M:%S'
DISPLAY_DATE_PATTERN = '%d %b'
DISPLAY_TIME_PATTERN = '%H:%M'
FOLDER_DATE_PATTERN = '%Y%m'
YEAR_FOLDER_DATE_PATTERN = '%Y'
FILENAME_DATE_PATTERN = '%Y%m%d-%H%M'
TEST_URL = 'www.google.co.uk'

# logging
loglevel = logging.DEBUG

# copyright owner of images generated
copyrightowner = ''

# photo interval - this should be a factor of 60
photointervalmin = 15

# locale information (lat + long to 6 decimal places, alt is altitude)
cameralocationlat = 0.000000
cameralocationlon = 0.000000
cameralocationalt = 62
cameratimezone = 'Europe/London'

# local file and folder paths
fswebcamconfig = '/home/pi/fswebcam.conf'
filename = 'garden'
filepath = '/home/pi/Pictures/'
currentimage = filepath + 'latest/' + filename + '.jpg'
fontspath = '/usr/share/fonts/truetype/'
logopath = '/home/pi/logo.png'

# upload details (set these to be your ftp location.  Folder should be in the format <host>/<directory>)
ftphost = ''
ftpuser = ''
ftpfolder = ''
