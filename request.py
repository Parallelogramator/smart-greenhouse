import requests, datetime, json
print(datetime.date.today().strftime('%Y-%m-%d'))
print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
'''print(requests.post('http://127.0.0.1:5000/update_data',
                    json={'temperature': 50, 'humidity': 0, 'humidity_earth': 0, 'key': 1},
                    headers={'Content-Type': 'application/json'}))'''
a = requests.post('http://127.0.0.1:5000/auth',
                    json={'mac': '11:30:72:33:49:51', 'key': 0}
                    )
print(a)
print(a.text)

'''def get_weather():
    response = requests.get(
        f"http://api.weatherapi.com/v1/forecast.json?&q=Moscow&days=1&aqi=yes&alerts=no&lang=ru&key=e6445624d3694167836183224242603")
    data = response.json()
    print(data['forecast']['forecastday'][0]['hour'][int(datetime.datetime.now().strftime('%H'))])
    with open('weather.json', 'w') as f:
        json.dump(data, f)


print(get_weather())
'''
