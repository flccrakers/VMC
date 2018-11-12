#!/usr/bin/env python3

import logging
import logging.handlers
import argparse
import sys
from time import sleep
import Adafruit_DHT
import RPi.GPIO as GPIO
from time import time

# Defaults
LOG_FILENAME = "/tmp/vmc.log"
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="Check for humidity and activate the extraction fan is too hight")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
    LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)


# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        """Needs a logger and a logger level."""
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())


# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

i = 0

# ###################################################################
# GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

# creation d'un objet PWM. canal=17 frequence=50Hz
FAN = GPIO.PWM(21, 50)

FAN.start(0)
# Sensor should be set to Adafruit_DHT.DHT11,
# Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
sensor = Adafruit_DHT.DHT11

# Example using a Beaglebone Black with DHT sensor
# connected to pin P8_11.
pin = '4'


def time_left_above_zero(start, time_vent):
    if start + time_vent - time() >= 0:
        return False
    else:
        return True


wait_time_seconds = 1
time_to_vent = 5  # time to put the fan on : 60 sec
start_vent_date = 1000
slow_duty = 30
high_duty = 100
duty = slow_duty
humidity = None
temperature = None

# Loop forever, doing something useful hopefully:
while True:
    if time_left_above_zero(start_vent_date, time_to_vent):
        humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    if humidity is not None:
        if humidity <= 65:
            duty = 0
            FAN.ChangeDutyCycle(duty)
            start_vent_date = 1000
        elif 65 < humidity < 75:
            logger.info('65% to 75% =>Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            if not duty == slow_duty:
                duty = slow_duty
                FAN.ChangeDutyCycle(duty)
            if time_left_above_zero(start_vent_date, time_to_vent):
                start_vent_date = time()
        elif 75 < humidity:
            logger.info('Above 75% =>Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            if not duty == high_duty:
                duty = high_duty
                FAN.ChangeDutyCycle(duty)
            if time_left_above_zero(start_vent_date, time_to_vent):
                start_vent_date = time()
        else:
            logger.debug('Failed to get reading. I\' Try again in ' + str(wait_time_seconds) + ' seconds')
    sleep(wait_time_seconds)

