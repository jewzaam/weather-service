import requests
import datetime

import weather

class OpenWeatherMap(weather.Weather):
    def __init__(self):
        self.set_source("openweathermap.org")

    def get_required_paramters(self):
        return [
            "apikey",
        ]

    def get_forecast_implementation(self, latitude, longitude, parameters):
        # already have validated in parent class that required params are included, blindly use them
        apikey = parameters["apikey"]

        request_url_onecall = f"https://api.openweathermap.org/data/3.0/onecall?appid={apikey}&lat={latitude}&lon={longitude}&exclude=minutely,daily,current&units=metric"

        output = {
            "metadata": {
                "source": self.get_source(),
                "request_urls": [
                    request_url_onecall,
                ],
                "coordinates": [latitude, longitude],
            },
            "data": {},
            "status": {
                "success": "true",
                "requested": str(datetime.datetime.now()),
            },
        }

        # get the data
        response = requests.get(request_url_onecall)

        if response.status_code != 200:
            output["status"]["success"] = "false"
            output["status"]["http_response_code"] = response.status_code
            output["status"]["http_request_url"] = request_url_onecall
            output["status"]["responded"] = str(datetime.datetime.now())
            return output
        else:
            hourly = response.json()["hourly"]

            for data in hourly:
                # output for each timestamp will include the following
                #   temperature
                #   apparentTemperature
                #   dewpoint
                #   relativeHumidity
                #   skyCover
                #   windDirection
                #   windSpeed
                #   windGust
                #   probabilityOfPrecipitation
                #   quantitativePrecipitation
                #   pressure
                #   visibility
                #   weather

                # the key for output is the date
                validTime=datetime.datetime.fromtimestamp(data["dt"], datetime.timezone.utc)

                # and that date as the key in object must be consistent
                o_key=self.output_date(validTime, 0)
                output["data"][o_key] = {
                    "dt": data["dt"],
                }

                if "temp" in data and data["temp"] is not None:
                    output["data"][o_key]["temperature"] = {
                        "value": data["temp"],
                        "uom": "celsius",
                    }

                if "feels_like" in data and data["feels_like"] is not None:
                    output["data"][o_key]["apparentTemperature"] = {
                        "value": data["feels_like"],
                        "uom": "celsius",
                    }

                if "dew_point" in data and data["dew_point"] is not None:
                    output["data"][o_key]["dewpoint"] = {
                        "value": data["dew_point"],
                        "uom": "celsius",
                    }

                if "humidity" in data and data["humidity"] is not None:
                    output["data"][o_key]["relativeHumidity"] = {
                        "value": data["humidity"],
                        "uom": "percent",
                    }

                if "clouds" in data and data["clouds"] is not None:
                    output["data"][o_key]["skyCover"] = {
                        "value": data["clouds"],
                        "uom": "percent",
                    }

                if "wind_deg" in data and data["wind_deg"] is not None:
                    output["data"][o_key]["windDirection"] = {
                        "value": data["wind_deg"],
                        "uom": "degrees",
                    }

                if "wind_speed" in data and data["wind_speed"] is not None:
                    output["data"][o_key]["windSpeed"] = {
                        "value": data["wind_speed"],
                        "uom": "kph",
                    }

                if "wind_gust" in data and data["wind_gust"] is not None:
                    output["data"][o_key]["windGust"] = {
                        "value": data["wind_gust"],
                        "uom": "kph",
                    }

                if "pop" in data and data["pop"] is not None:
                    output["data"][o_key]["probabilityOfPrecipitation"] = {
                        "value": data["pop"] * 100,
                        "uom": "percent",
                    }

                if "snow" in data and data["snow"] is not None:
                    output["data"][o_key]["quantitativePrecipitation"] = {
                        "value": data["snow"]["1h"],
                        "uom": "mm",
                    }
                if "rain" in data and data["rain"] is not None:
                    output["data"][o_key]["quantitativePrecipitation"] = {
                        "value": data["rain"]["1h"],
                        "uom": "mm",
                    }

                if "pressure" in data and data["pressure"] is not None:
                    output["data"][o_key]["pressure"] = {
                        "value": data["pressure"],
                        "uom": "millibars",
                    }

                if "visibility" in data and data["visibility"] is not None:
                    output["data"][o_key]["visibility"] = {
                        "value": data["visibility"],
                        "uom": "meters",
                    }

                if "weather" in data and data["weather"] is not None:
                    w_value = ""
                    for w in data["weather"]:
                        if "description" in w:
                            w_value+=w["description"] + " "
                    output["data"][o_key]["weather"] = {
                        "value": w_value.strip(),
                    }

            output["status"]["responded"] = str(datetime.datetime.now())
            return output