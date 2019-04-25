import os
import sys
import time

import requests

this_src_dir = os.path.dirname(os.path.abspath(__file__))
edgesim_package = os.path.abspath(os.path.join(this_src_dir, '../../'))
sys.path = [edgesim_package] + sys.path

from edgesim.device.api import EdgeNet

CLOUD_IP = "ms0935.utah.cloudlab.us"
REGISTRY_IP = "ms0935.utah.cloudlab.us"
SIZE = 512
POLICY = "random"
NUM_ITERS = 10

class Edgebit(object):
    def __init__(self):
        self.results = []
        self.net = EdgeNet(100, "%s:8888" % REGISTRY_IP)

    def get_target(self, policy):
        if policy is "cloud":
            return CLOUD_IP

        target = None
        candidates = self.net.get_candidate_edge_clusters()
        key_fn = lambda d: (d['latency'], d['cpu_load'], d['memory_used'])
        if policy is "random":
            target = random.choice(candidates)["ip_addr"]

        elif policy is "best":
            results = self.net.probe_candidates(candidates)
            target = sorted(results, key=key_fn)[0]["ip_addr"]

        elif policy is "worst":
            results = self.net.probe_candidates(candidates)
            target = sorted(results, key=key_fn, reverse=True)[0]["ip_addr"]
        else:
            raise Exception("Invalid policy")

        return target

    def send_data(self, size, policy):
        data = ''.join([random.choice(string.ascii_letters) for i in xrange(size)])

        st = time.time()
        target = self.get_target(policy)
        et = time.time()

        time_to_get_target = (et - st)

        st = et
        url = "http://%s:8090/foo" % target
        resp = requests.post(url, json={"data": data})
        rjson = resp.json()
        assert rjson.get("status", -1) == 0
        et = time.time()

        time_to_compute = (et - st)
        self.results.append([time_to_get_target, time_to_compute])

    def run(self, size, policy):
        i = 0
        while i < NUM_ITERS:
            i += 1
            self.send_data(size, policy)

if __name__ == "__main__":
    eb = Edgebit()
    eb.run(SIZE, POLICY)
    result = { "size": SIZE, "policy": POLICY, "num_iters": NUM_ITERS }
    result['get_target_timing'] = [i[0] for i in eb.results]
    result['compute_timing'] = [i[1] for i in eb.results]

    avg = lambda x: sum(x) / float(len(x))
    result['get_target_timing_avg'] = avg(result['get_target_timing'])
    result['compute_timing_avg'] = avg(result['compute_timing'])

    result['total_timing'] = [sum(i) for i in eb.results]
    result['total_timing_avg'] = avg(result['total_timing'])

    print json.dumps(result)

