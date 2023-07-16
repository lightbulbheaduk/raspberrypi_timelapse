#!/usr/bin/python3
import logging
import os
import shutil
import sys
import time
from PIL import Image, ImageDraw, ImageFont, ImageStat
from systemd.journal import JournalHandler

import cameraconfig
import camera_common

def calculatergb(imagefile):
    # return rgb
    image = Image.open(imagefile)
    stat = ImageStat.Stat(image)
    return stat.mean #r, g, b tuple

def normalisetimelapseimagesrgb(foldername):
    # based loosely in stackoverflow.com/questions/7116113 (second solution)

    imagefolder = cameraconfig.filepath + foldername
    
    # create a list of images in the folder (path to start with)
    folderimages = next(os.walk(imagefolder))[2]

    camera_common.log.info('Analysing ' + str(len(folderimages)) + ' images in ' + imagefolder)

    # iterate over the image list and add average rgb for each image to each element
    imagesrgb = []
    totalrgb = [0,0,0]
    for folderimage in sorted(folderimages):
        r,g,b = calculatergb(imagefolder + '/' + folderimage)
        imagesrgb.append([folderimage, r, g, b])
        totalrgb[0] += r
        totalrgb[1] += g
        totalrgb[2] += b

    # get average rgb values of all images in list
    averager = totalrgb[0]/len(imagesrgb)
    averageg = totalrgb[1]/len(imagesrgb)
    averageb = totalrgb[2]/len(imagesrgb)

    # iterate over the image list and add delta to each element
    imagesrgbanddelta = []
    for imagergb in sorted(imagesrgb):
        imagesrgbanddelta.append([imagergb[0], imagergb[1], averager - imagergb[1], imagergb[2], averageb - imagergb[2], imagergb[3], averageg - imagergb[3]])
    
    timelapseimage = 1
    
    # iterate over the image list and create a normalised copy of each image
    for originalimage in sorted(imagesrgbanddelta):

        camera_common.log.info('Converting image ' + str(originalimage[0]) + ', (' + str(timelapseimage) + '/' + str(len(folderimages)) + ')')
        
        # open and convert to RGB
        workingfile = Image.open(imagefolder + '/' + originalimage[0])        
        workingfile = workingfile.convert('RGB')

        # create an image map (2D array) of all pixels in the file
        imagemap = workingfile.load()

        # iterate over each pixel in turn
        for i in range(workingfile.size[0]):
            for j in range(workingfile.size[1]):

                # get the rgb values for the pixel (extra brackets needed as this is a tuple)
                r,g,b = workingfile.getpixel((i,j))

                # set the pixel values for the new image, adjusted based on the delta
                imagemap[i,j] = (r+int(originalimage[2]), g+int(originalimage[4]), b+int(originalimage[6]))

        # make a timelapse folder and save the updated image
        if not os.path.isdir(imagefolder + '/timelapse'):
            os.makedirs(imagefolder + '/timelapse')
        
        # save as incrementingly numbered (yes, that is a term!), to aid with avconv timelapse creation
        workingfile.save(imagefolder + '/timelapse/' + cameraconfig.filename + str(timelapseimage).zfill(5) + '.jpg')

        # add the watermark to the updated image (getting image time from original image, not timelapse image)      
        imagetime = time.localtime(os.path.getmtime(imagefolder + '/' + originalimage[0]))
        camera_common.addwatermark(imagefolder + '/timelapse/' + cameraconfig.filename + str(timelapseimage).zfill(5) + '.jpg', imagetime, cameraconfig.logopath)

        # increment the timelapse image number
        timelapseimage +=1
        
def createtimelapse(foldername):
    # make the timelapse
    os.system('avconv -y -r 20 -i ' + cameraconfig.filepath + foldername + '/timelapse/' + cameraconfig.filename + '%05d.jpg -r 20 -vcodec libx264 -crf 20 -g 15 Videos/' + cameraconfig.filename + foldername + '.mp4')

    camera_common.log.info('Timelapse created of folder: ' + foldername)


def uploadtimelapse(foldername):
    # upload the timelapse (after check for internet connection)
    if camera_common.connectioncheck():
        
        # scp the timelapse to the relevant server
        # NB: prior to this working, generate key on pi (ssh-keygen), then copy it to ftphost
        # into ~/.ssh/authorized_keys so that no password is necessary
        camera_common.log.info('Uploading timelapse generated from folder:' + foldername)
        cmd = os.popen('scp Videos/' + cameraconfig.filename + foldername + '.mp4 ' + cameraconfig.ftpuser + '@' + cameraconfig.ftphost + ':' + cameraconfig.ftpfolder)
        cmd.read()

# get the foldername from the command line arguments (first arg is script name, second is first proper arg)
foldername = sys.argv[1]

camera_common.log.info("Foldername is " + foldername)

# normalise the white balance of the images (to minimise flickering in the timelapse)
normalisetimelapseimagesrgb(foldername)

camera_common.log.info('Images processed and prepared for timelapse')

# create timelapse
createtimelapse(foldername)

# upload timelapse
uploadtimelapse(foldername)
            
# I know this is dangerous, but we don't want to run out of space on the Pi,
# so once we've uploaded the timelapse for the folder, delete the folder.
# However, check for presence of a timelapse with the foldername in the Videos
# folder first.
#if os.path.isfile('Videos/' + cameraconfig.filename + foldername + '.mp4'):
#    camera_common.log.info("Found video, therefore deleting folder: " + foldername)
#    shutil.rmtree(cameraconfig.filepath + foldername)
#else:
#    camera_common.log.warning("Timelapse generation failed - not deleting folder: " + foldername)
