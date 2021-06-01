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
"""AWS Account module for gp2gp3 package."""

import os
import sys

import boto3


def addIfNotNone(xdict, xvar, key):
    """Add a key/value to the dictionary if the value is not None."""
    try:
        if xvar is not None:
            xdict[key] = xvar
        return xdict
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getSession(profile=None, region=None):
    """Start a boto3 session."""
    try:
        kwargs = addIfNotNone({}, profile, "profile_name")
        kwargs = addIfNotNone(kwargs, region, "region_name")
        return boto3.Session(**kwargs)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getClient(client, profile=None, region=None):
    try:
        sess = getSession(profile, region)
        return sess.client(client)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getAccountAlias(profile=None):
    try:
        alias = "AliasNotSet"
        if profile is not None:
            iam = getClient("iam", profile=profile)
        else:
            iam = boto3.client("iam")
        pages = iam.get_paginator("list_account_aliases")
        for page in pages.paginate():
            alias = page["AccountAliases"][0]
        return alias
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getRegions():
    try:
        ec2 = getClient("ec2")
        xr = ec2.describe_regions()
        return ",".join([r["RegionName"] for r in xr["Regions"]])
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def ddbScan(table):
    try:
        ddb = getClient("dynamodb")
        resp = ddb.scan(TableName=table)
        data = resp.get("Items")
        while resp.get("LastEvaluatedKey"):
            resp = ddb.scan(TableName=table, ExclusiveStartKey=resp["LastEvaluatedKey"])
            data.extend(resp["Items"])
        return data
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def unpackItem(item):
    try:
        oitem = {}
        for key in item:
            for skey in item[key]:
                oitem[key] = item[key][skey].strip()
        return oitem
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getAccountIdsListDDB():
    try:
        acclist = []
        ddbaccts = ddbScan(os.environ.get("ACCOUNTSTABLE", "AWSAccountAdmin"))
        for acct in ddbaccts:
            uacct = unpackItem(acct)
            if uacct["Active"] == "Y":
                acclist.append({uacct["AccountNumber"]: uacct["AccountName"]})
        return acclist
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getAccountIdsList():
    try:
        accts = None
        ssm = getClient("ssm")
        res = ssm.get_parameter(Name="/services/aws/accounts")
        if "Parameter" in res and "Value" in res["Parameter"]:
            saccts = res["Parameter"]["Value"]
            accts = saccts.split(",")
        return accts
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getAccountIdsOrg():
    try:
        accts = []
        org = getClient("organizations")
        kwargs = {}
        while True:
            resp = org.list_accounts(**kwargs)
            if "Accounts" in resp:
                accts.extend(resp["Accounts"])
            if "NextToken" in resp:
                kwargs["NextToken"] = resp["NextToken"]
            else:
                break
        return accts
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def assumeRoleSession(rolename, acctid, region):
    try:
        rolearn = f"arn:aws:iam::{acctid}:role/{rolename}"
        sts = getClient("sts")
        kwargs = {
            "RoleArn": rolearn,
            "RoleSessionName": "gp2gp3",
            "DurationSeconds": 3600,
        }
        ar = sts.assume_role(**kwargs)
        if "Credentials" not in ar:
            raise Exception(f"Failed to assume {rolearn}")
        kwargs = {
            "aws_access_key_id": ar["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": ar["Credentials"]["SecretAccessKey"],
            "aws_session_token": ar["Credentials"]["SessionToken"],
            "region_name": region,
        }
        return boto3.session.Session(**kwargs)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def assumeRoleAlias(rolename, acctid, region):
    try:
        sess = assumeRoleSession(rolename, acctid, region)
        iam = sess.client("iam")
        pages = iam.get_paginator("list_account_aliases")
        for page in pages.paginate():
            alias = page["AccountAliases"][0]
        return alias
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def assumeRoleEC2(rolename, acctid, region, logid=0):
    try:
        if rolename == "":
            raise Exception(
                f"{logid}: rolename is the empty string at assumeRoleEC2, acctid: {acctid}, region: {region}"
            )
        if acctid is None:
            raise Exception(
                f"{logid}: acctid is None at assumeRoleEC2, rolename: {rolename}, region: {region}"
            )
        # print(
        #     f"{logid}: assumeRoleEC2: rolename: {rolename}, acctid: {acctid}, region: {region}"
        # )
        sess = assumeRoleSession(rolename, acctid, region)
        return sess.client("ec2")
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{logid}: {ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def assumeRoleGetRegions(rolename, acctid):
    try:
        ec2 = assumeRoleEC2(rolename, acctid, "eu-west-1")
        xr = ec2.describe_regions()
        return ",".join([r["RegionName"] for r in xr["Regions"]])
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getParameter(ppath, decrypt=True):
    try:
        pval = None
        ssm = getClient("ssm")
        param = ssm.get_parameter(Name=ppath, WithDecryption=decrypt)
        if "Parameter" in param and "Value" in param["Parameter"]:
            pval = param["Parameter"]["Value"]
        return pval
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def getParams(paramlist, decrypt=True):
    try:
        vals = None
        ssm = getClient("ssm")
        prams = ssm.get_parameters(Names=paramlist, WithDecryption=decrypt)
        if "Parameters" in prams:
            vals = [pram for pram in prams["Parameters"]]
        return vals
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise
