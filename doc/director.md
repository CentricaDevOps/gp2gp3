# Director Lambda for GP2 => GP3 Transition Process

The director lambda invokes a worker per child account in the AWS Organisation.

This function is in file [chalicelib/primary.py](../chalicelib/primary.py)
```python
def doPrimary():
    """Director code:

    retrieves list of organisation accounts
    retrieves list of enabled regions
    invokes one worker lambda per account
    """

    # TTL for use if updating a DDB Table
    tomorrow = int(time.time()) + (3600 * 23) + (45 * 60)  # 23 hrs and 45 minutes

    # retrieve the list of child accounts in the AWS Organisation
    oacctids = act.getAccountIdsOrg()

    # pull out the account id for each account into a list
    acctids = [x["Id"] for x in oacctids if x["Status"] == "ACTIVE"]

    # retrieve the list of enabled regions
    regions = act.getRegions()

    # get a flag from the environment to report or report and transition
    dotransition = os.environ.get("TRANSITIONVOLUMES", "false")

    # make a boto3 lambda client
    lam = act.getClient("lambda")

    # retrieve the worker lambda function arn that we wish to invoke
    seclambdaarn = os.environ.get("SECONDARYLAMBDA", "NOTSET")

    # test our inputs
    if seclambdaarn == "NOTSET":
        raise Exception("Secondary lambda arn not set in the environment under the key SECONDARYLAMBDA")
    if acctids is None:
        raise Exception("Failed to obtain any account ids.")

    # set some standard arguments into the keyword arguments dictionary
    kwargs = {
        "FunctionName": f"{seclambdaarn}",
        "InvocationType": "Event",
    }

    # counter for failed invocations
    fnc = 0

    # for each account keep count and invoke the worker lambda
    for cn, acct in enumerate(acctids, start=1):
        # build the dictionary that gets passed to the worker as the event.
        xdict = {
            "acctnum": acct,
            "regions": regions,
            "tomorrow": tomorrow,
            "transitionvolumes": os.environ.get("TRANSITIONVOLUMES", "false"),
        }

        # set the event dict. as the payload argument to the worker lambda
        kwargs["Payload"] = json.dumps(xdict)

        # invoke the worker and test that it started correctly
        res = lam.invoke(**kwargs)
        if res["StatusCode"] != 202:
            # note if it didn't start for a particular account
            print(f"Failed to launch {seclambaarn} in account {acctid}")
            fnc += 1

    # log result of workers started and workers that failed to start
    print(f"{fnc} secondaries failed to run, {cn-fnc} started successfully")
```

[Back to Code](code.md)
