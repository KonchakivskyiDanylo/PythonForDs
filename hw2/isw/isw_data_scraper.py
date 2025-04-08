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


def format_date(date, include_year=True):
    month_names = ["january", "february", "march", "april", "may", "june",
                   "july", "august", "september", "october", "november", "december"]

    if include_year:
        return f"{month_names[date.month - 1]}-{date.day}-{date.year}"
    else:
        return f"{month_names[date.month - 1]}-{date.day}"


def scrape_report(date, collection):
    date_with_year = format_date(date)
    date_without_year = format_date(date, include_year=False)
    #all links with reports
    url_formats = [
        f"https://www.understandingwar.org/backgrounder/russian-offensive-campaign-assessment-{date_with_year}",
        f"https://www.understandingwar.org/backgrounder/russian-offensive-campaign-assessment-{date_without_year}",
        f"https://www.understandingwar.org/backgrounder/russia-ukraine-warning-update-russian-offensive-campaign-assessment-{date_with_year}",
        f"https://www.understandingwar.org/backgrounder/russia-ukraine-warning-update-russian-offensive-campaign-assessment-{date_without_year}",
        f"https://www.understandingwar.org/backgrounder/russian-campaign-assessment-{date_without_year}",
        f"https://www.understandingwar.org/backgrounder/russian-offensive-campaign-update-{date_with_year}",
        f"https://www.understandingwar.org/backgrounder/russian-offensive-campaign-update-{date_without_year}",
        f"https://www.understandingwar.org/backgrounder/russian-offensive-campaign-assessment-{date_without_year}-0"
    ]

    for url in url_formats:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                document = {
                    "date": datetime.combine(date, datetime.min.time()),
                    "url": url,
                    "html_content": response.text,
                }

                existing = collection.find_one({"url": url})
                if existing:
                    collection.update_one({"_id": existing["_id"]}, {"$set": document})
                else:
                    collection.insert_one(document)
                return

        except Exception as e:
            print(f"Exception when trying URL {url}: {str(e)}")

    print(f"Failed for date {date.strftime('%Y-%m-%d')}")
    return


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
    parser.add_argument("--mongo", default="mongodb://localhost:27017/",
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
        client = pymongo.MongoClient(args.mongo)
        db = client[args.database]
        collection = db[args.collection]
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    scrape_data(args.start_date, args.end_date, collection)


if __name__ == "__main__":
    main()
