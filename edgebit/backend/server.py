import argparse
import hashlib
import logging
import sys
import os

import requests

this_src_dir = os.path.dirname(os.path.abspath(__file__))
edgesim_package = os.path.abspath(os.path.join(this_src_dir, '../../'))
sys.path = [edgesim_package] + sys.path

from edgesim.utils.server import run_server

class EdgebitServer(object):
    def foo(self, data, rounds):
        rounds = int(rounds)
        assert rounds > 0, "rounds has to be > 0"

        i = 0

        while i < rounds:
            i += 1
            result = hashlib.sha256(data)

        return result.hexdigest()

    def get_http_endpoints(self):
        return {
            "foo": self.foo,
        }

def main():
    logging.getLogger(__name__).setLevel(logging.ERROR)
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()

    run_server(args.host, args.port, EdgebitServer())

if __name__ == '__main__':
    main()
