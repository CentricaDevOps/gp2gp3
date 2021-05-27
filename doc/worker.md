# Worker Code for GP2 => GP3 Transition Process

A simple lambda function that starts a worker per region, returning data on the
Q.

This function is in file [chalicelib/secondary.py](../chalicelib/secondary.py)
```python
def secondaryLF(event, context):
    # test that we have the required keys in the event dictionary
    reqkeys = ["regions", "acctnum", "tomorrow", "transitionvolumes"]
    testKeys(reqkeys, event)

    # split the region string into a list of regions
    regions = event["regions"].split(",")

    # retrieve the account number from the event dict.
    acctnum = event["acctnum"]

    # grab the role to assume from the environment
    rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")

    # assume the role and ask the AWS API for the friendly account name
    acctname = act.assumeRoleAlias(rolename, acctnum, "eu-west-1")

    # set a flag to transition volumes or just report the number of gp2 vols.
    dotransition = False
    if event["transitionvolumes"] == "true":
        dotransition = True

    # create a Q
    Q = queue.Queue()

    # create a list of threads
    threads = []

    # standard arguments to pass into each thread
    gargs = [acctname, acctnum, tomorrow, Q, dotransition]

    # create each thread - one per region
    for xcn, region in enumerate(regions, start=1):
        # add the region name and the thread number to the list of arguments
        targs = [region, xcn]
        targs.extend(gargs)

        # create the thread for this region
        thread = threading.Thread(target=volsInRegion, args=targs)

        # add this thread to the list of threads
        threads.append(thread)

    # start each thread
    [x.start() for x in threads]

    # wait for each thread to complete
    [x.join() for x in threads]

    # test whether we have data from each region (the threads share the same Q)
    cn = Q.qsize()

    # log the numbers.
    if cn > 0:
        print(f"{acctnum} {acctname}: {cn} volumes left to transition")
    else:
        print(f"{acctnum} {acctname}: No volumes to transition at this time.")
```


This function is called for each thread (remember, one thread per region). The
resulting list of gp2 volumes are placed onto a global queue.


```python
def volsInRegion(region, logid, acctname, acctnum, ttl, Q, dotransition=False):
    """Retrieve list of all gp2/gp3 volumes in the region.

    Test to see if any of the gp3 volumes are still transitioning
    If not, pick a gp2 volume and attempt to transition it
    If that fails move to the next gp2 volume and so on
    """
    # common details for all volumes
    std = {"region": region, "acctname": acctname, "acctnum": acctnum, "ttl": ttl}

    # this returns a tuple of 2 lists (gp2-volumes, gp3-vol-in-transition)
    vols, gp3wait = vl.getGPVols(
        acctid=acctnum, acctname=acctname, region=region, logid=logid
    )

    # boolean to show whether we have yet to pick a gp2 volume
    picked = False

    # is the last gp3 transition still in progress?
    if gp3wait is not None:
        print(
            f"""{acctnum} {acctname} {region}: Volume: {gp3wait["volid"]} in region: {gp3wait["region"]} is transitioning, {gp3wait["progress"]}% complete, waiting..."""
        )
        # finish this thread early, as the last volume hasn't yet completed it's transition
        return

    # check each gp2 volume
    for vol in vols:

        # test that we can go ahead
        if checkCanDoTransition(dotransition, picked, vol["State"]):

            # ask the api to transition the volume to gp3
            if vl.transitionVolume(vol["VolumeId"], acctid=acctnum, region=region, logid=logid):

                # transition started, report that to the log
                print(f"""{logid}: {acctnum} {acctname} {region}: Transitioning {vol["VolumeId"]} from gp2 to gp3""")
                picked = True

            else:

                # hmm, the request failed
                print(
                    f"""{logid}: {acctnum} {acctname} {region}: Failed to start transitioning volume {vol["VolumeId"]}."""
                )
                # add the common values to the volume
                vol.update(std)
                # pop the volume onto the Q
                Q.put(vol)
        else:

            # add the common values to the volume
            vol.update(std)
            # pop the volume onto the Q
            Q.put(vol)
```

[Back to Code](code.md)
