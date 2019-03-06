#!/usr/bin/env python

import argparse

from edgesim.utils.server import run_server
from .master import Master

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0",
        help="host interface to listen on, default: %(default)s")

    parser.add_argument("--port", type=int, default=9999,
        help="port to listen on, default: %(default)s")

    return parser.parse_args()

def main(args):
    # TODO add logging
    master = Master()
    run_server(args.host, args.port, master)

if __name__ == '__main__':
    args = get_args()
    main(args)
