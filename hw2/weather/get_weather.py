import datetime as dt
import requests
import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API_KEY")

if not API_TOKEN or not VISUAL_CROSSING_API_KEY:
    raise ValueError("Missing API keys. Please set them in the .env file.")

REGIONS = {
    "Lviv": "Львівська",
    "Kyiv": "Київська",
    "Kharkiv": "Харківська",
    "Odesa": "Одеська",
    "Dnipro": "Дніпропетровська",
    "Zaporizhzhia": "Запорізька",
    "Vinnytsia": "Вінницька",
    "Poltava": "Полтавська",
    "Zhytomyr": "Житомирська",
    "Khmelnytskyi": "Хмельницька",
    "Uzhhorod": "Закарпатська",
    "Ivano-Frankivsk": "Івано-Франківська",
    "Chernivtsi": "Чернівецька",
    "Ternopil": "Тернопільська",
    "Cherkasy": "Черкаська",
    "Kropyvnytskyi": "Кіровоградська",
    "Mykolaiv": "Миколаївська",
    "Kherson": "Херсонська",
    "Sumy": "Сумська",
    "Chernihiv": "Чернігівська",
    "Rivne": "Рівненська",
    "Lutsk": "Волинська",
    "Kramatorsk": "Донецька",
    "Sievierodonetsk": "Луганська"
}


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


def get_hourly_weather_data(region: str, region_name: str):
    """
    Fetches and processes hourly weather forecast data for the specified region.

    :param region: The geographical region identifier used to specify the city.
    :type region: str

    :param region_name: The name of the region in Ukrainian.
    :type region_name: str

    :return: A dictionary containing the region name, an array of hourly forecast data
        for the next 24 hours, and the timestamp of when the data was collected.
    :rtype: dict
    """
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

                    hourly_data.append({
                        "datetime": hour_datetime,
                        "city_latitude": city_latitude,
                        "city_longitude": city_longitude,
                        "day_tempmax": day_tempmax,
                        "day_tempmin": day_tempmin,
                        "day_temp": day_temp,
                        "day_precipcover": day_precipcover,
                        "day_moonphase": day_moonphase,
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
                        "region": region_name
                    })

                    hours_needed -= 1
                    if hours_needed <= 0:
                        break

                if hours_needed <= 0:
                    break

            return {
                "region": region_name,
                "hourly_forecast": hourly_data,
                "collected_at": dt.datetime.now(dt.timezone.utc).isoformat()
            }
        else:
            raise InvalidUsage(response.text, status_code=response.status_code)
    except Exception as e:
        raise InvalidUsage(f"Error getting weather data: {str(e)}", status_code=500)


def collect_and_save_weather():
    """
    Collects hourly weather data for predefined regions and saves it into a MongoDB
    collection.

    :raises Exception: If there is an error connecting to the MongoDB database.
                  Errors related to individual weather data retrieval are logged
                  but do not cause the main process to terminate.
    """
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        weather_collection = db["weather"]

        weather_collection.create_index([
            ("region", pymongo.ASCENDING)
        ], unique=True)

        for region_en, region_ua in REGIONS.items():
            try:
                weather_data = get_hourly_weather_data(region_en, region_ua)

                weather_collection.update_one(
                    {"region": region_ua},
                    {"$set": weather_data},
                    upsert=True
                )

            except Exception as e:
                print(f"Error handling weather for {region_en}: {str(e)}")

    except Exception as e:
        print(f"Database error: {str(e)}")


if __name__ == "__main__":
    collect_and_save_weather()
