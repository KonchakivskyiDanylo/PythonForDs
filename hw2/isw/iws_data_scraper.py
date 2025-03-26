import requests
import pymongo
import time
import random
import argparse
from datetime import datetime, timedelta


def validate_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid date format. Use YYYY-MM-DD")


def format_date(date):
    month_names = ["january", "february", "march", "april", "may", "june",
                   "july", "august", "september", "october", "november", "december"]
    return f"{month_names[date.month - 1]}-{date.day}-{date.year}"


def scrape_report(date, collection):
    base_url = "https://www.understandingwar.org/backgrounder/russian-offensive-campaign-assessment-"
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
                collection.update_one({"_id": existing["_id"]}, {"$set": document})
            else:
                collection.insert_one(document)

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


def scrape_data(start_date, end_date, collection):
    current_date = start_date
    while current_date <= end_date:
        scrape_report(current_date, collection)
        delay = random.uniform(0.2, 1.0)
        time.sleep(delay)
        current_date += timedelta(days=1)


def main():
    today = datetime.now().date()
    parser = argparse.ArgumentParser(description="ISW Report Scraper")
    parser.add_argument("start_date", nargs='?', type=validate_date,
                        default=today,
                        help="Start date (YYYY-MM-DD), defaults to today")
    parser.add_argument("end_date", nargs='?', type=validate_date,
                        default=today,
                        help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017/",
                        help="MongoDB connection string (default: localhost)")
    parser.add_argument("--database", default="PythonForDs",
                        help="MongoDB database name (default: PythonForDs)")
    parser.add_argument("--collection", default="isw_html",
                        help="MongoDB collection name (default: isw_html)")
    args = parser.parse_args()
    if args.start_date > args.end_date:
        print("Start date must be before or equal to end date.")
        return

    try:
        client = pymongo.MongoClient(args.mongo_uri)
        db = client[args.database]
        collection = db[args.collection]
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    scrape_data(args.start_date, args.end_date, collection)


if __name__ == "__main__":
    main()
