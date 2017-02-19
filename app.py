#!/usr/bin/env python

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import urllib.request, urllib.parse, urllib.error
import requests
import json
import os
import time

from sanic import Sanic
from sanic.response import json

# Flask app should start in global layout
app = Sanic()

automateResponse = ""

@app.route('/webhook', methods=['POST'])
async def webhook(request):
    req = request.json

    print("Webhook Request:")
    print(req)
    
    action = req.get("result").get("action")

    if action == "yahooWeatherForecast":
        res = processRequest(req)
    else:
        forwardToAutomate(req)
        print("Waiting for response")
        time.sleep(4)
        print("Done waiting")
        res = automateResponse
    
    print("Response:")
    print(res)
    r = res
    print("Responded")
    return json(r)

@app.route('/automate', methods=['POST'])
async def automate(request):
    req = request.json
    print("Automate Request:")
    print(req)
    automateResponse = req
    

def forwardToAutomate(req):
    print("Forwarding to Automate...")
    result = req.get("result")
    action = result.get("action")
    parameters = result.get("parameters")
    
    payload = action + "=" + parameters
    
    data = {"secret": "1.mrxBipl3kqI0jptezLOa78IWjPvmoNi1wHeAeYYjyA4=",
           "to": "groupwise.cmadison@gmail.com",
           "payload": payload}
    print(data)
    
    baseurl = "https://llamalab.com/automate/cloud/message"
    requests.post(baseurl, json=data)


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urllib.parse.urlencode({'q': yql_query}) + "&format=json"
    result = urllib.request.urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(host='0.0.0.0', port=port)
