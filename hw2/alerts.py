from alerts_in_ua import Client as AlertsClient

alerts_client = AlertsClient(token="***REMOVED***")
active_alerts = alerts_client.get_active_alerts()
# print(alerts_client.get_alerts_history("Kyiv"))
print(active_alerts)
