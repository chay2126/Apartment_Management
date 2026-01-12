import requests

TOKEN = "8493019914:AAF4lR6K5auN_foC3XbJlS1OfNXtzpbKDqM"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
response = requests.get(url)
print(response.json())
