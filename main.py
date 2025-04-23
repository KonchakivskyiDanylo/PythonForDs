from get_data.isw import last_isw
from get_data.weather import get_weather
import pandas as pd
import pymongo
import pickle


def load_weather_data():
    """
    Loads weather data from a MongoDB collection and converts it into a pandas DataFrame.

    :raises RuntimeError: If there is an issue connecting to MongoDB or retrieving the data.
    :return: A pandas DataFrame containing the hourly forecast data with associated regions.
    :rtype: pandas.DataFrame
    """
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
    """
    Preprocesses and combines weather data with ISW reports.

    :param df:
        A pandas DataFrame that contains weather data.
    :param isw_df:
         A pandas DataFrame containing the TF-IDF vectorized coefficients derived from the latest ISW report.
    :return:
        A pandas DataFrame that combines the processed `df` DataFrame with `isw_df`.
    """
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["hour_preciptype"] = df["hour_preciptype"].fillna("none").astype(str)
    df["hour_preciptype"] = df["hour_preciptype"].apply(
        lambda x: " ".join(x.strip("[]").replace("'", "").replace(" ", "").split(","))
    )

    isw_expanded = pd.concat([isw_df] * len(df), ignore_index=True)
    df_combined = pd.concat([df.reset_index(drop=True), isw_expanded], axis=1)

    return df_combined


def load_model(path: str):
    """
    Loads a model from a file.
    """
    with open(path, "rb") as f:
        return pickle.load(f)


def main():
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
    X["region"] = "None" #It would be better to retrain the model, but due to the time required, we opted for this approach instead

    # Step 4: Predict
    model = load_model("models/RandomForestClassifier_model.pkl")
    predictions = model.predict(X)

    # Step 5: Save results
    results_df = pd.DataFrame({
        "datetime": datetime_col,
        "region": region_col,
        "predictions": predictions
    })

    # Step 6: Save to MongoDB
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["PythonForDs"]
        prediction_collection = db["prediction"]
        prediction_collection.delete_many({})
        prediction_collection.create_index([
            ("region", pymongo.ASCENDING)
        ], unique=True)

        for region, region_group in results_df.groupby("region"):
            region_group = region_group.sort_values("datetime")

            hourly_predictions = []
            for _, row in region_group.iterrows():
                hourly_predictions.append({
                    "datetime": row["datetime"].isoformat(),
                    "prediction": int(row["predictions"])
                })
            prediction_data = {
                "region": region,
                "hourly_predictions": hourly_predictions,
            }

            prediction_collection.update_one(
                {"region": region},
                {"$set": prediction_data},
                upsert=True
            )
    except Exception as db_error:
        raise RuntimeError(f"Failed to save predictions to MongoDB: {db_error}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error occurred: {e}")
