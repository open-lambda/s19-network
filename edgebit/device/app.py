import argparse
import json
import os
import random
import string
import sys
import time

import requests

this_src_dir = os.path.dirname(os.path.abspath(__file__))
edgesim_package = os.path.abspath(os.path.join(this_src_dir, '../../'))
sys.path = [edgesim_package] + sys.path

from edgesim.device.api import EdgeNet

CLOUD_IP = "ms0801.utah.cloudlab.us"
REGISTRY_IP = CLOUD_IP

class Edgebit(object):
    def __init__(self, id, size, policy, num_iters, rounds):
        self._id = id
        self.results = []
        self.size = size
        self.policy = policy
        self.num_iters = num_iters
        self.rounds = rounds
        self.net = EdgeNet(100, "%s:9999" % REGISTRY_IP)

    def get_target(self):
        if self.policy == "cloud":
            return CLOUD_IP

        target = None
        candidates = self.net.get_candidate_edge_clusters()
        def key_fn(d):
            latency = (int(d['latency']) // 5) * 5
            num_requests = (d['num_requests'] // 5) * 5
            return (latency, num_requests)

        # key_fn = lambda d: (d['latency'], d['cpu_load'], d['memory_used'])

        if self.policy == "random":
            target = random.choice(candidates)

        elif self.policy == "best":
            results = self.net.probe_candidates(candidates)
            ip_sorted_results = sorted(results, key=lambda x: x['ip_addr'])
            print [(i['num_requests'], i['latency']) for i in ip_sorted_results]
            target = sorted(results, key=key_fn)[0]["ip_addr"]

        elif self.policy == "worst":
            results = self.net.probe_candidates(candidates)
            target = sorted(results, key=key_fn, reverse=True)[0]["ip_addr"]
        else:
            raise Exception("Invalid policy")

        return target

    def send_data(self):
        data = ''.join([random.choice(string.ascii_letters) for i in xrange(self.size)])

        st = time.time()
        target = self.get_target()
        et = time.time()

        time_to_get_target = (et - st)

        st = et
        url = "http://%s:13014/foo" % target
        print '[%s] hitting %s' % (self._id, url)
        resp = requests.post(url, json={"data": data, "rounds": self.rounds})
        rjson = resp.json()
        assert rjson.get("status", -1) == 0, "failed on %r" % rjson
        et = time.time()

        time_to_compute = (et - st)
        self.results.append([time_to_get_target, time_to_compute])

    def run(self):
        i = 0
        while i < self.num_iters:
            i += 1
            self.send_data()

    
def get_args():
    default_msg = "defaults to %(default)s"
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", default=512, help=default_msg)
    parser.add_argument("--policy", choices=("cloud", "random", "best", "worst"), help=default_msg)
    parser.add_argument("--num-iters", type=int, default=10, help=default_msg)
    parser.add_argument("--rounds", type=int, default=100, help=default_msg)
    parser.add_argument("--id", required=True)
    return parser.parse_args()

def main(args):
    sz = args.size
    multipliers = { 'K': 1024, 'M': 1024 **2 }
    multiplier = multipliers.get(sz[-1])
    if multiplier is not None:
        sz = int(sz[:-1]) * multiplier
    else:
        sz = int(sz)

    eb = Edgebit(args.id, sz, args.policy, args.num_iters, args.rounds)
    result = { 
        "id": args.id,
        "size": args.size, 
        "policy": args.policy, 
        "num_iters": args.num_iters, 
        "rounds": args.rounds
    }
    filename = "{id}_{size}_{policy}_{num_iters}_{rounds}.json".format( **result)

    eb.run()

    result['get_target_timing'] = [i[0] for i in eb.results]
    result['compute_timing'] = [i[1] for i in eb.results]

    avg = lambda x: sum(x) / float(len(x))
    result['get_target_timing_avg'] = avg(result['get_target_timing'])
    result['compute_timing_avg'] = avg(result['compute_timing'])

    result['total_timing'] = [sum(i) for i in eb.results]
    result['total_timing_avg'] = avg(result['total_timing'])

    with open(filename, 'wb') as fp:
        json.dump(result, fp, indent=4)

if __name__ == "__main__":
    args = get_args()
    main(args)
