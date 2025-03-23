import requests
import pymongo
import time
import random
from datetime import datetime, timedelta

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["PythonForDs"]
collection = db["isw_html"]

base_url = "https://www.understandingwar.org/backgrounder/russian-offensive-campaign-assessment-"


def format_date(date):
    month_names = ["january", "february", "march", "april", "may", "june",
                   "july", "august", "september", "october", "november", "december"]
    return f"{month_names[date.month - 1]}-{date.day}-{date.year}"


def scrape_report(date):
    formatted_date = format_date(date)
    url = f"{base_url}{formatted_date}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            document = {
                "date": date,
                "url": url,
                "html_content": response.text,
            }

            existing = collection.find_one({"url": url})
            if existing:
                print(f"Report for {date.strftime('%Y-%m-%d')} already exists, updating...")
                collection.update_one({"_id": existing["_id"]}, {"$set": document})
            else:
                result = collection.insert_one(document)
                print(f"Saved report for {date.strftime('%Y-%m-%d')}, ID: {result.inserted_id}")

            return True
        elif response.status_code == 404:
            print(f"No report found for {date.strftime('%Y-%m-%d')}, URL: {url}")
            return False
        else:
            print(f"Error fetching {url}: Status code {response.status_code}")
            return False

    except Exception as e:
        print(f"Exception when scraping {url}: {str(e)}")
        return False


def scrape_data(start_date, end_date):
    current_date = start_date

    while current_date <= end_date:
        scrape_report(current_date)
        delay = random.uniform(0.2, 1.0)
        time.sleep(delay)
        current_date += timedelta(days=1)


def main():
    start_date = datetime(2025, 2, 24)
    end_date = datetime(2025, 3, 1)
    scrape_data(start_date, end_date)


if __name__ == "__main__":
    main()
