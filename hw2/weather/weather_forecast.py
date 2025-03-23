import requests
import json
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
URL = "http://127.0.0.1:5000/weather"


def get_weather_for_all_oblasts():
    oblasts = [
        "Kyiv", "Lviv", "Kharkiv", "Odesa", "Dnipro", "Zaporizhzhia", "Vinnytsia", "Poltava", "Zhytomyr",
        "Khmelnytskyi", "Uzhhorod", "Ivano-Frankivsk", "Chernivtsi", "Ternopil", "Cherkasy", "Kropyvnytskyi",
        "Mykolaiv", "Kherson", "Sumy", "Chernihiv", "Rivne", "Lutsk", "Kramatorsk", "Sievierodonetsk"
    ]
    all_weather_data = {}

    for oblast in oblasts:
        request_data = {
            "token": API_TOKEN,
            "oblast": oblast,
            "requester_name": "Weather Aggregator"
        }

        try:
            response = requests.post(URL, json=request_data)

            if response.status_code == 200:
                all_weather_data[oblast] = response.json()
                print(f"✓")
            else:
                print(f"Error for {oblast}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error for {oblast}: {str(e)}")

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"weather_data_{current_time}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_weather_data, f, ensure_ascii=False, indent=2)

    print(f"\nData is saved in {filename}")
    return all_weather_data


if __name__ == "__main__":
    get_weather_for_all_oblasts()
