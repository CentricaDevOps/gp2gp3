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
"""gp2gp3 migration chalice entry app.py for primary/secondary lambda functions."""

import os
import sys

from chalice import Chalice
from chalice import Rate

import chalicelib.account as act
import chalicelib.primary as PRI
import chalicelib.secondary as SEC

app = Chalice(app_name="gp2gp3")


def getWFKey():
    """
    retrieves the wavefront access key from the param store
    and populates the environment with it
    """
    try:
        ppath = os.environ.get("WFSSMPATH", "/sre/wavefront/directingest")
        pval = act.getParameter(ppath)
        if pval is None:
            raise Exception("Cannot retrieve Wavefront Token")
        # print(f"wftok: {pval}")
        os.environ["WAVEFRONT_API_TOKEN"] = pval
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        raise


@app.schedule(Rate(5, unit=Rate.MINUTES))
def primaryLambda(event):
    """Trigger the primary lambda every 15 minutes."""
    try:
        PRI.doPrimary()
        # getWFKey()
        # print(f"incoming event: {dir(event)}")
        return True
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)


@app.lambda_function()
def secondaryLambda(event, context):
    try:
        # getWFKey()
        # print(f"event: {event}")
        os.environ["WAVEFRONT_API_TOKEN"] = event["wfkey"]
        SEC.secondaryLF(event, context)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
