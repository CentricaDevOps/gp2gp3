"""gp2gp3 pkg AWS Account module tests."""

import pytest

from gp2gp3.account import getAccountAlias


def test_acctalias():
    alias = getAccountAlias(profile="sdev")
    # print(f"alias is {alias}")
    # assert True is False
    assert alias == "hsre-dev"
