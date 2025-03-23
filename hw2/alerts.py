from flask import Flask, jsonify, request
import datetime as dt
import os
from dotenv import load_dotenv
from alerts_in_ua import Client as AlertsClient

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ALERTS_API_TOKEN = os.getenv("ALERTS_API_TOKEN", "***REMOVED***")

if not API_TOKEN:
    raise ValueError("Missing API_TOKEN. Please set it in the .env file.")

app = Flask(__name__)


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


def get_alerts_data(oblast=None):
    """
    Get alert information for a specific oblast or all of Ukraine
    """
    try:
        alerts_client = AlertsClient(token=ALERTS_API_TOKEN)
        active_alerts = alerts_client.get_active_alerts()

        # If oblast is specified, filter alerts for that region
        if oblast:
            filtered_alerts = []
            for alert in active_alerts:
                # Check if the alert is for the specified oblast
                if oblast.lower() in alert.get("location_title", "").lower():
                    filtered_alerts.append({
                        "location_title": alert.get("location_title"),
                        "started_at": alert.get("started_at"),
                        "alert_type": alert.get("alert_type"),
                        "alert_status": "active"
                    })

            if not filtered_alerts:
                return {"oblast": oblast, "alerts": [], "status": "no active alerts"}

            return {"oblast": oblast, "alerts": filtered_alerts}
        else:
            # Return all alerts with formatted data
            formatted_alerts = []
            for alert in active_alerts:
                formatted_alerts.append({
                    "location_title": alert.get("location_title"),
                    "started_at": alert.get("started_at"),
                    "alert_type": alert.get("alert_type"),
                    "alert_status": "active"
                })

            return {"alerts": formatted_alerts}

    except Exception as e:
        raise InvalidUsage(f"Error getting alerts data: {str(e)}", status_code=500)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Alert Service for Ukrainian Regions</h2></p>"


@app.route("/alerts", methods=["POST"])
def alerts_endpoint():
    json_data = request.get_json()

    if json_data.get("token") != API_TOKEN:
        raise InvalidUsage("Invalid API token", status_code=403)

    oblast = json_data.get("oblast")
    requester_name = json_data.get("requester_name")

    if not requester_name:
        raise InvalidUsage("Missing requester_name field", status_code=400)

    # Oblast is optional - if not provided, return all alerts
    alerts_data = get_alerts_data(oblast)

    result = {
        "requester": requester_name,
        "request_time": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "data": alerts_data
    }

    return jsonify(result)


@app.route("/alerts/all", methods=["GET"])
def all_alerts_endpoint():
    # Simple endpoint to get all alerts with token as query param
    token = request.args.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("Invalid API token", status_code=403)

    alerts_data = get_alerts_data()

    result = {
        "request_time": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "data": alerts_data
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Using a different port than weather service