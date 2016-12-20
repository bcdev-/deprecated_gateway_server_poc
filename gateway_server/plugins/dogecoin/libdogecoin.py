from unittest import TestCase
from requests import post
from requests.auth import HTTPBasicAuth
from common.settings import dogecoin_api_username, dogecoin_api_password, dogecoin_api_url
import simplejson as json


def get_new_address():
    payload = {
        "method": "getnewaddress",
        "params": []
    }
    r = post(dogecoin_api_url, auth=HTTPBasicAuth(dogecoin_api_username, dogecoin_api_password),
             data=json.dumps(payload))
    return r.json()['result']


def validate_address(address):
    payload = {
        "method": "validateaddress",
        "params": [address]
    }
    r = post(dogecoin_api_url, auth=HTTPBasicAuth(dogecoin_api_username, dogecoin_api_password),
             data=json.dumps(payload))
    return r.json()['result']['isvalid']


def get_last_transactions(number=1000000, starting_from=0):
    payload = {
        "method": "listtransactions",
        "params": ["", number, starting_from]
    }
    r = post(dogecoin_api_url, auth=HTTPBasicAuth(dogecoin_api_username, dogecoin_api_password),
             data=json.dumps(payload))

    return json.loads(r.text, use_decimal=True)['result']


class Test(TestCase):
    def test_addresses(self):
        addr1 = get_new_address()
        addr2 = get_new_address()
        addr3 = get_new_address()
        self.assertTrue(validate_address(addr1))
        self.assertTrue(validate_address(addr2))
        self.assertTrue(validate_address(addr3))
        if addr3[-1] == 'a':
            addr4 = addr3[:-1] + 'b'
        else:
            addr4 = addr3[:-1] + 'a'
        self.assertFalse(validate_address(addr4))
