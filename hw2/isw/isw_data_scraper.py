"""
ISW (Institute for the Study of War) Report Scraper
This module provides functionality to scrape war reports from the ISW website.
"""
from typing import List, Optional
import requests
import pymongo
import time
import random
import argparse
from datetime import datetime, timedelta

# Base URL for all ISW reports
BASE_URL = "https://www.understandingwar.org/backgrounder/"

# different URL formats
URL_PATTERNS = [
    "russian-offensive-campaign-assessment-{}",
    "russia-ukraine-warning-update-russian-offensive-campaign-assessment-{}",
    "russian-campaign-assessment-{}",
    "russian-offensive-campaign-update-{}",
    "russian-offensive-campaign-assessment-{}-0"
]


class ISWReportScraper:
    def __init__(self, mongo_client: pymongo.MongoClient, database: str, collection: str):
        self.db = mongo_client[database]
        self.collection = self.db[collection]
        self.month_names = ["january", "february", "march", "april", "may", "june",
                            "july", "august", "september", "october", "november", "december"]

    def format_date(self, date: datetime.date, include_year: bool = True) -> str:
        """
        Formats the given date into a string representation based on the month names
        stored within the instance. The format includes the month name, day, and
        optionally the year, depending on the value of the `include_year` parameter.

        :param date: The date to be formatted.
        :type date: datetime.date
        :param include_year: Determines whether the year is included in the
            formatted string. Defaults to True.
        :type include_year: bool
        :return: A string representation of the formatted date, consisting of the
            month name, the day, and optionally the year.
        :rtype: str
        """
        month_name = self.month_names[date.month - 1]
        if include_year:
            return f"{month_name}-{date.day}-{date.year}"
        return f"{month_name}-{date.day}"

    def generate_urls(self, date: datetime.date) -> List[str]:
        """
        Generates a list of URLs based on predefined patterns and the given date.

        :param date: The date to format and use in the URL patterns.
        :type date: datetime.date
        :return: A list of generated URLs based on the given date and predefined
                 URL patterns.
        :rtype: List[str]
        """
        date_with_year = self.format_date(date)
        date_without_year = self.format_date(date, include_year=False)
        urls = []
        for pattern in URL_PATTERNS:
            urls.append(BASE_URL + pattern.format(date_with_year))
            urls.append(BASE_URL + pattern.format(date_without_year))
        return urls

    def save_report(self, date: datetime.date, url: str, content: str) -> None:
        """
        Save a report to the database. This function checks if a report with the same URL
        already exists in the database. If it does, the existing entry is updated with
        the new data. Otherwise, the new report is inserted as a new document.

        :param date: The date of the report.
        :type date: datetime.date
        :param url: The URL of the report.
        :type url: str
        :param content: The HTML content of the report.
        :type content: str
        :return: None
        """
        document = {
            "date": datetime.combine(date, datetime.min.time()),
            "url": url,
            "html_content": content
        }
        existing = self.collection.find_one({"url": url})
        if existing:
            self.collection.update_one({"_id": existing["_id"]}, {"$set": document})
        else:
            self.collection.insert_one(document)

    def scrape_report(self, date: datetime.date) -> Optional[bool]:
        """
        Scrapes report data for a given date by generating URLs, requesting
        each, and saving the report if the request succeeds.

        :param date: The target date for which the report is to be scraped.
        :type date: datetime.date
        :return: Returns True if the report is successfully scraped and saved,
            None if all attempts fail.
        :rtype: Optional[bool]
        """
        for url in self.generate_urls(date):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    self.save_report(date, url, response.text)
                    return True
            except Exception as e:
                print(f"Exception when trying URL {url}: {str(e)}")
        print(f"Failed for date {date.strftime('%Y-%m-%d')}")
        return None

    def scrape_data(self, start_date: datetime.date, end_date: datetime.date) -> None:
        """
        Scrapes data for each date in the given date range by calling the scrape_report
        method for each date. Introduces a random delay between iterations to mimic
        human behavior.

        :param start_date: The start date of the range to scrape data for.
        :type start_date: datetime.date
        :param end_date: The end date of the range to scrape data for.
        :type end_date: datetime.date
        :return: None
        """
        current_date = start_date
        while current_date <= end_date:
            self.scrape_report(current_date)
            delay = random.uniform(0.2, 1.0)
            time.sleep(delay)
            current_date += timedelta(days=1)


def validate_date(date_string: str) -> datetime.date:
    """
    Converts a date string in the format YYYY-MM-DD to a datetime.date object.
    If the format is incorrect, an exception is raised.

    :param date_string: The input date as a string in the format "YYYY-MM-DD".
    :type date_string: str
    :return: A datetime.date object representing the valid date.
    :rtype: datetime.date
    :raises argparse.ArgumentTypeError: If the date_string does not match the
        format "YYYY-MM-DD".
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid date format. Use YYYY-MM-DD")


def main():
    """
    Executes the main routine for scraping ISW (Institute for the Study of War) reports
    and storing the results in a MongoDB database. The script allows users to specify
    a date range for which reports are fetched and provides options to configure
    MongoDB connection details.

    :raises Exception: If any error occurs while connecting to the MongoDB instance.

    :return: None
    """
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
        scraper = ISWReportScraper(client, args.database, args.collection)
        scraper.scrape_data(args.start_date, args.end_date)

    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")


if __name__ == "__main__":
    main()
