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


def get_hourly_weather_data(oblast: str):
    city = oblast + ", Ukraine"
    if not city:
        raise InvalidUsage(f"{oblast} is not found", status_code=400)

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

            for day in data.get("days", []):
                for hour_data in day.get("hours", []):
                    hour_time = dt.datetime.strptime(hour_data.get("datetime"), "%H:%M:%S")
                    hour = hour_time.hour

                    if day == data.get("days", [])[0] and hour < current_hour:
                        continue

                    hourly_data.append({
                        "datetime": f"{day.get('datetime')} {hour_data.get('datetime')}",
                        "hour": hour,
                        "temperature_c": hour_data.get("temp"),
                        "feels_like_c": hour_data.get("feelslike"),
                        "wind_speed_kmh": hour_data.get("windspeed"),
                        "wind_direction": hour_data.get("winddir"),
                        "humidity_pct": hour_data.get("humidity"),
                        "pressure_mb": hour_data.get("pressure"),
                        "precip_probability_pct": hour_data.get("precipprob"),
                        "conditions": hour_data.get("conditions")
                    })

                    hours_needed -= 1
                    if hours_needed <= 0:
                        break

                if hours_needed <= 0:
                    break

            return {
                "oblast": oblast,
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

    oblast = json_data.get("oblast")
    requester_name = json_data.get("requester_name")

    if not oblast or not requester_name:
        raise InvalidUsage("Missing required fields", status_code=400)

    weather_data = get_hourly_weather_data(oblast)

    result = {
        "requester": requester_name,
        "request_time": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "data": weather_data
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
