# War Event Prediction Project

## **Team Members**

- *Konchakivskyi Danylo*
- *Lotariev Artem*
- *Beha Serhiy*
- *Kovalchuk Yurii*
- *Latyshenko Yaroslav*

## **Overview**

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

## 🔒 **CRITICAL SECURITY NOTICE: `.env` FILE PROTECTION**

**IMPORTANT: Your `.env` file contains sensitive credentials and MUST be kept ABSOLUTELY CONFIDENTIAL**

**Mandatory Security Practices**:

1. **Never** commit `.env` to version control
2. Use `.gitignore` to block `.env` files
3. Generate unique tokens for each environment
4. Rotate API keys periodically

```bash
# Add to .gitignore
.env
*.env
!.env.example
```

## Project Structure

The project consists of several key modules:

1. **Data Receiver**: Collects data from various sources
2. **Forecasting Module**: Prepares and executes prediction models
3. **Frontend UI**: Interaction interface for the backend

2 and 3 will be implemented soon

## **Prerequisites**

### **System Requirements**

- **Python 3.8+**
- **MongoDB**
- **Git**

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
ALERTS_API_TOKEN=your_alerts_api_token # you can apply for API on this website(we received ours within an hour) https://devs.alerts.in.ua/
```

2. MongoDB Setup

- Ensure MongoDB is installed and running locally if not all info can be found here https://www.mongodb.com/
- Default connection: `mongodb://localhost:27017/`
- Database name: `PythonForDs`
- Collections: `isw_html`, `isw_report`

You can change the database and collection names if needed

## Scripts and Their Purposes

### 1. ISW Data Scraper (`iws_data_scraper.py`)

- Scrapes daily reports from the Institute for the Study of War for a given period of time
- Saves HTML content to MongoDB

You can scrape ISW reports for a specific date range from the terminal:

```bash
# Basic usage
python iws_data_scraper.py 2022-02-24 2025-03-01

# Optional MongoDB customization
python iws_data_scraper.py 2022-02-24 2025-03-01 --mongo mongodb://localhost:27017/ --database PythonForDs --collection isw_html
```

**Arguments**:

- First argument: Start date (YYYY-MM-DD)
- Second argument: End date (YYYY-MM-DD)
- `--mongo`: Custom MongoDB connection string (optional)
- `--database`: MongoDB database name (optional)
- `--collection`: MongoDB collection name (optional)

```bash
# Run this script to get from the given data until today:
python iws_data_scraper.py 2022-02-24 

# To get today's report run this:
python iws_data_scraper.py 
```

### 2. HTML Text Extractor (`html_extractor.py`)

- Extracts text from scraped HTML reports
- Saves processed text to MongoDB

**Arguments**:

- `--mongo`: Custom MongoDB connection string (optional)
- `--database`: MongoDB database name (optional)
- `--input-collection`: MongoDB input collection name (optional)
- `--output-collection`: MongoDB output collection name (optional)

**Usage**:

```bash
# Basic usage
python html_extractor.py

# Optional MongoDB customization
python html_extractor.py --mongo mongodb://localhost:27017/ --database PythonForDs --input-collection isw_html --output-collection isw_report
```

### 3. Weather Service API (`get_weather.py`)

- Flask-based service for getting hourly weather forecasts for Ukrainian regions
- Uses Visual Crossing Weather API to fetch detailed weather data

**Key Features**:

- Hourly weather data for 24 hours
- Metrics include:
    - Temperature
    - Feels like temperature
    - Wind speed and direction
    - Humidity
    - Atmospheric pressure
    - Precipitation probability
    - Weather conditions


- Requires `.env` file with `API_TOKEN` and `VISUAL_CROSSING_API_KEY`

**Usage**:

```bash
# Run the Flask weather service
python get_weather.py
```

Although you can run the Python script directly, it is better to use WSGI server instead

**API Endpoint**:

- Method: POST
- URL: http://127.0.0.1:5000
- Endpoint: `/weather`
- Required JSON payload:
  ```json
  {
    "token": "your_api_token",
    "oblast": "Kyiv",
    "requester_name": "Your Name"
  }
  ```

We recommend using Postman https://www.postman.com/downloads/

To use it, create postman collection -> add_request -> use text above and click send to get response

### 4. Weather Forecast Aggregator (`weather_forecast.py`)

- Retrieves weather data for Ukrainian oblasts
- Return forecast data for every Ukrainian oblast for the next 24 hours

**Usage**:

```bash
python weather_forecast.py
```

Make sure that get_weather.py is currently running

### 5. Alerts (`alerts.py`)

- Flask-based service for getting active alerts in Ukraine
- Uses devs_alerts_in_ua and their python library

- Requires `.env` file with `API_TOKEN` and `ALERTS_API_TOKEN`

**Usage**:

```bash
# Run the Flask weather service
python alerts.py
```

Although you can just run python script, it is better to use WSGI server instead

**API Endpoint**:

- Method: POST
- URL: http://127.0.0.1:5001
- Endpoint: `/alerts`
- Required JSON payload:
  ```json
  {
    "token": "your_api_token",
    "requester_name": "Your Name"
  }
  ```

You can use it in postman with all the info in the end of 3rd paragraph

## Data Collection Workflow

1. Run ISW scraper to collect historical reports
2. Process HTML reports using parser
3. Collect weather forecasts
4. Retrieve active alerts

## Acknowledgments

- Institute for the Study of War
- Visual Crossing Weather API
- Devs alerts in UA API
- Andrew Kurochkin