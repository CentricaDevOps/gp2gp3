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


@app.schedule(Rate(15, unit=Rate.MINUTES))
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
        getWFKey()
        # print(f"event: {event}")
        SEC.secondaryLF(event, context)
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
