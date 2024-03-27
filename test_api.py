import requests
import json

url = "https://api.caresoft.vn/scidemo/api/v1/search"

data = {
    "params": {
        "ticket_status": "open",
        "update_since": "2021-08-01T00:00:00Z",
        "custom_fields": [
            {
                "field_id": 5668,
                "field_value": 76214
            }
        ]
    }
}
headers = {
    'Authorization': 'Bearer AniWsZEju0ur_qc',
    'Content-Type': 'application/json'
}

r = requests.post(url, data=json.dumps(data), headers=headers)
response = r.json()
print(response)
