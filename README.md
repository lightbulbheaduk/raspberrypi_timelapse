# raspberrypi_timelapse

A little project from a few years ago that in daylight hours takes a photo every x minutes and uploads it to an online location, then once a month during night hours, creates a timelapse of the images from that month and uploads that to an online location via SCP

To avoid the need for a password, prior to setting this to run, generate an SSH key on pi (using the ssh-keygen command), then copy it to ftphost into ~/.ssh/authorized_keys
