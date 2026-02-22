import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://www.visualcrossing.com/weather-api
RSA_KEY = ""

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


def generate_weather(location: str, date: str):
    url_base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

    url = f"{url_base_url}/{location}/{date}"

    parameters = {"unitGroup": "metric",
                  "key": RSA_KEY,
                  "include": "days",
                  }

    response = requests.get(url, params=parameters)

    if response.status_code == requests.codes.ok:
        data = json.loads(response.text)
        day_data = data["days"][0]

        weather = {
            "temp_c": day_data.get("temp"),
            "wind_kph": day_data.get("windspeed"),
            "pressure_mb": day_data.get("pressure"),
            "humidity": day_data.get("humidity"),
            "conditions": day_data.get("conditions"),
            "cloudcover": day_data.get("cloudcover")
        }

        return weather
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA H1: python weather Saas.</h2></p>"


@app.route("/content/api/v1/integration/generate", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    if json_data.get("requester_name") is None:
        raise InvalidUsage("requester_name is required", 400)

    if json_data.get("location") is None:
        raise InvalidUsage("location is required", 400)

    if json_data.get("date") is None:
        raise InvalidUsage("date is required", 400)
    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    requester_name = json_data.get("requester_name")
    location = json_data.get("location")
    date = json_data.get("date")
    weather = generate_weather(location, date)

    end_dt = dt.datetime.now()

    result = {
        "requester_name": requester_name,
        "timestamp": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": weather
    }

    return result
