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
            elif pram["Name"] == "/src/wavefront/directingest":
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


def doPrimary():
    """Director code:

    retrieves list of organisation accounts
    retrieves list of enabled regions
    invokes one worker lambda per account
    """
    try:
        tomorrow = int(time.time()) + (3600 * 23) + (45 * 60)  # 23 hrs and 45 minutes
        oacctids = act.getAccountIdsOrg()
        acctids = [x["Id"] for x in oacctids if x["Status"] == "ACTIVE"]
        regions = act.getRegions()
        dotransition = os.environ.get("TRANSITIONVOLUMES", "false")
        lam = act.getClient("lambda")
        snowsrv = os.environ.get("SNOWSERVER", "dev_test")
        prams = setupParameters(snowsrv)
        seclambdaarn = os.environ.get("SECONDARYLAMBDA", "NOTSET")
        if seclambdaarn == "NOTSET":
            raise Exception(
                "Secondary lambda arn not set in the environment under the key SECONDARYLAMBDA"
            )
        if acctids is None:
            raise Exception("Failed to obtain any account ids.")
        kwargs = {
            "FunctionName": f"{seclambdaarn}",
            "InvocationType": "Event",
        }
        fnc = 0
        for cn, acct in enumerate(acctids, start=1):
            xdict = {
                "acctnum": acct,
                "regions": regions,
                "tomorrow": tomorrow,
                "transitionvolumes": os.environ.get("TRANSITIONVOLUMES", "false"),
            }
            xdict.update(prams)
            kwargs["Payload"] = json.dumps(xdict)
            res = lam.invoke(**kwargs)
            if res["StatusCode"] != 202:
                print(f"Failed to launch {seclambaarn} in account {acctid}")
                fnc += 1
        print(f"{fnc} secondaries failed to run, {cn-fnc} started successfully")
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise
