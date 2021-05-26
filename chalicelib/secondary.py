"""Secondary Lambda function for the gp2gp3 package."""

import os
import queue
import sys
import threading

import botocore
import chalicelib.account as act
import chalicelib.volumes as vl
from chalicelib.wflambda import wfwrapper


def checkCanDoTransition(dotransition, picked, volstate):
    """Test that we can transiton this volume."""
    try:
        # are we in dry-run mode (dotransition would be false if so)
        if dotransition:
            # have we already picked a volume
            if not picked:
                # is this volume in a suitable state
                if volstate == "available" or volstate == "in-use":
                    return True
        return False
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def volsInRegion(region, logid, acctname, acctnum, ttl, Q, dotransition=False):
    """Retrieve list of all gp2/gp3 volumes in the region.

    Test to see if any of the gp3 volumes are still transitioning
    If not, pick a gp2 volume and attempt to transition it
    If that fails move to the next gp2 volume and so on
    """
    try:
        # common details for all volumes
        std = {"region": region, "acctname": acctname, "acctnum": acctnum, "ttl": ttl}
        if acctnum is None:
            raise Exception(f"{logid}: acctnum is None at volsInRegion")
        # this returns a tuple of 2 lists (gp2-volumes, gp3-vol-in-transition)
        vols, gp3wait = vl.getGPVols(
            acctid=acctnum, acctname=acctname, region=region, logid=logid
        )
        picked = False
        # is the last gp3 transition still in progress?
        if gp3wait is not None:
            print(
                f"""{acctnum} {acctname} {region}: Volume: {gp3wait["volid"]} in region: {gp3wait["region"]} is transitioning, {gp3wait["progress"]}% complete, waiting..."""
            )
            return
        # check each gp2 volume
        for vol in vols:
            # test that we can go ahead
            if checkCanDoTransition(dotransition, picked, vol["State"]):
                if vl.transitionVolume(
                    vol["VolumeId"], acctid=acctnum, region=region, logid=logid
                ):
                    print(
                        f"""{logid}: {acctnum} {acctname} {region}: Transitioning {vol["VolumeId"]} from gp2 to gp3"""
                    )
                    picked = True
                else:
                    print(
                        f"""{logid}: {acctnum} {acctname} {region}: Failed to start transitioning volume {vol["VolumeId"]}."""
                    )
                    vol.update(std)
                    Q.put(vol)
            else:
                vol.update(std)
                Q.put(vol)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{acctnum} {acctname}: {ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def testKeys(keys, xdict):
    try:
        for key in keys:
            if key not in xdict:
                raise Exception(f"key {key} not in input")
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


@wfwrapper
def secondaryLF(event, context):
    try:
        reqkeys = ["regions", "acctnum", "tomorrow", "transitionvolumes"]
        testKeys(reqkeys, event)
        regions = event["regions"].split(",")
        acctnum = event["acctnum"]
        rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")
        # regions = testRegions(xregions, acctnum, rolename)
        # xregions = act.assumeRoleGetRegions(rolename, acctnum)
        # regions = xregions.split(",")
        # print(f"allowed regions: {regions}")
        acctname = act.assumeRoleAlias(rolename, acctnum, "eu-west-1")
        tomorrow = event["tomorrow"]
        dotransition = False
        if event["transitionvolumes"] == "true":
            dotransition = True
        Q = queue.Queue()
        threads = []
        gargs = [acctname, acctnum, tomorrow, Q, dotransition]
        for xcn, region in enumerate(regions, start=1):
            targs = [region, xcn]
            targs.extend(gargs)
            thread = threading.Thread(target=volsInRegion, args=targs)
            threads.append(thread)
        # start each thread
        [x.start() for x in threads]
        # wait for each thread to complete
        [x.join() for x in threads]
        cn = Q.qsize()
        if cn > 0:
            print(f"{acctnum} {acctname}: {cn} volumes left to transition")
        else:
            print(f"{acctnum} {acctname}: No volumes to transition at this time.")
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{acctnum} {acctname}: {ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
