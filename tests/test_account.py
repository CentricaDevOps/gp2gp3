"""gp2gp3 pkg AWS Account module tests."""

import os

import pytest

import chalicelib.account as act


# def test_acctalias():
#     alias = act.getAccountAlias(profile="sdev")
#     # print(f"alias is {alias}")
#     # assert True is False
#     assert alias == "hsre-dev"


def test_getParams():
    os.environ["AWS_PROFILE"] = "awsbilling"
    server = "dev_test"
    base = f"/service_now/{server}"
    plist = [
        f"{base}/host",
        f"{base}/username",
        f"{base}/password",
        f"{base}/template_id",
    ]
    prams = act.getParams(plist)
    assert len(prams) == 4


def test_getParamHost():
    os.environ["AWS_PROFILE"] = "awsbilling"
    server = "dev_test"
    base = f"/service_now/{server}"
    plist = [
        f"{base}/host",
        f"{base}/username",
        f"{base}/password",
        f"{base}/template_id",
    ]
    gprams = {}
    prams = act.getParams(plist)
    for pram in prams:
        tmp = pram["Name"].split("/")
        gprams[tmp[-1]] = pram["Value"]
    assert gprams["host"] == "csmpmdev.service-now.com"
