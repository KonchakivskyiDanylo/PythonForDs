from flask import Flask, request, jsonify, render_template
import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
from flask_cors import CORS

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
app = Flask(__name__)
CORS(app)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST","GET","OPTIONS"])
def get_prediction():
    json_data = request.get_json()
    if json_data.get("token") != API_TOKEN:
        raise InvalidUsage("Invalid API token", status_code=403)
    region = json_data.get("region")

    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["PythonForDs"]
    collection = db["prediction"]
    predict_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    if region:
        result = collection.find_one({"region": region})
        if result:
            result.pop("_id", None)
            hourly_predictions = result.get("hourly_predictions", [])
            response_data = {
                "last_prediction_time": predict_time,
                result.get("region", "Unknown"): hourly_predictions
            }
            return jsonify(response_data)
        else:
            raise InvalidUsage("No prediction found for region", status_code=404)
    else:
        results = collection.find()
        forecasts = []
        for r in results:
            r.pop("_id", None)
            forecasts.append({
                r.get("region", "Unknown"): r.get("hourly_predictions", [])
            })

        response_data = {
            "last_prediction_time": predict_time,
            "regions_forecast": forecasts
        }
        return jsonify(response_data)

if __name__ == "__main__":
    app.run(debug=True)
