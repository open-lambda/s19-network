import argparse
import subprocess
import time

import requests
from colorama import init
from colorama import Fore, Style

from edgesim.utils import move

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="20.0.0.200:8888")
    parser.add_argument("--edgesim-master", default="23.0.0.3:9999",
        help="location of server to move device",
    )
    parser.add_argument("--interval", default=5, type=int)

    args = parser.parse_args()
    return args

def ping_all(ip_addrs):
    procs = []
    cmd = "fping -e -s -c 3 %s 2>&1 | grep 'avg round trip time' | awk '{print $1 }'"
    for ip in ip_addrs:
        procs.append(subprocess.Popen(cmd % ip, shell=True, stdout=subprocess.PIPE))

    latency_ip_list = []
    for ip, proc in zip(ip_addrs, procs):
        stdout, stderr = proc.communicate()
        latency = float(stdout)
        latency_ip_list.append((latency, ip))

    return latency_ip_list

def main(args):
    init()

    resp = requests.get("http://%s/get_edge_clusters?location=blah" % args.registry)
    jresp = resp.json()
    assert jresp['status'] == 0, "expected status 0"
    ip_addrs = jresp['result']

    header = "      0 -------------- 5 ------------- 10        "
    i = 0
    while True:
        if i % 10 == 0:
            print header

        i += 1

        latency_ip_list = ping_all(ip_addrs)
        time.sleep(args.interval)
        min_latency = min(latency_ip_list)
        message = []
        for latency,ip in latency_ip_list:
            msg = "%s (%s)" % (ip, latency)
            if (latency,ip) == min_latency:
                message.append(Fore.GREEN + msg + Style.RESET_ALL)
            else:
                message.append(msg)

        print ', '.join(message)

if __name__ == '__main__':
    main(get_args())
