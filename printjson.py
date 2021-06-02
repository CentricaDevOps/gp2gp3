"""Utility to pretty print json data."""

import json
from pathlib import Path
import sys


def jprint():
    try:
        if len(sys.argv) == 1:
            raise Exception("Please supply file name")
        fn = Path(sys.argv[1])
        if fn.exists():
            with open(fn, "r") as ifn:
                jdata = json.load(ifn)
            print(json.dumps(jdata, indent=4, sort_keys=True), end="\n\n", flush=True)
        else:
            raise Exception(f"{fn} file does not exist")
    except Exception as e:
        exci = sys.exc_info()[2]
        lineno = exci.tb_lineno
        fname = exci.tb_frame.f_code.co_name
        ename = type(e).__name__
        msg = f"{ename} Exception at line {lineno} in function {fname}: {e}"
        print(msg)
        sys.exit(1)


if __name__ == "__main__":
    jprint()
