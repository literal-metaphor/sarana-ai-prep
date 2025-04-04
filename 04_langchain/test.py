import requests

response = requests.post("http://localhost:8000/", files={"file": open("./bittensor.pdf", "rb")}, stream=True)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))