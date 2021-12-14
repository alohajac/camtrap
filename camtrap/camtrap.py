# camtrap v1.2

# Camtrap is a controller for a raspberry pi camera trap.  The code operates 
# raspberry pi hardware (a raspberry pi 3b, a camera, and a IR motions sensor). 
# The code includes modes to collect still photos, time-lapse photos, or video 
# of wildlife and natural phenomena.  It also includes a mode for optimizing 
# white balance.

# This code was written by Jack Lawrence in December 2021.

from picamera import PiCamera
from gpiozero import MotionSensor
import time
import datetime as dt
import sys

# Start timer.  In the still photo and video capture modes, the user can set 
# the time to stop operating. 
dtEnd = dt.datetime(2021, 12, 8, 20, 0, 0)      # Set ending datetime
dtNow = dt.datetime.now()                       # Check current datetime
dtStart = dtNow                                 # Record start time
dtComp = (dtEnd - dtNow).seconds                # Compare end and current times

print('Standby')                    # Since the code takes a few moments to 
                                    # run through camera setup before it can 
                                    # start taking pictures, this print command 
                                    # lets the user know that the code is
                                    # running and the delay is normal.

# Confirm end time is after the start time.  If using the timer, this section 
# will make sure the ending time has been set to a time after the start time.
dtCheck = (dtEnd - dtNow).days
if dtCheck < 0:
    sys.exit('End time is before start time.')

# Set delayed start.  This allows the user to delay the start of operation.
# time.sleep(0)                          # Seconds to hold before starting

# Set camera mode.  Only one mode can be active at a time.
still = 1                                # toggle mode for still photos
video = 0                                # toggle mode for taking video
timeLapse = 0                            # toggle mode for taking time-lapse
wbTest = 0                               # toggle mode for setting white balance

# Input values to be used later to set hardware parameters.

# Camera parameters
iso = 100                                # set iso (photos & timeLapse)
framerate = 42                           # set framerate (video; depends on camera resolution)
wb = [1.0, 1.4]                          # set white balance
                                         #   dining room old cam = [1.0, 1.4]
                                         #   dining room new cam = [1.3, 1.4]
                                         #   dining room video new cam = [1.0, 1.4]
resolutionPhoto = [2592, 1944]
resolutionVideo = [1296, 972]            # [640, 480] supports up to 60fps
                                         # [1296, 972] supports up to 42fps
                                         # See picamera documentation for more information
interval = 5                             # seconds between timeLapse photos
stopLapse = 60*30                        # stop timeLapse after this many seconds
vidDur = 10                              # video recording duration (seconds)
camAngle = 0                             # compensate for camera deployment angle

# Motion sensor parameters
qLen = 5                                 # queue length, I've used 3-5
sRate = 10                               # sample rate (per second)
thr = 0.5                                # threashold for 'active'

# Confirm only one mode has been selected.
modeSum = still + video + timeLapse + wbTest
if modeSum != 1:
    sys.exit('Only one mode can be selected at a time.')

# Create python objects for the motion sensor and camera.
pir = MotionSensor(4, queue_len=qLen, sample_rate=sRate, threshold=thr)
camera = PiCamera()

# Set mode-specific camera parameters.
if still == 1:
    camera.resolution = resolutionPhoto
    camera.iso = iso

if video == 1:
    camera.resolution = resolutionVideo
    camera.framerate = framerate

if timeLapse == 1:
    camera.resolution = resolutionPhoto
    camera.iso = iso

if wbTest == 1:
    camera.resolution = resolutionPhoto
    camera.iso = iso

# Start camera.  Some parameters can be set only after the camera is active.
camera.start_preview()

# Wait for the automatic gain control to settle.
time.sleep(5)

# Set camera parameters.
camera.shutter_speed = camera.exposure_speed
camera.exposure_mode = 'off'
camera.awb_mode = 'off'
camera.awb_gains = wb
camera.rotation = camAngle

# Initialize a counter.  The code will save separate image files under filenames
# distinguished by the counter number.
i = 0

# Define a module to take a still photo.  Time-lapse mode also uses this module.
def take_still():
    global i

    for j in range(1,2):
        i += 1
        camera.capture('/home/pi/pics/pics/photo_%s.jpg' % i)
        print('Photo taken at %s.' % dtNow)
#        time.sleep(0.5)

# Define a module to record a video.
def take_video():
    global i

    for j in range(1,2):
        i += 1
        camera.start_recording('/home/pi/pics/vids/video_%s.h264' % i)
        print('Video recording started at %s.' % dtNow)
        camera.wait_recording(vidDur)
        camera.stop_recording()
        print('Video recording complete')
#        time.sleep(0.5)

# Define a module to generate a series of pictures to determine best
# white balance and/or color
def test_for_white_balance():
    c = 0
    red_range = range(5, 15)
    blue_range = range (5, 15)
    lenR = len(red_range)
    lenB = len(blue_range)
    for r in red_range:
        for b in blue_range:
            c += 1
            print((lenR*lenB)-c)
            camera.awb_gains = (r/10, b/10)
            rb = str(r) + str(b)
            camera.capture('/home/pi/pics/test/test_%s.jpg' % rb)

# Start cameratrap execution loops

print('Ready')          # This command lets the user know that the setup 
                        # delay is over and the camera trap is now operating.

# Motion Sensor-enabled still photo capture loop.
if still == 1:
    while dtComp > 10:                      # Checks for timer ending condition.
        pir.when_motion = take_still
#        pir.when_no_motion = None
        dtNow = dt.datetime.now()
        dtComp = (dtEnd - dtNow).seconds    # Increments the timer.

# Motion sensor-enabled video capture loop.
if video == 1:
    while dtComp > 10:                      # Checks for timer ending condition.
        pir.when_motion = take_video
#        pir.when_no_motion = None
        dtNow = dt.datetime.now()
        dtComp = (dtEnd - dtNow).seconds    # Increments the timer.

# Time-lapse photograph capture loop (not motion-sensor enabled).
if timeLapse == 1:

    for n in range(0,stopLapse):            # Checks the stop condition.
        dtNow = dt.datetime.now()
        dtComp = (dtEnd - dtNow).seconds

        if n%interval == 0: 
            tl = take_still()

        print('n=', n)
        time.sleep(1)

# Run a picture series to determine best white balance and/or color
if  wbTest == 1:
    print('Starting photography for white balance test.')
    print('Standby.')
    p = test_for_white_balance()
    print('Finished photography for white balance test.')

# Record final time after quit
dtFinish = dtNow
camera.close()
