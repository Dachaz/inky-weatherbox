import socket
import requests
import calendar
import datetime

class NewRelic:
    logging = {}

    api_key = ""
    metrics_url = ""
    logs_url = ""
    hostname = ""
    appname = ""

    def __init__(self, logging, api_key, metrics_url, logs_url, appname):
        self.logging = logging
        self.api_key = api_key
        self.metrics_url = metrics_url
        self.logs_url = logs_url
        self.appname = appname

        self.hostname = socket.gethostname()

    def get_headers(self):
        return { "Api-Key": self.api_key }

    def post_metric(self, batt):
        date = datetime.datetime.utcnow()
        utc_time = calendar.timegm(date.utctimetuple())

        obj = [{
                "metrics":[{
                    "name": "battery.charge_level",
                    "type": "gauge",
                    "value": batt,
                    "timestamp": utc_time,
                    "attributes": {
                        "host.name": self.hostname,
                        "app.name": self.appname
                    }
                }]
            }]

        try:
            requests.post(self.metrics_url, headers=self.get_headers(), json=obj)
        except Exception as e:
            self.logging.error("Couldn't post metric to NewRelic: %s" % e)

    def log(self, message, batt):
        obj = { "batt": batt, "message": message, "host.name": self.hostname, "app.name": self.appname }

        try:
            self.logging.info(message)
            requests.post(self.logs_url, headers=self.get_headers(), json=obj)
        except Exception as e:
            self.logging.error("Couldn't post the log to NewRelic: %s" % e)
