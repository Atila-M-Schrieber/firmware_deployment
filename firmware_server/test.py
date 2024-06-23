import requests
import json

# Testing done with requests for black box testing of APIs running in Docker

base_url = "http://localhost:8000/firmware"

class EndpointTest:
    def __init__(self, name, endpoint, method, json, expected_status, expected_response=None):
        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.json = json
        self.expected_status = expected_status
        self.expected_response = expected_response

    def test(self):
        url = f"{base_url}{self.endpoint}"
        try:
            response = requests.request(self.method, url, json=self.json)
            assert response.status_code == self.expected_status
            if self.expected_response is not None:
                assert response.json() == self.expected_response
            result = "passed"
            error = ""
        except AssertionError as e:
            result = "failed - assert"
            error = str(e)
        except Exception as e:
            result = "failed - error"
            error = str(e)
        
        return f"{self.name:<50} ... {result:<20} {error}"

# Example good status request
good_status = EndpointTest(
    "Good status ping",
    "/status",
    "POST",
    {
        "firmware": "blinker",
        "version": "0.1.0",
        "id": -1, # Reserved for testing, update=false
        "uptime": 100,
    },
    200,
    {"update": False}
)

# Example good status request with update
good_status_update = EndpointTest(
    "Good status ping - update",
    "/status",
    "POST",
    {
        "firmware": "blinker",
        "version": "0.1.0",
        "id": -2, # Reserved for testing, update=true
        "uptime": 100,
    },
    200,
    {"update": True}
)

tests = [
    good_status,
    good_status_update,
]

for test in tests:
    print(test.test())
