#!/usr/bin/python3

import logging
import logging.handlers
import argparse
import sys
from time import sleep
import Adafruit_DHT
import RPi.GPIO as GPIO

# Defaults
LOG_FILENAME = "/tmp/vmc.log"
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="Check for humidity and activate the extraction fan is too hight")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")
parser.add_argument("-hu", "--humidity", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
HUMIDITY = None
args = parser.parse_args()
print(args)
if args.log:
    LOG_FILENAME = args.log
if args.humidity:
    HUMIDITY = int(args.humidity)

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
# sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
# sys.stderr = MyLogger(logger, logging.ERROR)

# ###################################################################
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

# creation d'un objet PWM. canal=4 frequence=50Hz
LED = GPIO.PWM(21, 20)

LED.start(0)
# Sensor should be set to Adafruit_DHT.DHT11,
# Adafruit_DHT.DHT22, or Adafruit_DHT.AM2302.
sensor = Adafruit_DHT.DHT11

# Example using a Beaglebone Black with DHT sensor
# connected to pin P8_11.
pin = '4'

# Example using a Raspberry Pi with DHT sensor
# connected to GPIO23.
# pin = 23
wait_time_seconds = 1

# Loop forever, doing something useful hopefully:
while True:
    # Try to grab a sensor reading.  Use the read_retry method which will retry up
    # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    # Note that sometimes you won't get a reading and
    # the results will be null (because Linux can't
    # guarantee the timing of calls to read the sensor).
    # If this happens try again!

    print('HUMIDITY: ' + str(HUMIDITY))
    if HUMIDITY is not None:
        humidity = HUMIDITY
    print("humidity: " + str(humidity))
    if humidity is not None:
        # print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
        if humidity <= 55:
            LED.stop()
            wait_time_seconds = 1
        elif 55 < humidity < 70:
            logger.info('Below 70% =>Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            LED.start(1)
            LED.ChangeDutyCycle(30)
            wait_time_seconds = 1
        elif 71 < humidity:
            logger.info('Up 70% =>Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            LED.ChangeDutyCycle(100)
            wait_time_seconds = 1
    else:
        logger.debug('Failed to get reading. I\' Try again in ' + str(wait_time_seconds) + 'seconds')
    sleep(wait_time_seconds)
GPIO.cleanup()