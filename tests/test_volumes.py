"""Tests for the gp2gp3.volumes module."""

import sys

import pytest

import chalicelib.volumes as vl


def test_getVolumes():
    """This will test the addIfNotNone, getSession, getClient and getVolumes functions."""
    vols = vl.getVolumes("sdev", "eu-west-1")
    # print(f"len all vols: {len(vols)}")
    # for vol in vols:
    #     print(f"""{vol["VolumeId"]}: {vol["VolumeType"]}""")
    # assert True is False
    assert type(vols) is list
