"""Tests for the gp2gp3.secondary module."""

import pytest

import gp2gp3.volumes as vl


def test_getGPVols():
    vols = vl.getGPVols("sdev", "eu-west-1")
    # print(f"len gp2/3 vols: {len(vols)}")
    # for vol in vols:
    #     print(f"""{vol["VolumeId"]}: {vol["VolumeType"]}""")
    # assert True is False
    assert type(vols) is list
