import requests

session = requests.Session()

response1 = session.post("http://localhost:8000/", json={"messages": [{"role": "user", "content": "Hello, how are you?"}]}, stream=True)
response2 = session.post("http://localhost:8000/", json={"messages": [{"role": "user", "content": "So, what can you do?"}]}, stream=True)
response3 = session.post("http://localhost:8000/", json={"messages": [{"role": "user", "content": "Tell me more about the British Empire."}]}, stream=True)
response4 = session.post("http://localhost:8000/", json={"messages": [{"role": "user", "content": "Rewrite the history of our conversation so far."}]}, stream=True)

for response in [response1, response2, response3, response4]:
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))