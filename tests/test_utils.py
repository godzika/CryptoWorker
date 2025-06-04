import pytest
from utils import validate_eth_address, to_wei, from_wei, call_callback_url

def test_validate_eth_address_valid():
    # Valid Ethereum address
    assert validate_eth_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e") is True

def test_validate_eth_address_invalid():
    # Invalid address
    assert validate_eth_address("0x1234") is False

def test_to_wei_and_from_wei():
    assert to_wei(1) == 10**18
    assert from_wei(10**18) == 1

def test_call_callback_url_success(requests_mock):
    url = "http://test.com/callback"
    requests_mock.post(url, status_code=200)
    assert call_callback_url(url, {"foo": "bar"}) is True

def test_call_callback_url_fail(requests_mock):
    url = "http://test.com/callback"
    requests_mock.post(url, status_code=500)
    assert call_callback_url(url, {"foo": "bar"}, retries=2) is False
