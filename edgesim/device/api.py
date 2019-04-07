import time

from datetime import datetime
from threading import Thread

import requests

class EdgeNet(object):

    def __init__(self, registry, policy="default"):
        self.cache = {}
        self.registry = registry
        self.update_location()
        self.get_candidate_edge_clusters()
        self.pick_edge_cluster()
        self.policy = policy

        policy_map = {
            "every_n": self.update_n_secs,
            "location_change": self.location_change,
        }
        if self.policy != "default":
            assert self.policy in policy_map, "Policy not found"
            thread = Thread(target=policy_map[self.policy])
            thread.daemon = True
            thread.start()

    def update_location(self):
        with open("/tmp/location", "r") as f:
            self.location = int(f.read().strip())

    def set_location(self, location):
        self.location = location

    def get_location(self):
        return self.location

    def get_candidate_edge_clusters(self):
        # this function will need to be called to get a new candidate list in future
        resp = requests.post("http://%s/get_edge_clusters" % (self.registry,), json={"location":self.location})
        rjson = resp.json()
        assert rjson.get("status", -1) == 0

        self.candidate_edge_clusters = rjson["result"]

    def update_cache(self):
        self.cache[self.location] = (self.selected_edge_cluster, datetime.now())
        if len(self.cache.keys()) > 10:
            oldest = datetime.now()
            location = None
            for loc, last_access_time in self.cache.iteritems():
                if last_access_time < self.oldest:
                    self.oldest = last_access_time
                    location = loc
            if location is not None:
                self.cache.pop(location)

    def pick_edge_cluster(self):
        def worker(ip_addr, responses):
            resp = requests.get("http://%s:8888/stats" % ip_addr)
            rjson = resp.json()["result"]
            rjson["ip_addr"] = ip_addr
            rjson["latency"] = resp.elapsed.total_seconds() * 1000
            responses.append(rjson)

        if self.location in self.cache:
            self.selected_edge_cluster, _ = self.cache[self.location]
            self.update_cache()
            return

        threads = []
        responses = []
        for ip_addr in self.candidate_edge_clusters:
            thread = Thread(target=worker, args=(ip_addr, responses, ))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        self.selected_edge_cluster = sorted(responses, key=lambda d: (d['latency'], d['cpu_load'], d['memory_used']))[0]["ip_addr"]
        self.update_cache()

    def get_edge_cluster(self):
        if self.policy == "default":
            self.update_location()
            self.pick_edge_cluster()

        return self.selected_edge_cluster

    def update_n_secs(self):
        while True:
            self.update_location()
            self.pick_edge_cluster()
            time.sleep(5)

    def location_change(self):
        while True:
            current_location = self.location
            self.update_location()
            if current_location != self.location:
                self.pick_edge_cluster()
            time.sleep(2)

if __name__ == "__main__":
    net = EdgeNet(100, "20.0.0.200:8888")
    print net.selected_edge_cluster
