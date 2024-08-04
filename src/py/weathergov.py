import requests
import datetime

import utility
import weather

API_BASE="https://api.weather.gov"

class WeatherGov(weather.Weather):
    def __init__(self):
        self.set_source("weather.gov")

    def get_required_paramters(self):
        return []

    def get_forecast_implementation(self, latitude, longitude, parameters={}):
        # note parameters are not used at this time
        request_url_points = f"{API_BASE}/points/{latitude},{longitude}"

        output = {
            "metadata": {
                "source": self.get_source(),
                "request_urls": [
                    request_url_points,
                ],
                "coordinates": [latitude,longitude],
            },
            "data": {},
            "status": {
                "success": "true",
                "requested": str(datetime.datetime.now()),
            },
        }

        # get the grid location
        response = requests.get(request_url_points)

        if response.status_code != 200:
            output["status"]["success"] = "false"
            output["status"]["http_response_code"] = response.status_code
            output["status"]["http_request_url"] = request_url_points
            output["status"]["responded"] = str(datetime.datetime.now())
            print(response.content)
            return output

        # using raw forecast
        forecast_grid_data = response.json()["properties"]["forecastGridData"]
        output["metadata"]["request_urls"].append(forecast_grid_data)
        response = requests.get(forecast_grid_data)

        if response.status_code != 200:
            output["status"]["success"] = "false"
            output["status"]["http_response_code"] = response.status_code
            output["status"]["http_request_url"] = forecast_grid_data
            output["status"]["responded"] = str(datetime.datetime.now())
            print(response.content)
            return output
        else:
            data = response.json()

            # walk the properties I care about
            for key in data["properties"]:
                if key not in [
                    "temperature",
                    "apparentTemperature",
                    "dewpoint",
                    "relativeHumidity",
                    "skyCover",
                    "windDirection",
                    "windSpeed",
                    "windGust",
                    "probabilityOfPrecipitation",
                    "quantitativePrecipitation",
                    "pressure",
                    "visibility",
                    "weather", # special handling
                ]:
                    # it isn't one I care about
                    continue
            
                if "values" not in data["properties"][key]:
                    # there is no data, skip
                    continue

                uom=""
                if "uom" in data["properties"][key]:
                    uom=data["properties"][key]["uom"].split(":")[1]
                    if uom == "degree_(angle)":
                        uom="degrees"
                    elif uom == "km_h-1":
                        uom="kph"
                    elif uom == "degC":
                        uom="celsius"
                
                for v in data["properties"][key]["values"]:
                    # always has 'validTime' and 'value'
                    # data for value is usually float, but for key="weather" it is an object
                    _validTime, _duration=v["validTime"].split("/")
                    value=v["value"]

                    # convert pressure to millibars, it comes as Hg
                    if key == "pressure":
                        uom="millibars"
                        value=self.convert_Hg_to_millibars(value)

                    # convert to date
                    validTime=datetime.datetime.strptime(_validTime, "%Y-%m-%dT%H:%M:%S%z")

                    # convert duration (hours)
                    d_uom=_duration[-1]
                    duration_h=int(_duration[2:-1])
                    if d_uom == "D":
                        # convert "day" to "hour" duration
                        duration_h=duration_h*24

                    for i in range(0, duration_h):
                        o_key=self.output_date(validTime, i)
                        if o_key not in output["data"]:
                            output["data"][o_key] = {}
                        if key != "weather":
                            output["data"][o_key][key]={
                                "value": value,
                                "uom": self.normalized_uom(uom),
                            }
                        else:
                            w_value=""
                            # value is an array in the case of "weather"
                            for v in value:
                                if w_value != "":
                                    w_value+="and "
                                if "coverage" in v and v["coverage"] is not None:
                                    w_value+=v["coverage"]+" "
                                if "intensity" in v and v["intensity"] is not None:
                                    w_value+=v["intensity"]+" "
                                if "weather" in v and v["weather"] is not None:
                                    w_value+=v["weather"]+" "

                            w_value = w_value.replace("_", " ")
                            output["data"][o_key][key]={
                                "value": w_value.strip()
                            }
            
            output["status"]["responded"] = str(datetime.datetime.now())
            return output