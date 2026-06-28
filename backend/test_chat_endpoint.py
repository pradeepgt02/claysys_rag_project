import requests

try:
    res = requests.post("http://127.0.0.1:8000/chat", json={
        "website_id": "python_org_1595931a",
        "question": "What is this website about?"
    })
    print(res.status_code)
    print(res.text)
except Exception as e:
    print("Error:", e)
