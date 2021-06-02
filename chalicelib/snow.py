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
"""Service-Now routines for the gp2gp3 project."""

import json
import sys

import requests

from chalicelib.wflambda import ggMetric


def patchRequest(snow, sysid, state):
    try:
        url = f'https://{snow["host"]}/api/sn_chg_rest/change/standard/{sysid}'
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        dat = {"state": state}
        if state == "closed":
            dat["close_code"] = "successful"
            dat["close_notes"] = "update successful"
        sjdat = json.dumps(dat)
        resp = requests.patch(
            url,
            auth=(f'{snow["username"]}', f'{snow["password"]}'),
            headers=headers,
            data=sjdat,
        )
        if resp.status_code == 200:
            return True
        print(f"SNow patch request {state} failed: {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


def changeRequest(snow, volid, acctname, acctid, region):
    try:
        orgid = os.environ.get("ORGID", "unset")
        orgname = os.environ.get("ORGNAME", "unset")
        sjdat = json.dumps(
            {"short_description": f"gp23.{acctid}.{acctname}.{region}.{volid}"}
        )
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        url = f'https://{snow["host"]}/api/sn_chg_rest/change/standard/{snow["template_id"]}'
        resp = requests.post(
            url,
            auth=(f'{snow["username"]}', f'{snow["password"]}'),
            headers=headers,
            data=sjdat,
        )
        if resp.status_code == 200:
            jresp = resp.json()
            try:
                sysid = jresp["result"]["sys_id"]["value"]
                states = ["scheduled", "implement", "review", "closed"]
                donestates = []
                for state in states:
                    if patchRequest(snow, sysid, state):
                        donestates.append(state)
                    else:
                        print(f"SNoW change request {sysid} {state} failed")
                        break
                if len(donestates) == len(states):
                    ggMetric(
                        f"{orgid}.{orgname}.{acctid}.{acctname}.{region}.snow.success",
                        1,
                    )
                    return True
            except KeyError:
                print(f"ValueError: path result.number.value not found in {jresp}")
        ggMetric(f"{orgid}.{orgname}.{acctid}.{acctname}.{region}.snow.fail", 1)
        print(resp.status_code)
        print(resp.text)
        return False
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise
