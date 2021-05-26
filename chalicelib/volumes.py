"""Volumes file for gp2gp3 package."""

import os
import sys

import botocore

import chalicelib.account as acct
from chalicelib.wflambda import ggMetric


def getVolumes(acctid=None, region="eu-west-1", filters=None, logid=0):
    """Obtain a list of volumes in the specified account/region."""
    try:
        volumes = []
        rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")
        if acctid is None:
            raise Exception(f"{logid}: acctid is none at getVolumes")
        # print(
        #     f"{logid}: in getVolumes: acctid: {acctid}, region: {region}, rolename: {rolename}"
        # )
        ec2 = acct.assumeRoleEC2(rolename, acctid, region, logid)
        kwargs = acct.addIfNotNone({}, filters, "Filters")
        try:
            while True:
                vols = ec2.describe_volumes(**kwargs)
                volumes.extend(vols.get("Volumes"))
                if "NextToken" in vols and vols["NextToken"]:
                    kwargs["NextToken"] = vols["NextToken"]
                else:
                    break
        except botocore.exceptions.ClientError as e:
            print(f"region {region} not enabled (clienterror)")
        except botocore.exceptions.UnauthorizedOperation as e:
            print(f"region {region} not enabled (unauthorised)")
        return volumes
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{logid}: {region}: {ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getGPVols(acctid=None, acctname="", region="eu-west-1", logid=0):
    """Retrieve gp2/gp3 volumes.

    returns a tuple of
    (
        a list of gp2 volumes,
        None or any gp3 volume that is currently in transition from gp2
    )
    """
    try:
        if acctid is None:
            raise Exception(
                f"{logid}: acctid is None at getGPVols for region: {region}"
            )
        gpfilter = [{"Name": "volume-type", "Values": ["gp2", "gp3"]}]
        vols = getVolumes(acctid=acctid, region=region, filters=gpfilter, logid=logid)
        volumes = []
        gp3ids = []
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
            # print(
            #     f"{logid}: testing for gp3: len: {len(gp3ids)}, rolename: {rolename}, acctid: {acctid}, region: {region}"
            # )
            ec2 = acct.assumeRoleEC2(rolename, acctid, region, logid)
            filters = [
                {"Name": "modification-state", "Values": ["modifying", "optimizing"]}
            ]
            states = ec2.describe_volumes_modifications(
                VolumeIds=gp3ids, Filters=filters
            )
            mods = states.get("VolumesModifications", None)
            if mods is not None:
                if len(mods) > 0:
                    gp3wait = {
                        "region": region,
                        "volid": mods[0]["VolumeId"],
                        "progress": mods[0]["Progress"],
                    }
        orgid = os.environ.get("ORGID", "unset")
        orgname = os.environ.get("ORGNAME", "unset")
        ggMetric(
            f"{orgid}.{orgname}.{acctid}.{acctname}.{region}.volumes.gp2", len(volumes)
        )
        ggMetric(
            f"{orgid}.{orgname}.{acctid}.{acctname}.{region}.volumes.gp3", len(gp3ids)
        )
        return volumes, gp3wait
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{logid}: {region}: {ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def transitionVolume(volumeid, acctid=None, region="eu-west-1", logid=0):
    try:
        resp = None
        transitioning = False
        rolename = os.environ.get("ASSUMEROLENAME", "NOTSET")
        # print(
        #     f"{logid}: in transitioning: volid: {volumeid}, acctid: {acctid}, region: {region}, rolename: {rolename}"
        # )
        ec2 = acct.assumeRoleEC2(rolename, acctid, region, logid)
        # print(f"{logid}: doing transition dryrun")
        # resp = ec2.modify_volume(DryRun=True, VolumeId=volumeid, VolumeType="gp3")
        resp = ec2.modify_volume(VolumeId=volumeid, VolumeType="gp3")
        # print(f"{logid}: dryrun: {resp}")
        r = resp.get("VolumeModification", None)
        if r is not None:
            state = r.get("ModificationState", None)
            if state is not None and state != "failed":
                transitioning = True
        return transitioning
    except botocore.exceptions.ClientError as e:
        print(f"{logid}: client error exception: resp: {resp}, e: {e}")
    except botocore.exceptions.UnauthorizedOperation as e:
        print(f"{logid}: unauthorised exception: resp: {resp}, e: {e}")
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{logid}: {region}: {ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise
