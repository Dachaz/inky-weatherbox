#!/usr/bin/python3

import configparser
import logging
import os
import weather

from time import sleep
from pijuice import PiJuice
from newrelic import NewRelic

config = configparser.ConfigParser()
config.read( os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), "config.ini")) )

logging.basicConfig(
	filename = config["DEFAULT"]["LogFile"],
	level = logging.INFO,
	format = '%(asctime)s %(message)s',
	datefmt = '%d/%m/%Y %H:%M:%S')

pj = PiJuice(1,0x14)

pjOK = False
while pjOK == False:
   stat = pj.status.GetStatus()
   if stat['error'] == 'NO_ERROR':
      pjOK = True
   else:
      sleep(0.1)

data = stat['data']
stat = pj.status.GetChargeLevel()
batt = stat['data']

# Post a metric and a log to NewRelic
nr = NewRelic(
    logging = logging,
    api_key = config["NewRelic"]["ApiKey"],
    metrics_url = config["NewRelic"]["MetricsUrl"],
    logs_url = config["NewRelic"]["LogsUrl"],
    appname = config["DEFAULT"]["AppName"])

# Post the battery status to New Relic
nr.post_metric(batt)

# Get the weather and update inky phat
try:
   weather.main(
      lattitude = config["Weather"]["Lattitude"],
      longitude = config["Weather"]["Longitude"],
      temperature_unit = config["Weather"]["TempUnit"],
      windspeed_unit = config["Weather"]["WindUnit"],
   )
except Exception as e:
   logging.error("Couldn't get the weather: %s" % e)

# If on mains power, just write statement to log
if data['powerInput'] != "NOT_PRESENT" or data['powerInput5vIo'] != 'NOT_PRESENT':
   nr.log(message='Raspberry Pi on mains power, not turned off automatically', batt=batt)

# If on battery power, shut down
else:
   nr.log(message='Raspberry Pi on battery power (%d). Turning off.' % batt, batt=batt)

   # Make sure wakeup_enabled and wakeup_on_charge have the correct values
   pj.rtcAlarm.SetWakeupEnabled(True)
   pj.power.SetWakeUpOnCharge(0)

   # Handle quiet time for the alarm
   time = pj.rtcAlarm.GetTime()
   alarmTime = 'EVERY_HOUR'
   if int(time['data']['hour']) == int(config['Schedule']['QuietTimeFrom']):
      alarmTime = config['Schedule']['QuietTimeTo']
   pj.rtcAlarm.SetAlarm({'second': 0, 'minute': 2, 'hour': alarmTime, 'day': 'EVERY_DAY'})

   # Make sure power to the Raspberry Pi is stopped to not deplete the battery
   pj.power.SetSystemPowerSwitch(0)
   pj.power.SetPowerOff(30)

   # Now turn off the system
   os.system("sudo shutdown -h now")
