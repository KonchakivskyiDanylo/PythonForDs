from get_data.isw import last_isw
from get_data.weather import get_weather
from get_data.alerts import main as get_alerts
import pandas as pd
import pymongo
import pickle


def load_weather_data():
    """Connects to MongoDB and loads hourly weather data with region info."""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        collection = db["weather"]
        documents = collection.find()

        hourly_data = []
        for doc in documents:
            region = doc.get("region", "Unknown")
            for hour in doc.get("hourly_forecast", []):
                hour["region"] = region
                hourly_data.append(hour)

        return pd.DataFrame(hourly_data)

    except Exception as e:
        raise RuntimeError(f"Failed to load weather data: {e}")


def load_alarms_data():
    """Loading ongoing alarms"""
    try:
        # Using the existing function
        alerts = get_alerts()

        if not alerts:
            print("No alerts data available or error occurred.")
            return pd.DataFrame(columns=["location", "alert_type"])

        alerts_df = pd.DataFrame(alerts)
        alerts_df = alerts_df.rename(columns={"location": "region"})

        return alerts_df

    except Exception as e:
        print(f"Failed to load alarms data: {e}")
        return pd.DataFrame(columns=["region", "alert_type"])


def preprocess_data(df: pd.DataFrame, isw_df: pd.DataFrame, alarms_df: pd.DataFrame = None) -> pd.DataFrame:
    """Prepares the dataset for prediction."""
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour_preciptype"] = df["hour_preciptype"].fillna("none").astype(str)
    df["hour_preciptype"] = df["hour_preciptype"].apply(
        lambda x: " ".join(x.strip("[]").replace("'", "").replace(" ", "").split(","))
    )

    isw_expanded = pd.concat([isw_df] * len(df), ignore_index=True)
    df_combined = pd.concat([df.reset_index(drop=True), isw_expanded], axis=1)

    if alarms_df is not None and not alarms_df.empty:
        df_combined["has_active_alarm"] = df_combined["region"].apply(
            lambda region: 1 if region in alarms_df["region"].values else 0
        )

        def get_alert_type(region):
            matches = alarms_df[alarms_df["region"] == region]
            if not matches.empty:
                return matches.iloc[0]["alert_type"]
            return "none"

        df_combined["alert_type"] = df_combined["region"].apply(get_alert_type)
    else:
        df_combined["has_active_alarm"] = 0
        df_combined["alert_type"] = "none"

    return df_combined


def load_model(path: str):
    """Loads the pre-trained model from file."""
    with open(path, "rb") as f:
        return pickle.load(f)


def run_prediction():
    # Step 1: Update weather, ISW, and alarms data
    get_weather.main()
    isw_df = last_isw.main()
    alarms_df = load_alarms_data()  # Add alarms data loading

    # Step 2: Load and prepare data
    df_weather = load_weather_data()
    df_processed = preprocess_data(df_weather, isw_df, alarms_df)  # Pass alarms data to preprocessing

    # Step 3: Extract useful columns
    datetime_col = df_processed["datetime"]
    region_col = df_processed["region"]
    X = df_processed.drop(columns=["datetime", "region"])  # Ensure region is dropped as well

    # Step 4: Predict
    model = load_model("RandomForestClassifier_model.pkl")
    predictions = model.predict(X)

    # Step 5: Save results
    results_df = pd.DataFrame({
        "datetime": datetime_col,
        "region": region_col,
        "predictions": predictions
    })
    print(results_df)

    # Step 6: Save to MongoDB
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        prediction_collection = db["prediction"]
        prediction_collection.delete_many({})  # Clear previous predictions
        prediction_collection.insert_many(results_df.to_dict("records"))
    except Exception as db_error:
        raise RuntimeError(f"Failed to save predictions to MongoDB: {db_error}")


if __name__ == "__main__":
    try:
        run_prediction()
    except Exception as e:
        print(f"Error occurred: {e}")from get_data.isw import last_isw
from get_data.weather import get_weather
from get_data.alerts import main as get_alerts
import pandas as pd
import pymongo
import pickle


def load_weather_data():
    """Connects to MongoDB and loads hourly weather data with region info."""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        collection = db["weather"]
        documents = collection.find()

        hourly_data = []
        for doc in documents:
            region = doc.get("region", "Unknown")
            for hour in doc.get("hourly_forecast", []):
                hour["region"] = region
                hourly_data.append(hour)

        return pd.DataFrame(hourly_data)

    except Exception as e:
        raise RuntimeError(f"Failed to load weather data: {e}")


def load_alarms_data():
    """Loading ongoing alarms"""
    try:
        # Using the existing function
        alerts = get_alerts()

        if not alerts:
            print("No alerts data available or error occurred.")
            return pd.DataFrame(columns=["location", "alert_type"])

        alerts_df = pd.DataFrame(alerts)
        alerts_df = alerts_df.rename(columns={"location": "region"})

        return alerts_df

    except Exception as e:
        print(f"Failed to load alarms data: {e}")
        return pd.DataFrame(columns=["region", "alert_type"])


def preprocess_data(df: pd.DataFrame, isw_df: pd.DataFrame, alarms_df: pd.DataFrame = None) -> pd.DataFrame:
    """Prepares the dataset for prediction."""
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour_preciptype"] = df["hour_preciptype"].fillna("none").astype(str)
    df["hour_preciptype"] = df["hour_preciptype"].apply(
        lambda x: " ".join(x.strip("[]").replace("'", "").replace(" ", "").split(","))
    )

    isw_expanded = pd.concat([isw_df] * len(df), ignore_index=True)
    df_combined = pd.concat([df.reset_index(drop=True), isw_expanded], axis=1)

    if alarms_df is not None and not alarms_df.empty:
        df_combined["has_active_alarm"] = df_combined["region"].apply(
            lambda region: 1 if region in alarms_df["region"].values else 0
        )

        def get_alert_type(region):
            matches = alarms_df[alarms_df["region"] == region]
            if not matches.empty:
                return matches.iloc[0]["alert_type"]
            return "none"

        df_combined["alert_type"] = df_combined["region"].apply(get_alert_type)
    else:
        df_combined["has_active_alarm"] = 0
        df_combined["alert_type"] = "none"

    return df_combined


def load_model(path: str):
    """Loads the pre-trained model from file."""
    with open(path, "rb") as f:
        return pickle.load(f)


def run_prediction():
    # Step 1: Update weather, ISW, and alarms data
    get_weather.main()
    isw_df = last_isw.main()
    alarms_df = load_alarms_data()  # Add alarms data loading

    # Step 2: Load and prepare data
    df_weather = load_weather_data()
    df_processed = preprocess_data(df_weather, isw_df, alarms_df)  # Pass alarms data to preprocessing

    # Step 3: Extract useful columns
    datetime_col = df_processed["datetime"]
    region_col = df_processed["region"]
    X = df_processed.drop(columns=["datetime", "region"])  # Ensure region is dropped as well

    # Step 4: Predict
    model = load_model("RandomForestClassifier_model.pkl")
    predictions = model.predict(X)

    # Step 5: Save results
    results_df = pd.DataFrame({
        "datetime": datetime_col,
        "region": region_col,
        "predictions": predictions
    })
    print(results_df)

    # Step 6: Save to MongoDB
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        prediction_collection = db["prediction"]
        prediction_collection.delete_many({})  # Clear previous predictions
        prediction_collection.insert_many(results_df.to_dict("records"))
    except Exception as db_error:
        raise RuntimeError(f"Failed to save predictions to MongoDB: {db_error}")


if __name__ == "__main__":
    try:
        run_prediction()
    except Exception as e:
        print(f"Error occurred: {e}")