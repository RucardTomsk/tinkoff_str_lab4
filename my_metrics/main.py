from http.server import HTTPServer
import prometheus_client
from prometheus_client import Counter, start_http_server
import logging
import requests
import yaml
import json
import time
from time import sleep
from threading import Thread
import datetime

logging.basicConfig(level=logging.INFO, filename="service_log.log", filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()

prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

class prometheus(object):
    def __init__(self, config):
        try:
            port = int(config["prometheus"]['server_port'])
        except (ValueError, KeyError):
            logger.error('prometheus server_port not present in config.')
            return

        self.counters = {}

        logger.info('Starting prometheus metrics web server at %s', port)
        start_http_server(port)

    def send_metrics(self, metric):
        if metric not in self.counters:
            self.counters[metric] = Counter(metric, '')
        logger.info('Setting metrics counter %s', metric)
        self.counters[metric].inc()


class oncall_api(object):
    def __init__(self, config):
        self.url = f"{config['oncall_api']['base_url']}"
        self.session = requests.Session()
        self.__login(username=config['oncall_api']['username'], password=config['oncall_api']['password'])

    def __login(self, username, password=123):
        try:
            response = self.session.post(f"{self.url}/login", data={
                'username': username,
                'password': password
            })
        except requests.exceptions.ConnectionError:
            logger.error(f"API: Failed connection {config['oncall_api']['base_url']}")


        if response.status_code == 200:
            self.csrf_token = response.json()['csrf_token']
        else:
            logger.warning(f"API: Failed authorisation attempt.[{response.status_code}] {response.json()}")

    def get(self, request_path, query_params={}):
        response = self.session.get(f"{self.url}{request_path}", params=query_params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"API: Failed get request.[{response.status_code}] {response.json()}")
            return None

def date_to_unixtime(date):
    return time.mktime(date.timetuple())

def metric1(_prometheus: prometheus, api: oncall_api):
    while True:
        name_metric = "number_of_off_duty_hours"
        teams = api.get("/api/v0/teams")
        if teams is None:
            continue

        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        for team in teams:
            events = api.get("/api/v0/events", query_params={
                'team': team,
                'start__ge': date_to_unixtime(today),
                'start__lt': date_to_unixtime(tomorrow),
                'end__ge': date_to_unixtime(tomorrow),
            })
            if events is None:
                continue

            if len(events) == 0:
                _prometheus.send_metrics(name_metric)

        sleep(2)



with open('config.yml') as fh:
    config = yaml.load(fh, Loader=yaml.FullLoader)
    fh.close()

if __name__ == "__main__":
    api = oncall_api(config)
    prom = prometheus(config)
    m1 = Thread(target=metric1, args=(prom, api,))
    m1.start()


