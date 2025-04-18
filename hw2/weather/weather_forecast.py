import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
URL = "http://127.0.0.1:5000/weather"


def get_weather_for_all_regions():
    regions = [
        "Kyiv", "Lviv", "Kharkiv", "Odesa", "Dnipro", "Zaporizhzhia", "Vinnytsia", "Poltava", "Zhytomyr",
        "Khmelnytskyi", "Uzhhorod", "Ivano-Frankivsk", "Chernivtsi", "Ternopil", "Cherkasy", "Kropyvnytskyi",
        "Mykolaiv", "Kherson", "Sumy", "Chernihiv", "Rivne", "Lutsk", "Kramatorsk", "Sievierodonetsk"
    ]
    all_weather_data = {}

    for region in regions:
        request_data = {
            "token": API_TOKEN,
            "region": region,
            "requester_name": "Weather Aggregator"
        }

        try:
            response = requests.post(URL, json=request_data)

            if response.status_code == 200:
                all_weather_data[region] = response.json()
                print(f"Successfully retrieved data for {region}")
            else:
                print(f"Error for {region}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error for {region}: {str(e)}")

    # to ensure it works
    with open("ukrainian_weather_data.json", "w", encoding="utf-8") as f:
        json.dump(all_weather_data, f, ensure_ascii=False, indent=2)

    print(f"Weather data for {len(all_weather_data)} regions saved to ukrainian_weather_data.json")
    return all_weather_data


if __name__ == "__main__":
    get_weather_for_all_regions()