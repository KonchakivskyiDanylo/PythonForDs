import requests
import json
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")


def get_weather_for_all_oblasts():
    oblasts = [
        "київська", "львівська", "харківська", "одеська", "дніпропетровська",
        "запорізька", "вінницька", "полтавська", "житомирська", "хмельницька",
        "закарпатська", "івано-франківська", "чернівецька", "тернопільська",
        "черкаська", "кіровоградська", "миколаївська", "херсонська", "сумська",
        "чернігівська", "рівненська", "волинська", "донецька", "луганська"
    ]

    url = "http://127.0.0.1:5000/weather"

    all_weather_data = {}

    for oblast in oblasts:
        request_data = {
            "token": API_TOKEN,
            "oblast": oblast,
            "requester_name": "Weather Aggregator"
        }

        try:
            response = requests.post(url, json=request_data)

            if response.status_code == 200:
                all_weather_data[oblast] = response.json()
                print(f"✓ Отримано дані для {oblast} області")
            else:
                print(f"✗ Помилка для {oblast} області: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Помилка при отриманні даних для {oblast} області: {str(e)}")

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"weather_data_{current_time}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_weather_data, f, ensure_ascii=False, indent=2)

    print(f"\nВсі дані збережено у файл {filename}")
    return all_weather_data


if __name__ == "__main__":
    print("Почалася агрегація погодних даних для всіх областей України...")
    get_weather_for_all_oblasts()