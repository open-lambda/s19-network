import argparse

import psutil
import requests

from edgesim.utils.server import run_server

class StatsServer(object):
    def get_stats(self):
        return {
            "cpu_load": psutil.cpu_percent(),
            "memory_used": psutil.virtual_memory()._asdict().get("percent", None)
        }

    def get_http_endpoints(self):
        return {
            "stats": self.get_stats,
        }


def register(args):
    url = "http://%s/register" % args.registry_server
    payload = {"ip": args.host, "name": args.name, "location": args.location}
    resp = requests.post(url, json=payload)
    assert resp.json()["status"] == 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-server", default="20.0.0.200:8888")
    parser.add_argument("--location", required=True, type=int)
    parser.add_argument("--name", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()

    # register
    register(args)

    run_server(args.host, args.port, StatsServer())

if __name__ == '__main__':
    main()
