import os
import sys

from aiohttp import web
from setproctitle import setproctitle

from sales.api.app import init_app
from sales.config import DebugConfig
from sales.utils.argparse import get_arg_parser
from sales.utils.logging import set_logging


def run_dev():
    import subprocess

    subprocess.run(["adev", "runserver", "sales/api/debug.py"])


app = None
parser = None
cfg = DebugConfig()

parser = get_arg_parser(cfg)
args = parser.parse_args()

set_logging("debug", args.log_format)

setproctitle(f"[Dev] {os.path.basename(sys.argv[0])}")

app = init_app(args, cfg)

if __name__ == "__main__":
    web.run_app(app)
