import requests

base = "http://127.0.0.1:5000/"
api_key = "x{lhtTaQz58QJ7ZK;a~`/t!:D"
res = requests.post(base + "api/signup",
    json={"username": "eastbo3", "password": "noah3", "api_key": api_key}
)
json_response = res.json()
print (json_response)
