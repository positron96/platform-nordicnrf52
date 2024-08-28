# from adafruit-nrfutil

import sys
import os
import site

contrib_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "site-packages")
site.addsitedir(contrib_dir)
sys.path.insert(0, contrib_dir)

from nordicsemi.__main__ import cli

if __name__ == "__main__":
    cli()
