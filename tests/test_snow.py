"""gp2gp3 pkg AWS snow module tests."""

import pytest

import chalicelib.account as act
import chalicelib.snow as snw


def test_getURL():
    url = snw.getBaseUrl(server="dev_test")
    assert url == "https://csmpmdev.service-now.com/api/sn_chg_rest/change/standard"


def test_newChangeRequest():
    url = snw.newChangeRequest()
    assert (
        url
        == "https://csmpmdev.service-now.com/api/sn_chg_rest/change/standard/4aaa54eedb3390106f5426f35b961994"
    )
