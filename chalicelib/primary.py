"""Primary Lambda function for the gp2gp3 package."""

import json
import os
import sys
import time

import chalicelib.account as act


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
