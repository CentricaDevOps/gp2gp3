#
# Copyright (c) 2021, Centrica PLC.
#
#     This file is part of gp2gp3.
#
#     gp2gp3 is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     gp2gp3 is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with gp2gp3.  If not, see <http://www.gnu.org/licenses/>.
#
"""Service-Now routines for the gp2gp3 project."""

import sys

import requests

import chalicelib.account as act

GPRAMS = {}


def setupParameters(server="dev_test"):
    try:
        global GPRAMS
        base = f"/service_now/{server}"
        plist = [
            f"{base}/host",
            f"{base}/username",
            f"{base}/password",
            f"{base}/template_id",
        ]
        prams = act.getParams(plist)
        for pram in prams:
            tmp = pram["Name"].split("/")
            GPRAMS[tmp[-1]] = pram["Value"]
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getBaseUrl(server="dev_test"):
    try:
        global GPRAMS
        if len(GPRAMS) == 0:
            setupParameters(server="dev_test")
        url = f'https://{GPRAMS["host"]}/api/sn_chg_rest/change/standard'
        return url
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def newChangeRequest():
    try:
        global GPRAMS
        if len(GPRAMS) == 0:
            setupParameters(server="dev_test")
        url = f'https://{GPRAMS["host"]}/api/sn_chg_rest/change/standard/{GPRAMS["template_id"]}'
        # resp = requests.get(url, auth=(f'GPRAMS["username"]}', f'GPRAMS["password"]}')
        return url
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise
