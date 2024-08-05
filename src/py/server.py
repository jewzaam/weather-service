import argparse
import json
import yaml
import httpimport

import openweathermap
import weathergov

from flask import Flask
from flask import request
from flask import Response
from prometheus_flask_exporter import PrometheusMetrics

import utility

app = Flask(__name__)

# global config, loaded in __main__
config = {}
sources = {}

@app.route("/")
def help():
    return f"see http://github.com/jewzaam/weather-service for help"

@app.route("/forecast/<latitude>/<longitude>")
def forecast(latitude, longitude):
    source = request.args.get('source')
    code=200
    try:
        if source not in sources:
            code=400
            return "Invalid source", code
        forecast = sources[source].get_forecast(latitude, longitude, request.args)
        return Response(json.dumps(forecast), mimetype='text/json'), code
    except ValueError as ve:
        code=400
        return ve.args[0], code
    finally:
        # note including "source" could explode metrics if some bad actor tries a lot of random strings
        # therefore source is not included on this metric
        utility.inc("weatherService_forecast_response", {"code": code})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Service to get weather data from various sources.")
    parser.add_argument("--config", type=str, help="configuraiton file", default="config.yaml")

    args = parser.parse_args()

    # load config file
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # setup sources
    for source in config["sources"]:
        if source == "openweathermap":
            sources[source] = openweathermap.OpenWeatherMap()
        elif source == "weathergov":
            sources[source] = weathergov.WeatherGov()

    # Start up the server to expose the metrics.
    utility.metrics(config["metrics"]["port"])

    # start http server to listen for requests
    app.run(host=config["service"]["host"], port=config["service"]["port"])

