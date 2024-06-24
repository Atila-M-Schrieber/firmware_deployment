import requests
import os

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
            error = None
        except AssertionError as e:
            result = "failed - assert"
            error = str(e)
        except Exception as e:
            result = "failed - error"
            error = str(e)
        
        return f"{self.name:<30} ... {result:<15}" + ("" if not error else f" - {error}")

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

with open("../firmware/test-1.0.0/main.py", 'r') as f:
    main_text = f.read()
with open("../firmware/test-1.0.0/thing.py", 'r') as f:
    thing_text = f.read()
with open("../firmware/test_sig.asc", 'r') as f:
    sig = f.read()

# Good upload
good_upload = EndpointTest(
    "Good upload",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    200,
    None,
    {
        'main.py': main_text,
        'thing.py': thing_text,
        'sig.asc': sig
    }
)

# Flips the first char's case after a / in the signature, therefore invalidating it (generated)
bad_sig = '\n'.join([''.join([ch.swapcase() if (i > 0 and line[i-1] == '/')
                              else ch for i, ch in enumerate(line)]) for line in sig.split('\n')])

# Bad upload - invalid signature
bad_upload_sign = EndpointTest(
    "Bad upload signature",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    401,
    None, # "Invalid or unknown signature",
    {
        'main.py': main_text,
        'thing.py': thing_text,
        'sig.asc': bad_sig
    }
)

# Bad upload - missing signature
bad_upload_no_sig = EndpointTest(
    "Bad upload missing signature",
    "/upload",
    "PUT",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    422,
    None,
    {
        'main.py': 'import thing\nprint("Hello World!")',
        'thing.py': 'print("Hello Thing!")',
    }
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
    },
    400,
    # "No files found"
)

# Good firmware info request
good_firmware_info = EndpointTest(
    "Good firmware info request",
    "",
    "GET",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    200,
    {}
)

# Good firmware info request
bad_firmware_info_just_version = EndpointTest(
    "Bad fwinfo - just version",
    "",
    "GET",
    False,
    {
        "version": "1.0.0",
    },
    400,
    # Only version given...
)

tests = [
    good_status,
    good_status_update,
    bad_status_id,
    good_upload,
    bad_upload_sign,
    bad_upload_no_sig,
    bad_upload_no_files,
    good_firmware_info,
    bad_firmware_info_just_version,
    # good_update_order,
    # bad_update_order_sign,
    # good_rollback_order,
    # bad_rollback_order_sign,
    # good_update_request,
    # bad_update_request_id,
]

for test in tests:
    print(test.test())
