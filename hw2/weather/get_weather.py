import datetime as dt
import requests
from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API_KEY")

if not API_TOKEN or not VISUAL_CROSSING_API_KEY:
    raise ValueError("Missing API keys. Please set them in the .env file.")

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_hourly_weather_data(region: str):
    city = region + ", Ukraine"
    if not city:
        raise InvalidUsage(f"{region} is not found", status_code=400)

    today = dt.datetime.now().strftime("%Y-%m-%d")
    tomorrow = (dt.datetime.now() + dt.timedelta(days=1)).strftime("%Y-%m-%d")

    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{today}/{tomorrow}?unitGroup=metric&include=hours&key={VISUAL_CROSSING_API_KEY}&contentType=json"

    try:
        response = requests.get(url)

        if response.status_code == requests.codes.ok:
            data = response.json()
            current_hour = dt.datetime.now().hour

            hourly_data = []
            hours_needed = 24

            city_latitude = data.get("latitude")
            city_longitude = data.get("longitude")

            for day in data.get("days", []):
                day_tempmax = day.get("tempmax")
                day_tempmin = day.get("tempmin")
                day_temp = day.get("temp")
                day_precipcover = day.get("precipcover", 0)
                day_moonphase = day.get("moonphase", 0)

                for hour_data in day.get("hours", []):
                    hour_time = dt.datetime.strptime(hour_data.get("datetime"), "%H:%M:%S")
                    hour = hour_time.hour

                    if day == data.get("days", [])[0] and hour < current_hour:
                        continue

                    hour_datetime = f"{day.get('datetime')}T{hour_data.get('datetime')}"
                    hour_datetime_obj = dt.datetime.strptime(hour_datetime, "%Y-%m-%dT%H:%M:%S")
                    hour_datetimeEpoch = int(hour_datetime_obj.timestamp())

                    hourly_data.append({
                        "datetime": hour_datetime,
                        "hour_datetimeEpoch": hour_datetimeEpoch,
                        "city_latitude": city_latitude,
                        "city_longitude": city_longitude,
                        "day_tempmax": day_tempmax,
                        "day_tempmin": day_tempmin,
                        "day_temp": day_temp,
                        "day_precipcover": day_precipcover,
                        "day_moonphase": day_moonphase,
                        "hour": hour,
                        "hour_temp": hour_data.get("temp"),
                        "hour_humidity": hour_data.get("humidity"),
                        "hour_dew": hour_data.get("dew"),
                        "hour_precip": hour_data.get("precip", 0),
                        "hour_precipprob": hour_data.get("precipprob", 0),
                        "hour_snow": hour_data.get("snow", 0),
                        "hour_snowdepth": hour_data.get("snowdepth", 0),
                        "hour_preciptype": hour_data.get("preciptype", ""),
                        "hour_windgust": hour_data.get("windgust", 0),
                        "hour_windspeed": hour_data.get("windspeed", 0),
                        "hour_winddir": hour_data.get("winddir", 0),
                        "hour_pressure": hour_data.get("pressure", 0),
                        "hour_visibility": hour_data.get("visibility", 0),
                        "hour_cloudcover": hour_data.get("cloudcover", 0),
                        "hour_solarradiation": hour_data.get("solarradiation", 0),
                        "hour_solarenergy": hour_data.get("solarenergy", 0),
                        "hour_uvindex": hour_data.get("uvindex", 0),
                        "hour_conditions": hour_data.get("conditions", ""),
                        "region": region
                    })

                    hours_needed -= 1
                    if hours_needed <= 0:
                        break

                if hours_needed <= 0:
                    break

            return {
                "region": region,
                "hourly_forecast": hourly_data
            }
        else:
            raise InvalidUsage(response.text, status_code=response.status_code)
    except Exception as e:
        raise InvalidUsage(f"Error getting weather data: {str(e)}", status_code=500)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Weather Service for Ukrainian Regions</h2></p>"


@app.route("/weather", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") != API_TOKEN:
        raise InvalidUsage("Invalid API token", status_code=403)

    region = json_data.get("region")
    requester_name = json_data.get("requester_name")

    if not region or not requester_name:
        raise InvalidUsage("Missing required fields", status_code=400)

    weather_data = get_hourly_weather_data(region)

    result = {
        "requester": requester_name,
        "request_time": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "data": weather_data
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)