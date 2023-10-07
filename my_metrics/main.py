from http.server import HTTPServer
from prometheus_client import Gauge, MetricsHandler
import logging
import requests
import yaml
import json

logger = logging.getLogger()


class prometheus(object):
    def __init__(self, config):
        try:
            port = int(config["prometheus"]['server_port'])
        except (ValueError, KeyError):
            logger.error('prometheus server_port not present in config.')
            return

        self.gauges = {}

        logger.info('Starting prometheus metrics web server at %s', port)
        HTTPServer(("0.0.0.0", port), MetricsHandler).serve_forever()

    def send_metrics(self, metrics):
        for metric, value in metrics.items():
            if metric not in self.gauges:
                self.gauges[metric] = Gauge(metric, '')
            logger.info('Setting metrics gauge %s to %s', metric, value)
            self.gauges[metric].set_to_current_time()
            self.gauges[metric].set(value)


class oncall_api(object):
    def __init__(self, config):
        self.url = f"{config['oncall_api']['base_url']}"
        self.session = requests.Session()
        self.__login(username=config['oncall_api']['username'], password=config['oncall_api']['password'])

    def __login(self,username, password = 123):
        response = self.session.post(f"{self.url}/login", data={
            'username': username,
            'password': password
        })

        if response.status_code == 200:
            self.csrf_token = response.json()['csrf_token']
        else:
            logger.warning("API: Failed authorisation attempt")


with open('config.yml') as fh:
    config = yaml.load(fh, Loader=yaml.FullLoader)
    fh.close()

api = oncall_api(config)
