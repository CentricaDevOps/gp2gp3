# Code to Transition GP2 => GP3

## Make Lists of both types of Volume in a Region

The meat of the process are these four functions, these are run together on a
thread per region, for one particular account.

```python
def getVolumes(acctid=None, region="eu-west-1", filters=None, logid=0):
    """Obtain a list of volumes in the specified account/region."""

    # setup
    volumes = []
    rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")

    # assume the role, create a boto3 ec2 client
    ec2 = acct.assumeRoleEC2(rolename, acctid, region, logid)

    # add filters to the describe_volumes api call if necessary
    kwargs = acct.addIfNotNone({}, filters, "Filters")
    try:
        while True:

            # retrieve (a partial) list of volumes
            vols = ec2.describe_volumes(**kwargs)

            # add the (partial) list to the master list of volumes
            volumes.extend(vols.get("Volumes"))

            # check if there are more volumes to retrieve
            if "NextToken" in vols and vols["NextToken"]:
                kwargs["NextToken"] = vols["NextToken"]
            else:
                break

    # These exceptions check if the required region is denied via an SCP (ClientError Exception)
    # or for any other reason (API Unauthorized exception)
    except botocore.exceptions.ClientError as e:
        print(f"region {region} not enabled (clienterror)")
    except botocore.exceptions.UnauthorizedOperation as e:
        print(f"region {region} not enabled (unauthorised)")

    # return the list of found volumes to the caller
    return volumes
```

The above function accepts an account number `acctid`, the region to investigate, any filters and a thread identifier `logid`.

This function filters out any volume that isn't a gp2/3 volume type, reports the count of both types to Wavefront and returns the
list of gp2 volumes along with any gp3 volume that is still in the transition state.
```python
def getGPVols(acctid=None, acctname="", region="eu-west-1", logid=0):
    """Retrieve gp2/gp3 volumes.

    returns a tuple of
    (
        a list of gp2 volumes,
        None or any gp3 volume that is currently in transition from gp2
    )
    """
    if acctid is None:
        raise Exception(
            f"{logid}: acctid is None at getGPVols for region: {region}"
        )

    # filter to only retrieve gp2 and gp3 volume types
    gpfilter = [{"Name": "volume-type", "Values": ["gp2", "gp3"]}]

    # call the getVolumes function above
    vols = getVolumes(acctid=acctid, region=region, filters=gpfilter, logid=logid)

    volumes = []
    gp3ids = []

    # make a list of gp2 volumes, also make a note of any gp3 volume ids
    for vol in vols:
        if vol["VolumeType"] == "gp2":
            volumes.append(vol)
        else:
            # gp3 volume
            gp3ids.append(vol["VolumeId"])

    # detect if any of the current gp3 volumes
    # are still in a transition state from gp2
    gp3wait = None
    if len(gp3ids) > 0:
        rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")
        ec2 = acct.assumeRoleEC2(rolename, acctid, region, logid)

        # only look for gp3 volumes that are still transitioning from gp2
        filters = [
            {"Name": "modification-state", "Values": ["modifying", "optimizing"]}
        ]
        states = ec2.describe_volumes_modifications(
            VolumeIds=gp3ids, Filters=filters
        )
        mods = states.get("VolumesModifications", None)

        # check if any of the gp3 volumes is still transitioning
        if mods is not None:
            if len(mods) > 0:

                # set a dictionary up with info re: the transitioning volume
                gp3wait = {
                    "region": region,
                    "volid": mods[0]["VolumeId"],
                    "progress": mods[0]["Progress"],
                }

    # setup for reporting into Wavefront
    orgid = os.environ.get("ORGID", "unset")
    orgname = os.environ.get("ORGNAME", "unset")

    # seperately report to Wavefront the number of gp2/3 vols.
    ggMetric(
        f"{orgid}.{orgname}.{acctid}.{acctname}.{region}.volumes.gp2", len(volumes)
    )
    ggMetric(
        f"{orgid}.{orgname}.{acctid}.{acctname}.{region}.volumes.gp3", len(gp3ids)
    )

    # return a tuple of the current gp2 volumes and any gp3 volume that is still transitioning
    return volumes, gp3wait
```

This function performs the API call to transition the volume from gp2 to gp3

```python
def transitionVolume(volumeid, acctid=None, region="eu-west-1", logid=0):
    resp = None
    transitioning = False
    rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")
    ec2 = acct.assumeRoleEC2(rolename, acctid, region, logid)

    # placeholder for a 'dry run' test
    # # resp = ec2.modify_volume(DryRun=True, VolumeId=volumeid, VolumeType="gp3")
    # # print(f"{logid}: dryrun: {resp}")

    # issue the modify volume api call
    resp = ec2.modify_volume(VolumeId=volumeid, VolumeType="gp3")

    # test the result of the modify volume api call
    r = resp.get("VolumeModification", None)
    if r is not None:
        state = r.get("ModificationState", None)
        if state is not None and state != "failed":
            transitioning = True

    # return either False if the call failed or True if it succeeded
    return transitioning
```

Test function to check we can go ahead and transition or not
```python
def checkCanDoTransition(dotransition, picked, volstate):
    """Test that we can transiton this volume."""

    # are we in dry-run mode (dotransition would be false if so)
    if dotransition:

        # have we already picked a volume
        if not picked:

            # is this volume in a suitable state
            if volstate == "available" or volstate == "in-use":
                return True

    # if we get here then, no, we can't transition this volume
    return False
```


This function is called for each thread (remember, one thread per region). The resulting list of gp2 volumes are placed onto a
global queue.

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
