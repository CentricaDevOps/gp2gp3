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
"""Primary Lambda function for the gp2gp3 package."""

import json
import os
import sys
import time

import chalicelib.account as act


def setupParameters(server="dev_test"):
    try:
        gprams = {}
        base = f"/service_now/{server}"
        plist = [
            "/sre/wavefront/directingest",
            f"{base}/host",
            f"{base}/username",
            f"{base}/password",
            f"{base}/template_id",
        ]
        prams = act.getParams(plist)
        for pram in prams:
            if pram["Name"].startswith(base):
                tmp = pram["Name"].split("/")
                gprams[tmp[-1]] = pram["Value"]
            elif pram["Name"] == "/sre/wavefront/directingest":
                gprams["wfkey"] = pram["Value"]
            else:
                raise Exception(f"Unknown param returned: {pram}")
        return gprams
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getAIDs():
    try:
        allids = [x["Id"] for x in act.getAccountIdsOrg() if x["Status"] == "ACTIVE"]
        onlyaccts = os.environ.get("ONLYACCOUNTS", "NOTSET")
        tids = (
            [x.strip() for x in onlyaccts.split(",")] if onlyaccts != "NOTSET" else []
        )
        reportids = [x for x in allids if x not in tids]
        return (reportids, tids)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def doPrimary():
    """Director code:

    retrieves list of organisation accounts
    retrieves list of enabled regions
    invokes one worker lambda per account
    """
    try:
        tomorrow = int(time.time()) + (3600 * 23) + (45 * 60)  # 23 hrs and 45 minutes
        reportids, tids = getAIDs()
        # oacctids = act.getAccountIdsOrg()
        # accts = os.environ.get("ONLYACCOUNTS", "NOTSET")
        # if accts == "NOTSET":
        #     acctids = [x["Id"] for x in oacctids if x["Status"] == "ACTIVE"]
        # else:
        #     acctids = [x.strip() for x in accts.split(",")]
        regions = act.getRegions()
        lam = act.getClient("lambda")
        snowsrv = os.environ.get("SNOWSRV", "dev_test")
        prams = setupParameters(snowsrv)
        seclambdaarn = os.environ.get("SECONDARYLAMBDA", "NOTSET")
        if seclambdaarn == "NOTSET":
            raise Exception(
                "Secondary lambda arn not set in the environment under the key SECONDARYLAMBDA"
            )
        if reportids is None:
            raise Exception("Failed to obtain any account ids.")
        if tids is None:
            raise Exception("Failed to obtain account ids from environment")
        kwargs = {
            "FunctionName": f"{seclambdaarn}",
            "InvocationType": "Event",
        }
        adict = {
            "regions": regions,
            "tomorrow": tomorrow,
            "transitionvolumes": "fales",
            "oldestfirst": os.environ.get("OLDESTFIRST", "true").lower(),
            "ignoredisks": os.environ.get("IGNOREDISKS", "999"),
        }
        fnc = 0
        rn = 0
        tn = 0
        for acct in reportids:
            if doLaunch(lam, acct, adict, prams, kwargs):
                rn += 1
            else:
                fnc += 1
        adict["transitionvolumes"] = os.environ.get(
            "TRANSITIONVOLUMES", "false"
        ).lower()
        for acct in tids:
            if doLaunch(lam, acct, adict, prams, kwargs):
                tn += 1
            else:
                fnc += 1
        print(
            f"{fnc} secondaries failed to run, {rn} reporters started successfully, {tn} transitioners started successfully."
        )
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def doLaunch(lam, acct, adict, prams, kwargs):
    try:
        xdict = {
            "acctnum": acct,
        }
        xdict.update(adict)
        xdict.update(prams)
        # print(f"xdict: {xdict}")
        kwargs["Payload"] = json.dumps(xdict)
        res = lam.invoke(**kwargs)
        if res["StatusCode"] != 202:
            print(f'Failed to launch {kwargs["FunctionName"]} in account {acct}.')
            return False
        return True
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise
