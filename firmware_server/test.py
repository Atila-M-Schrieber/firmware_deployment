import requests
import pgpy
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
        
        return f"{self.name:<35} ... {result:<15}" + ("" if not error else f" - {error}")

# Example good status request
good_status = EndpointTest(
    "Good status ping",
    "/status",
    "POST",
    True,
    {
        "firmware": "blinker",
        "version": "0.1.0",
        "board_id": "-1", # Reserved for testing, update=false
        "uptime": 100,
    },
    200,
    {}
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
        "board_id": "-2", # Reserved for testing, update=true
        "uptime": 100,
    },
    200,
    {"update": True, "secret": "test_secret"}
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
        "board_id": "0", # Reserved for testing, unknown ID
        "uptime": 100,
    },
    401,
    # "Unknown ID"
)


with open("../firmware/test-1.0.0/main.py", 'r') as f:
    main_text = f.read()
with open("../firmware/test-1.0.0/thing.py", 'r') as f:
    thing_text = f.read()
priv_key, _ = pgpy.PGPKey.from_file("../firmware/private.asc")
priv_key.unlock('')
pub_key, _ = pgpy.PGPKey.from_file("../firmware/public.asc")
sig = str(priv_key.sign(main_text + thing_text))

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

# Sign something else
bad_sig = str(priv_key.sign(main_text + thing_text + "lol"))

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

# Bad firmware info request - only the version provided, not the name
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


order_dict = {
    "firmware": "test",
    "version": "1.0.0",
    "board_id": "test_id"
}
# Signature signs fw_name-version-board_id, ie: test-1.0.0-test_id - just like
# the whole firmware directory, except with the -board_id added as a target
def gen_order_sig(bad_fw=None, bad_ver=None, bad_id=None, bad_sig=None):
    o_d = order_dict.copy()
    if bad_fw:
        o_d['firmware'] = bad_fw
    if bad_ver:
        o_d['version'] = bad_ver
    if bad_id:
        o_d['board_id'] = bad_id
    return str(priv_key.sign(
        # adding bad_sig in text - not signing the right text
        f"{o_d['firmware']}-{o_d['version']}-{o_d['board_id']}{bad_sig if bad_sig else ""}"
    ))

# Good update order
good_update_order = EndpointTest(
    "Good update order",
    f"/update/{order_dict['board_id']}",
    "POST",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    200,
    None,
    {
        'sig.asc': gen_order_sig()
    }
)

# Bad update order - nonexistent firmware
bad_update_order_no_firmware = EndpointTest(
    "Bad u. order - no such firmware",
    f"/update/{order_dict['board_id']}",
    "POST",
    False,
    {
        "firmware": "bad_test",
        "version": "1.0.0",
    },
    404,
    None, # Firmware 'bad_test' not found
    {
        'sig.asc': gen_order_sig(bad_fw="bad_test")
    }
)

# Bad update order - nonexistent version
bad_update_order_no_version = EndpointTest(
    "Bad u. order - no such version",
    f"/update/{order_dict['board_id']}",
    "POST",
    False,
    {
        "firmware": "test",
        "version": "10000.0.0",
    },
    404,
    None, # Firmware 'test-10000.0.0' not found, firmware 'test' versions: ...
    {
        'sig.asc': gen_order_sig(bad_ver="10000.0.0")
    }
)

# Bad update order - unknown ID
bad_update_order_unknown_id = EndpointTest(
    "Bad u. order - unknown board ID",
    f"/update/bad_{order_dict['board_id']}",
    "POST",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    404,
    None, # Board id unknown / not found
    {
        'sig.asc': gen_order_sig(bad_id=f"bad_{order_dict['board_id']}")
    }
)

# Bad update order - invalid signature
bad_update_order_sign = EndpointTest(
    "Bad u. order - invalid signature",
    f"/update/{order_dict['board_id']}",
    "POST",
    False,
    {
        "firmware": "test",
        "version": "1.0.0",
    },
    401,
    None, # Invalid signature
    {
        'sig.asc': gen_order_sig(bad_sig="lol")
    }
)


# Good update request from board
good_update_request = EndpointTest(
    "Good update request",
    f"/update/-2",
    "GET",
    True,
    {
        "firmware": "test",
        "version": "1.0.0",
        "board_id": "-2",
        "secret": "test_secret"
    },
    200,
    None,
)

# Bad update request - known ID but no update order
bad_update_request_id = EndpointTest(
    "Bad u. req. - known ID - no u. order",
    f"/update/-1",
    "GET",
    True,
    {
        "firmware": "test",
        "version": "1.0.0",
        "board_id": "-1",
        "secret": "test_secret"
    },
    406,
    None, # Known ID, but no update ordered
)

# Bad update request - bad secret
bad_update_request_secret = EndpointTest(
    "Bad u. req. - u. order but bad secret",
    f"/update/-2",
    "GET",
    True,
    {
        "firmware": "test",
        "version": "1.0.0",
        "board_id": "-2",
        "secret": "bad_test_secret"
    },
    403,
    None, # Known ID, update ordered, but bad secet
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
    good_update_order,
    bad_update_order_no_firmware,
    bad_update_order_no_version,
    bad_update_order_unknown_id,
    bad_update_order_sign,
    good_update_request,
    bad_update_request_id,
    bad_update_request_secret,
]

for test in tests:
    print(test.test())
