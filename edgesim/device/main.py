import argparse
import subprocess

import requests

from edgesim.utils import move

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="10.0.0.200:8888")
    parser.add_argument("--edgesim-master", default="13.0.0.3:9999",
        help="location of server to move device",
    )

    args = parser.parse_args()
    return args

def ping_all(ip_addrs):
    procs = []
    for ip in ip_addrs:
        procs.append(subprocess.Popen(["ping", "-c", "3", ip], stdout=subprocess.PIPE))

    for ip, proc in zip(ip_addrs, procs):
        stdout, stderr = proc.communicate()
        print "Ping to %s" % ip
        print stdout


def main(args):
    resp = requests.get("http://%s/get_edge_clusters?location=blah" % args.registry)
    jresp = resp.json()
    assert jresp['status'] == 0, "expected status 0"
    ip_addrs = jresp['result']

    ping_all(ip_addrs)

    move(5, args.edgesim_master)

    ping_all(ip_addrs)

if __name__ == '__main__':
    main(get_args())
