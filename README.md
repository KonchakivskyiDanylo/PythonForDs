# War Event Prediction Project

# Table of Contents

- [Team Members](#team-members)
- [Overview](#overview)
- [Critical Security Notice](#-critical-security-notice-env-file-protection)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
    - [System Requirements](#system-requirements)
    - [Installation Steps](#installation-steps)
    - [Environment Setup](#environment-setup)
- [Scripts and Their Purposes](#scripts-and-their-purposes)
    - [ISW Data Collection](#isw-data-collection-getdataisw)
    - [Weather Data Collection](#weather-data-collection-getdataweather)
    - [Alerts Data Collection](#alerts-data-collection-getdataalerts)
- [Data Collection and Analysis Workflow](#data-collection-and-analysis-workflow)
    - [Data Directory Structure](#data-directory-structure-data)
    - [Data Analysis](#data-analysis-data_analysis)
    - [Processed Data](#processed-data-prepared_data)
- [Model Training and Evaluation](#model-training-and-evaluation)
    - [Train Models](#train-models-train_models)
- [Backend Implementation](#backend-implementation)
- [Frontend Interface](#frontend-interface-templatesindexhtml)
- [Data Processing Pipeline](#data-processing-pipeline)
    - [Model Training and Prediction Pipeline](#model-training-and-prediction-pipeline)
- [Optional: Server Deployment](#optional-server-deployment)
    - [Official Documentation References](#official-documentation-references)
    - [Deployment Steps](#deployment-steps)
- [User Interface](#user-interface)
- [Acknowledgments](#acknowledgments)

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
- Historical weather and weather forecasts https://www.visualcrossing.com/weather-api
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

4. The project follows a modular directory structure:

```
PythonForDs/
├── data/                    # Raw datasets
│   ├── alarms.csv           # Historical air alarm events
│   ├── regions.csv          # Information about Ukrainian regions
│   └── weather.csv          # Historical weather data
├── data_analysis/           # Jupyter notebooks for analysis
│   ├── alarms_analysis.ipynb
│   ├── isw_analysis.ipynb
│   ├── weather_analysis.ipynb
│   └── merge_datasets.ipynb
├── prepared_data/           # Processed datasets
├── get_data/                # Data collection modules
├── models/                  # Trained model files
├── templates/               # Frontend templates
├── train_models/            # Model training notebooks
├── .env                     # Environment variables (not committed to git)
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── server.py                # Web server implementation
└── main.py                  # Main prediction engine
```

## **Prerequisites**

### **System Requirements**

- **Python 3.8+**
- **MongoDB**
- **Git**
- **Python Libraries** – listed in `requirements.txt`

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/KonchakivskyiDanylo/PythonForDs.git
cd PythonForDs
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

> You can change the database and collection names if needed

## Scripts and Their Purposes

### ISW Data Collection (`get_data/isw/`)

#### 1. ISW Data Scraper (`isw_data_scraper.py`)

- Scrapes daily reports from the Institute for the Study of War for a given period of time
- Saves HTML content to MongoDB

You can scrape ISW reports for a specific date range from the terminal:

```bash
# Basic usage
python -m get_data.isw.isw_data_scraper 2022-02-24 2025-03-01

# Optional MongoDB customization
python -m get_data.isw.isw_data_scraper 2022-02-24 2025-03-01 --mongo mongodb://localhost:27017/ --database PythonForDs --collection isw_html
```

**Arguments**:

- First argument: Start date (YYYY-MM-DD)
- Second argument: End date (YYYY-MM-DD)
- `--mongo`: Custom MongoDB connection string (optional)
- `--database`: MongoDB database name (optional)
- `--collection`: MongoDB collection name (optional)

```bash
# Run this script to get from the given data until today:
python -m get_data.isw.isw_data_scraper 2022-02-24 

# To get yesterday's-today's report run this:
python -m get_data.isw.isw_data_scraper 
```

> **Note:** Downloading the complete dataset from `2022-02-24` to `2025-03-01` may take up to **10 minutes**.
> Please note that some data may be missing for New Year's, Christmas, and `2022-11-24`.

#### 2. HTML Text Extractor (`html_extractor.py`)

- Parses and extracts text content from all scraped HTML reports in the given database collection
- Saves processed text to MongoDB

**Arguments**:

- `--mongo`: Custom MongoDB connection string (optional)
- `--database`: MongoDB database name (optional)
- `--input-collection`: MongoDB input collection name (optional)
- `--output-collection`: MongoDB output collection name (optional)

**Usage**:

```bash
# Basic usage
python -m get_data.isw.html_extractor

# Optional MongoDB customization
python -m get_data.isw.html_extractor --mongo mongodb://localhost:27017/ --database PythonForDs --input-collection isw_html --output-collection isw_report
```

#### 3. Latest ISW Report Processor (`last_isw.py`)

- Retrieves and processes the most recent ISW report
- Follows the same processing pipeline as historical data:
    - Scrapes latest report HTML
    - Extracts text content
    - Applies TF-IDF vectorization with predefined features
- Returns processed data ready for prediction

**Usage**:

```bash
python -m get_data.isw.last_isw
```

### Weather Data Collection (`get_data/weather/`)

#### 1. Weather Service API (`get_weather.py`)

- Collects hourly weather forecasts for Ukrainian regions
- Uses Visual Crossing Weather API to fetch detailed weather data
- Saves the data to MongoDB `weather` collection

**Key Features**:

- Hourly weather data for 24 hours
- Metrics include:
    - Temperature
    - Wind speed and direction
    - Humidity
    - Atmospheric pressure
    - Weather conditions
    - Other

- Requires `.env` file with `VISUAL_CROSSING_API_KEY`

**Usage**:

```bash
python -m get_data.weather.get_weather
```

### Alerts Data Collection (`get_data/alerts/`)

#### 1. Active Alerts Retriever (`get_active_alerts.py`)

- Fetches active air alerts in Ukrainian regions
- Uses the official Ukrainian alerts API
- Returns regions with currently active alerts
- Requires `.env` file with `ALERTS_API_TOKEN`

**Usage**:

```bash
python -m get_data.alerts.get_active_alerts
```

## Data Collection and Analysis Workflow

### Data Directory Structure (`/data`)

The `data` directory contains raw datasets collected from various sources:

- `alarms.csv` - Historical air alarm events across Ukrainian regions
- `regions.csv` - Information about Ukrainian regions
- `weather.csv` - Historical weather data for Ukrainian regions

> **Note:** While weather.csv and regions.csv are openly available data, access to alarms.csv requires special
> permission.
> Please contact us or the air-alarms.in.ua service to request access to
> this data.

### Data Analysis (`/data_analysis`)

The `data_analysis` directory contains Jupyter notebooks for comprehensive data analysis:

- `alarms_analysis.ipynb` - Processes raw data from `data/alarms.csv`, performs exploratory analysis with
  visualizations, and prepares cleaned alarm data for merging.

- `isw_analysis.ipynb` - Analyzes text data from MongoDB collections, creates TF-IDF (Term Frequency-Inverse Document
  Frequency) vectors
  from the reports, and generates a matrix with coefficients saved to `isw_prepared.csv`. Before running this notebook,
  ensure you've executed the ISW scraper scripts and have the MongoDB server running.

- `weather_analysis.ipynb` - Processes raw weather data from `data/weather.csv`, visualizes weather patterns, and
  prepares weather features for merging.

- `merge_datasets.ipynb` - Combines the three preprocessed datasets along with `regions.csv`, identifies correlations
  between features, and removes unnecessary variables to create the final optimized dataset for model training.

### Processed Data (`/prepared_data`)

After analysis, the processed datasets are stored in the `prepared_data` directory:

- `alarms_prepared.csv` - Cleaned and preprocessed alarm event data
- `isw_prepared.csv` - Matrix of TF-IDF coefficients extracted from ISW reports
- `weather_prepared.csv` - Processed weather features with relevant parameters for prediction
- `final_dataset.csv` - Combined dataset with optimized features, ready for model training

## Model Training and Evaluation

### Train Models (`train_models`)

#### 1. Model Implementation (`model.ipynb`)

The `model.ipynb` notebook contains the implementation of our prediction models:

- Implements **Linear Regression** and **Logistic Regression** models
- Includes preprocessing steps such as **scaling** and **one-hot encoding**
- Trains and evaluates models using **time series split**
- Evaluates model performance using various metrics
- Visualizes model performance and predictions

#### 2. Extended Model Exploration (`final_model.ipynb`)

The `final_model.ipynb` notebook:

- Trains **Random Forest**, **Decision Tree**, and **GaussianNB** models
- Evaluates each model and selects the best-performing one for prediction
- Saves the trained models as pickle files to the **`model`** directory for production use
- Displays **confusion matrices** and the **top 20 features** for all models
- Discusses potential improvements that can be made to enhance model performance

## Backend Implementation

#### 1. Main Prediction Engine (`main.py`)

The `main.py` script serves as the central prediction engine, doing the following operations:

- Updates weather data and ISW reports via calls to `get_weather.main()` and `last_isw.main()`
- Loads and preprocesses the collected data
- Makes predictions using the trained RandomForest model
- Organizes predictions by region
- Stores hourly forecasts in MongoDB for API access

**Usage**:

```bash
python main.py
```

#### 2. Web Server Implementation (`server.py`)

The `server.py` script implements a Flask-based web server that provides:

- A web interface accessible at the root URL
- REST API endpoints for retrieving predictions
- Authentication via API token
- Cross-Origin Resource Sharing (CORS) support

**API Endpoints**:

1. **Home Page**
    - **URL**: `/`
    - **Method**: GET
    - **Description**: Serves the frontend interface from templates/index.html

2. **Prediction API**
    - **URL**: `/predict`
    - **Methods**: POST, GET, OPTIONS
    - **Authentication**: Requires valid API token
    - **Parameters**: Optional region name(if not mentioned return for all regions)
    - **Response**: JSON with hourly predictions for specified region or all regions

3. **Active Alarms API**
    - **URL**: `/alarms`
    - **Methods**: POST, GET, OPTIONS
    - **Description**: Returns currently active air alerts across Ukraine

**Usage**:

```bash
python server.py
```

## Frontend Interface (`/templates/index.html`)

- Interactive map of Ukraine using the `ukraine.svg` file as the base map
- Real-time visualization of active air alerts across Ukrainian regions
- Hourly predictions displayed as a timeline for the selected region
- Color-coded regions to distinguish active alerts (red) from inactive ones (gray)
- Selection mechanism to focus on specific regions
- Time indicators for both current and predicted alert statuses
- Frontend communicates with the Flask backend via REST API endpoints

## Data Processing Pipeline

1. **Initial Data Sources**:
    - Weather data (provided by lecturer in CSV format)
    - Air alarm events data (provided by lecturer in CSV format)
    - Region information data

2. **ISW Report Collection**:
    - Scrape reports using `isw_data_scraper.py`
    - Store raw HTML in MongoDB `isw_html` collection
    - Process HTML with `html_extractor.py` to extract text content
    - Store processed text in MongoDB `isw_report` collection

3. **Data Analysis and Preparation**:
    - Process alarms data with `alarms_analysis.ipynb`
    - Analyze ISW reports with `isw_analysis.ipynb` to create TF-IDF vectors
    - Process weather data with `weather_analysis.ipynb`
    - Merge all datasets with `merge_datasets.ipynb`
    - Store prepared datasets in the `prepared_data` directory

### Model Training and Prediction Pipeline

1. **Model Implementation**:
    - Train prediction models using `model.ipynb` and `final_model.ipynb`
    - Implement Linear Regression and Logistic Regression models in `model.ipynb`
    - Implement Random Forest, Decision Tree and Gaussian NB models in `final_model.ipynb`
    - Use pipelines with scaling and one-hot encoding
    - Validate models with time series cross-validation
    - Save trained model as a pickle file

2. **Real-time Prediction System**:
    - Collect weather forecasts using `get_weather.py`
    - Store forecasts in MongoDB `weather` collection
    - Get latest ISW report using `last_isw.py`
    - Process report through HTML extraction and TF-IDF vectorization
    - Merge latest data with the trained model to generate predictions
    - Store predictions in MongoDB `prediction` collection

# Optional: Server Deployment

For production deployment, the application can be hosted on an AWS EC2 instance. This section provides instructions for
setting up the environment and deploying the application.

## Official Documentation References

- EC2 Management Console: [EC2 Console](https://eu-north-1.console.aws.amazon.com/ec2/home?region=eu-north-1#Home)
- Docker installation on AWS
  EC2: [Docker on EC2](https://linux.how2shout.com/how-to-install-docker-on-aws-ec2-ubuntu-22-04-or-20-04-linux/)
- MongoDB with
  Docker: [MongoDB with Docker](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-community-with-docker/)

## Deployment Steps

We've created deployment script(`deployment.sh`) that automate the setup process on an AWS EC2 instance:

### 1. **Set up SSH access to your EC2 instance**:

   ```bash
   # For Linux/Mac users, secure the SSH key permissions
   chmod 400 "path to key"
   
   # For Windows users, secure the SSH key permissions
   icacls "path to key" /inheritance:r /grant:r "%USERNAME%":(R)
   
   # Transfer file to server
   scp -i /path/to/your-key.pem /path/to/deployment.sh ubuntu@<your-ec2-public-ip>:/home/ubuntu/
   
   # Connect to your EC2 instance
   ssh -i "path to key" ubuntu@your-ec2-instance-address
   ```

### 2. **Run the setup script**:

   ```bash
   # Make the script executable
   chmod +x deployment.sh
   
   # Run the script
   ./deployment.sh
   ```

### 3. **Configure Jupyter Notebook**:

After running the setup script, configure Jupyter Notebook by editing its configuration file. Add the following lines
after `c.get_config()` in the `jupyter_notebook_config.py` file:

```bash
# After c=get_config()
c.NotebookApp.ip = '0.0.0.0'  # default value is 'localhost'
c.NotebookApp.open_browser = False  # default value is True
c.NotebookApp.password = u'sha1:b33024f36caa:ca337d6d6204ef502d69f8a49a915881c5e47ffa'
```

### 4. **Open Jupyter Notebook and upload your files**:

```bash
jupyter notebook
```

### 5. **Install Project Dependencies**:

```bash
pip install -r requirements.txt
```

### 6. **Run Flask Application**:

To start the Flask application using uWSGI, run the following command:

```bash
uwsgi --http 0.0.0.0:8000 --wsgi-file server.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191
```

> **Important Configuration Notes**:
>- Configure your EC2 security group to allow inbound traffic on the following ports:
>

- Port **8000** for the web application

> - Port **8888** for Jupyter Notebook

## User Interface

The frontend interface provides:

- Interactive map of Ukraine showing regions
- Real-time visualization of active air alerts
- Hourly predictions displayed as a timeline
- Color-coded regions based on alert status


## Acknowledgments

- Institute for the Study of War
- Visual Crossing Weather API
- Devs alerts in UA API
- Andrew Kurochkin(Lecturer)