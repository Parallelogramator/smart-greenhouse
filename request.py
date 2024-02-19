import requests

print(requests.post('http://127.0.0.1:5000/update_data', json={'temperature': 22, 'humidity': 50, 'humidity_earth': 14}, headers={'Content-Type': 'application/json'}))