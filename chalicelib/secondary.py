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
"""Secondary Lambda function for the gp2gp3 package."""

import os
import queue
import sys
import threading

import botocore
import chalicelib.account as act
from chalicelib.snow import changeRequest
import chalicelib.volumes as vl
from chalicelib.wflambda import wfwrapper


# def checkCanDoTransition(dotransition, picked, volstate):
#     """Test that we can transiton this volume."""
#     try:
#         # are we in dry-run mode (dotransition would be false if so)
#         if dotransition:
#             # have we already picked a volume
#             if not picked:
#                 # is this volume in a suitable state
#                 if volstate == "available" or volstate == "in-use":
#                     return True
#         return False
#     except Exception as e:
#         exci = sys.exc_info()[2]
#         lineno = exci.tb_lineno
#         fname = exci.tb_frame.f_code.co_name
#         ename = type(e).__name__
#         msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
#         print(msg)
#         raise


def checkCanDoTransition(event, vol, picked):
    try:
        if event["transitionvolumes"].lower() != "true":
            return False
        if int(vol["Size"]) > int(event["ignoredisks"]):
            return False
        if not picked and (vol["State"] == "available" or vol["State"] == "in-use"):
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


def volsInRegion(region, logid, event):
    """Retrieve list of all gp2/gp3 volumes in the region.

    Test to see if any of the gp3 volumes are still transitioning
    If not, pick a gp2 volume and attempt to transition it
    If that fails move to the next gp2 volume and so on

    event is input event dictionary to lambda function
    """
    try:
        msghead = f"""{event["acctnum"]} {event["acctname"]} {region}:"""
        # common details for all volumes
        std = {
            "region": region,
            "acctname": event["acctname"],
            "acctnum": event["acctnum"],
            "ttl": event["tomorrow"],
        }
        if event["acctnum"] is None:
            raise Exception(f"{logid}: acctnum is None at volsInRegion")
        # this returns a tuple of 2 lists (gp2-volumes, gp3-vol-in-transition)
        vols, gp3wait = vl.getGPVols(
            acctid=event["acctnum"],
            acctname=event["acctname"],
            region=region,
            logid=logid,
        )
        picked = False
        # is the last gp3 transition still in progress?
        if gp3wait is not None:
            msg = f"""{msghead}: Volume: {gp3wait["volid"]} in region: {gp3wait["region"]}"""
            msg += f""" is transitioning, {gp3wait["progress"]}% complete, waiting..."""
            print(msg)
            return
        # check each gp2 volume
        for vol in vols:
            # test that we can go ahead
            if checkCanDoTransition(event, vol, picked):
                if vl.transitionVolume(
                    vol["VolumeId"], event["acctnum"], region=region, logid=logid
                ):
                    print(
                        f"""{msghead} Transitioning {vol["VolumeId"]} from gp2 to gp3"""
                    )
                    picked = True
                    if changeRequest(
                        event,
                        vol["VolumeId"],
                        event["acctname"],
                        event["acctnum"],
                        region,
                    ):
                        print(f"""{msghead} Updated Snow for vol {vol["VolumeId"]}""")
                    else:
                        print(
                            f"""{msghead} Failed to updated Snow for vol {vol["VolumeId"]}"""
                        )
                else:
                    print(
                        f"""{msghead} Failed to start transitioning volume {vol["VolumeId"]}."""
                    )
                    vol.update(std)
                    Q.put(vol)
            else:
                vol.update(std)
                event["Q"].put(vol)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


# def volsInRegion(
#     region, logid, acctname, acctnum, ttl, Q, dotransition=False, snow=None
# ):
#     """Retrieve list of all gp2/gp3 volumes in the region.
#
#     Test to see if any of the gp3 volumes are still transitioning
#     If not, pick a gp2 volume and attempt to transition it
#     If that fails move to the next gp2 volume and so on
#     """
#     try:
#         # common details for all volumes
#         std = {"region": region, "acctname": acctname, "acctnum": acctnum, "ttl": ttl}
#         if acctnum is None:
#             raise Exception(f"{logid}: acctnum is None at volsInRegion")
#         # this returns a tuple of 2 lists (gp2-volumes, gp3-vol-in-transition)
#         vols, gp3wait = vl.getGPVols(
#             acctid=acctnum, acctname=acctname, region=region, logid=logid
#         )
#         picked = False
#         # is the last gp3 transition still in progress?
#         if gp3wait is not None:
#             print(
#                 f"""{acctnum} {acctname} {region}: Volume: {gp3wait["volid"]} in region: {gp3wait["region"]} is transitioning, {gp3wait["progress"]}% complete, waiting..."""
#             )
#             return
#         # check each gp2 volume
#         for vol in vols:
#             # test that we can go ahead
#             if checkCanDoTransition(dotransition, picked, vol["State"]):
#                 if vl.transitionVolume(
#                     vol["VolumeId"], acctid=acctnum, region=region, logid=logid
#                 ):
#                     print(
#                         f"""{logid}: {acctnum} {acctname} {region}: Transitioning {vol["VolumeId"]} from gp2 to gp3"""
#                     )
#                     picked = True
#                     if changeRequest(snow, vol["VolumeId"], acctname, acctnum, region):
#                         print(
#                             f"""{logid}: {acctnum} {acctname} {region}: Updated Snow for vol {vol["VolumeId"]}"""
#                         )
#                     else:
#                         print(
#                             f"""{logid}: {acctnum} {acctname} {region}: Failed to updated Snow for vol {vol["VolumeId"]}"""
#                         )
#                 else:
#                     print(
#                         f"""{logid}: {acctnum} {acctname} {region}: Failed to start transitioning volume {vol["VolumeId"]}."""
#                     )
#                     vol.update(std)
#                     Q.put(vol)
#             else:
#                 vol.update(std)
#                 Q.put(vol)
#     except Exception as e:
#         exci = sys.exc_info()[2]
#         lineno = exci.tb_lineno
#         fname = exci.tb_frame.f_code.co_name
#         ename = type(e).__name__
#         msg = f"{acctnum} {acctname}: {ename} Exception at line {lineno} in function {fname}: {e}"
#         print(msg)
#         raise


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
        reqkeys = [
            "regions",
            "acctnum",
            "tomorrow",
            "transitionvolumes",
            "wfkey",
            "host",
            "username",
            "password",
            "template_id",
            "oldestfirst",
            "ignoredisks",
        ]
        testKeys(reqkeys, event)
        regions = event["regions"].split(",")
        acctnum = event["acctnum"]
        rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")
        acctname = act.assumeRoleAlias(rolename, acctnum, "eu-west-1")
        tomorrow = event["tomorrow"]
        dotransition = True if event["transitionvolumes"] == "true" else False
        Q = queue.Queue()
        threads = []
        gargs = [acctname, acctnum, tomorrow, Q, dotransition, event]
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
