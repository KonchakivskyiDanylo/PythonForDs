import os
from dotenv import load_dotenv
from alerts_in_ua import Client as AlertsClient


def load_api_token() -> str:
    load_dotenv()
    token = os.getenv("ALERTS_API_TOKEN")

    if not token:
        raise EnvironmentError("Missing ALERTS_API_TOKEN. Please set it in the .env file.")

    return token


def fetch_active_alerts(token: str):
    try:
        alerts_client = AlertsClient(token=token)
        active_alerts = alerts_client.get_active_alerts()

        return [getattr(alert, "location_title", "Unknown").replace(" область", "") for alert in active_alerts]


    except Exception as e:
        raise RuntimeError(f"Error getting alerts data: {str(e)}")


def main():
    try:
        token = load_api_token()
        alerts = fetch_active_alerts(token)
        return alerts

    except (EnvironmentError, RuntimeError) as e:
        print(str(e))
        return None


if __name__ == "__main__":
    main()
