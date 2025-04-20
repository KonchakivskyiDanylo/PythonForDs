from get_data.isw import last_isw
from get_data.weather import get_weather
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


def preprocess_data(df: pd.DataFrame, isw_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the dataset for prediction."""
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour_preciptype"] = df["hour_preciptype"].fillna("none").astype(str)
    df["hour_preciptype"] = df["hour_preciptype"].apply(
        lambda x: " ".join(x.strip("[]").replace("'", "").replace(" ", "").split(","))
    )

    isw_expanded = pd.concat([isw_df] * len(df), ignore_index=True)
    df_combined = pd.concat([df.reset_index(drop=True), isw_expanded], axis=1)

    return df_combined


def load_model(path: str):
    """Loads the pre-trained model from file."""
    with open(path, "rb") as f:
        return pickle.load(f)


def run_prediction():
    # Step 1: Update weather & ISW data
    get_weather.main()
    isw_df = last_isw.main()

    # Step 2: Load and prepare data
    df_weather = load_weather_data()
    df_processed = preprocess_data(df_weather, isw_df)

    # Step 3: Extract useful columns
    datetime_col = df_processed["datetime"]
    region_col = df_processed["region"]
    X = df_processed.drop(columns=["datetime"])

    # Step 4: Predict
    model = load_model("models/RandomForestClassifier_model.pkl")
    predictions = model.predict(X)

    # Step 5: Save results
    results_df = pd.DataFrame({
        "datetime": datetime_col,
        "region": region_col,
        "predictions": predictions
    })
    print(results_df)


    #Don't know how to save better, by regions or 1 by 1, i think better by regions
    # Step 6: Save to MongoDB
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        prediction_collection = db["prediction"]
        prediction_collection.delete_many({})#Сlear previous predictions
        prediction_collection.insert_many(results_df.to_dict("records"))
    except Exception as db_error:
        raise RuntimeError(f"Failed to save predictions to MongoDB: {db_error}")


if __name__ == "__main__":
    try:
        run_prediction()
    except Exception as e:
        print(f"Error occurred: {e}")
