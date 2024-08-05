import json
import httpimport
import datetime

from expiring_lru_cache import lru_cache

import utility

"""
Metrics:
    weatherService_get_forecast_success_total{source}
    weatherService_get_forecast_invalid_total{source}
    weatherService_get_forecast_error_total{source}
    weatherService_get_forecast_implementation_success_total{source}
    weatherService_get_forecast_implementation_invalid_total{source}
    weatherService_get_forecast_implementation_error_total{source}
"""

class Weather:
    source = ""

    def output_date(self, date, offset_hours):
        return str(date + datetime.timedelta(hours=offset_hours))

    def convert_F_to_C(self, temp_F):
        return (temp_F-32)/1.8

    def convert_Hg_to_millibars(self, pressure_Hg):
        return pressure_Hg * 33.864

    def set_source(self, source):
        self.source = source

    def get_source(self):
        return self.source
    
    def get_required_paramters(self):
        return []

    def __normalize_coordinates(self, latitude, longitude):
        return [
            "{:.2f}".format(latitude),
            "{:.2f}".format(longitude),
        ]
    
    def normalized_uom(self, uom):
        if uom == "C":
            return "celsius"
        elif uom == "m":
            return "meters"
        return uom

    def get_forecast(self, latitude, longitude, parameters={}):
        for p in self.get_required_paramters():
            if p not in parameters.keys():
                raise ValueError(f"missing parameter: {p}")

        try:
            coordinates=self.__normalize_coordinates(float(latitude), float(longitude))
            forecast = self.__get_forecast_cached(coordinates[0], coordinates[1], parameters)
            is_valid, _ = self.validate_output(forecast)
            utility.inc("weatherService_get_forecast_success_total", {"source": self.get_source()})
            if not is_valid:
                utility.inc("weatherService_get_forecast_invalid_total", {"source": self.get_source()})
            return forecast
        except Exception as e:
            # fail for any reason, make sure we have error metric and re-raise the error
            utility.inc("weatherService_get_forecast_error_total", {"source": self.get_source()})
            raise e

    @lru_cache(expires_after=30) # 30 seconds
    def __get_forecast_cached(self, latitude, longitude, parameters):
        try:
            forecast = self.get_forecast_implementation(latitude, longitude, parameters)
            is_valid, _ = self.validate_output(forecast)
            utility.inc("weatherService_get_forecast_implementation_success_total", {"source": self.get_source()})
            if not is_valid:
                utility.inc("weatherService_get_forecast_implementation_invalid_total", {"source": self.get_source()})
            return forecast
        except Exception as e:
            # fail for any reason, make sure we have error metric and re-raise the error
            utility.inc("weatherService_get_forecast_implementation_error_total", {"source": self.get_source()})
            raise e

    def get_forecast_implementation(self, latitude, longitude, parameters={}):
        pass

    def pretty_print(self, forecast):
        print(json.dumps(forecast, indent=2))

    def validate_output(self, output):
        is_valid = True
        errors = []
        if "metadata" not in output:
            is_valid = False
            errors.append("missing metadata")
        if "data" not in output:
            is_valid = False
            errors.append("missing data")
        if "status" not in output:
            is_valid = False
            errors.append("missing status")

        for date in output["data"]:
            # key is the date, check each hour's data
            for key in output["data"][date]:
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
                    "weather",
                ]:
                    is_valid = False
                    errors.append(f"unexpected key: data.DATE.{key}")
                    continue
                
                for key2 in output["data"][date][key]:
                    if key2 not in [
                        "value",
                        "uom",
                    ]:
                        is_valid = False
                        errors.append(f"unexpected key: data.DATE.{key}.{key2}")
                        break
        
        return is_valid, errors