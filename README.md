# War Event Prediction Project

### Team 2:

- Konchakivskyi Danylo
- Lotariev Artem
- Beha Serhiy
- Kovalchuk Yurii
- Latyshenko Yaroslav

## Overview

This is a Python-based SaaS (Software as a Service) project designed to predict war events in Ukrainian regions using
multiple data sources. The project aims to forecast three primary event types:

- Air alarms
- Explosions
- Artillery fire

The system combines data from various sources including:

- War events https://air-alarms.in.ua/
- Institute for the Study of War (ISW) reports https://www.understandingwar.org/
- Historical weather
- Weather forecasts https://www.visualcrossing.com/weather-api
- Regional alert systems https://devs.alerts.in.ua/

## Project Structure

The project consists of several key modules:

1. **Data Receiver**: Collects data from various sources
2. **Forecasting Module**: Prepares and executes prediction models
3. **Frontend UI**: Interaction interface for the backend

2 and 3 will be implemented soon!

## Prerequisites

### System Requirements

- Python 3.8+
- MongoDB
- Git

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/your-username/war-event-prediction.git
cd war-event-prediction
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

### Environment Setup

1. Create a `.env` file in the project root with the following variables:

```
API_TOKEN=your_generated_api_token # can be generated on different websites 
VISUAL_CROSSING_API_KEY=your_visual_crossing_api_key # can be found here https://www.visualcrossing.com/weather-api
ALERTS_API_TOKEN=your_alerts_api_token # you can apply for API on this website( we get during an hour) https://devs.alerts.in.ua/
```

2. MongoDB Setup

- Ensure MongoDB is installed and running locally if not all info can be found here https://www.mongodb.com/
- Default connection: `mongodb://localhost:27017/`
- Database name: `PythonForDs`
- Collections: `isw_html`, `isw_report`

Database and collections names can be changed if you want

## Scripts and Their Purposes

### 1. ISW Data Scraper (`iws_data_scraper.py`)

- Scrapes daily reports from the Institute for the Study of War
- Saves HTML content to MongoDB

**Usage**:

```bash
python iws_data_scraper.py 2022-02-24 2025-03-01 mongodb
```

### 2. HTML Parser (`html_parser.py`)

- Extracts text from scraped HTML reports
- Saves processed text to MongoDB and text files

**Usage**:

```bash
python html_parser.py
```

### 3. Weather Forecast (`weather_forecast.py`)

- Retrieves weather data for multiple Ukrainian oblasts
- Saves forecast data to JSON files

**Usage**:

```bash
python weather_forecast.py
```

### 4. Alerts Service (`alerts.py`)

- Flask-based API for retrieving active air alerts
- Requires running a local server

**Usage**:

```bash
flask run
```

## Data Collection Workflow

1. Run ISW scraper to collect historical reports
2. Process HTML reports using parser
3. Collect weather forecasts
4. Retrieve active alerts

## Contributions

Please read `CONTRIBUTING.md` (to be created) for details on our code of conduct and the process for submitting pull
requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgments

- Institute for the Study of War
- Visual Crossing Weather API
- Ukrainian Alerts API