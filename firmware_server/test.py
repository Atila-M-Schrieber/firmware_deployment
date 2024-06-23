import requests
from json import dumps as jsonify

# Testing done with requests for black box testing of APIs running in Docker
# Validation errors are not tested for - Pydantic is responsible server-side

base_url = "http://localhost:8000/firmware"

class EndpointTest:
    def __init__(self, name, endpoint, method, is_json, data,
                 expected_status, expected_response=None, files=None):
        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.is_json = is_json
        self.data = data
        self.expected_status = expected_status
        self.expected_response = expected_response
        self.files = files

    def test(self):
        url = f"{base_url}{self.endpoint}"
        try:
            if self.is_json:
                response = requests.request(self.method, url, json=self.data, files=self.files)
            else:
                response = requests.request(self.method, url, data=self.data, files=self.files)
            assert response.status_code == self.expected_status, "Bad status"
            if self.expected_response is not None:
                assert response.json() == self.expected_response, "Bad response"
            result = "passed"
            error = ""
        except AssertionError as e:
            result = "failed - assert"
            error = str(e)
        except Exception as e:
            result = "failed - error"
            error = str(e)
        
        return f"{self.name:<30} ... {result:<15} - {error}"

# Example good status request
good_status = EndpointTest(
    "Good status ping",
    "/status",
    "POST",
    True,
    {
        "firmware": "blinker",
        "version": "0.1.0",
        "id": "-1", # Reserved for testing, update=false
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
    True,
    {
        "firmware": "blinker",
        "version": "0.1.0",
        "id": "-2", # Reserved for testing, update=true
        "uptime": 100,
    },
    200,
    {"update": True}
)

# Example bad request
bad_status_id = EndpointTest(
    "Bad status ping - unknown ID",
    "/status",
    "POST",
    True,
    {
        "firmware": "blinker",
        "version": "0.1.0",
        "id": "0", # Reserved for testing, unknown ID
        "uptime": 100,
    },
    401,
    # "Unknown ID"
)

# Good upload
good_upload = EndpointTest(
    "Good upload",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
        "shasum": "TODO",
        "signature": "TODO",

    },
    200,
    None,
    { 'main.py': 'print("Hello World!")' }
)

# Bad upload - bad shasum
bad_upload_sha = EndpointTest(
    "Bad upload shasum",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
        "shasum": "TODO_BAD",
        "signature": "TODO",

    },
    422,
    None, # "Shasum does not match files.",
    { 'main.py': 'print("Hello World!")' }
)

# Bad upload - invalid signature
bad_upload_sign = EndpointTest(
    "Bad upload signature",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
        "shasum": "TODO",
        "signature": "TODO_BAD",

    },
    401,
    None, # "Invalid or unknown signature",
    { 'main.py': 'print("Hello World!")' }
)

# Bad upload - no files
bad_upload_no_files = EndpointTest(
    "Bad upload - no files",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
        "shasum": "TODO",
        "signature": "TODO",

    },
    400,
    # "No files found"
)

tests = [
    good_status,
    good_status_update,
    bad_status_id,
    good_upload,
    bad_upload_sha,
    bad_upload_sign,
    bad_upload_no_files,
    # good_update_order,
    # bad_update_order_sign,
    # good_rollback_order,
    # bad_rollback_order_sign,
    # good_update_request,
    # bad_update_request_id,
]

for test in tests:
    print(test.test())
