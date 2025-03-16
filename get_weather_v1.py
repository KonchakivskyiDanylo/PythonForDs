import datetime as dt
import json
import requests
from flask import Flask, jsonify, request
from tokens import API_TOKEN, VISUAL_CROSSING_API_KEY

API_TOKEN = API_TOKEN
VISUAL_CROSSING_API_KEY = VISUAL_CROSSING_API_KEY

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
    oblast_centers = {
        "київська": "Kyiv, Ukraine",
        "львівська": "Lviv, Ukraine",
        "харківська": "Kharkiv, Ukraine",
        "одеська": "Odesa, Ukraine",
        "дніпропетровська": "Dnipro, Ukraine",
        "запорізька": "Zaporizhzhia, Ukraine",
        "вінницька": "Vinnytsia, Ukraine",
        "полтавська": "Poltava, Ukraine",
        "житомирська": "Zhytomyr, Ukraine",
        "хмельницька": "Khmelnytskyi, Ukraine",
        "закарпатська": "Uzhhorod, Ukraine",
        "івано-франківська": "Ivano-Frankivsk, Ukraine",
        "чернівецька": "Chernivtsi, Ukraine",
        "тернопільська": "Ternopil, Ukraine",
        "черкаська": "Cherkasy, Ukraine",
        "кіровоградська": "Kropyvnytskyi, Ukraine",
        "миколаївська": "Mykolaiv, Ukraine",
        "херсонська": "Kherson, Ukraine",
        "сумська": "Sumy, Ukraine",
        "чернігівська": "Chernihiv, Ukraine",
        "рівненська": "Rivne, Ukraine",
        "волинська": "Lutsk, Ukraine",
        "донецька": "Kramatorsk, Ukraine",
        "луганська": "Sievierodonetsk, Ukraine"
    }

    city = oblast_centers.get(oblast.lower())
    if not city:
        raise InvalidUsage(f"Область '{oblast}' не знайдена у списку областей України", status_code=400)

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
                        "час": hour_data.get("datetime"),
                        "температура_C": hour_data.get("temp"),
                        "відчувається_як_C": hour_data.get("feelslike"),
                        "швидкість_вітру_km/h": hour_data.get("windspeed"),
                        "напрям_вітру": hour_data.get("winddir"),
                        "вологість": hour_data.get("humidity"),
                        "тиск_mb": hour_data.get("pressure"),
                        "імовірність_опадів": hour_data.get("precipprob"),
                        "опис": hour_data.get("conditions")
                    })

                    hours_needed -= 1
                    if hours_needed <= 0:
                        break

                if hours_needed <= 0:
                    break

            return {
                "область": oblast,
                "місто": city,
                "прогноз_на_24_години": hourly_data
            }
        else:
            raise InvalidUsage(response.text, status_code=response.status_code)
    except Exception as e:
        raise InvalidUsage(f"Помилка при отриманні даних про погоду: {str(e)}", status_code=500)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Погодний сервіс для областей України</h2></p>"


@app.route("/weather", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") != API_TOKEN:
        raise InvalidUsage("Невірний API токен", status_code=403)

    oblast = json_data.get("oblast")
    requester_name = json_data.get("requester_name")

    if not oblast or not requester_name:
        raise InvalidUsage("Відсутні обов'язкові поля", status_code=400)

    weather_data = get_hourly_weather_data(oblast)

    result = {
        "запитувач": requester_name,
        "час_запиту": dt.datetime.utcnow().isoformat() + "Z",
        "дані": weather_data
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)