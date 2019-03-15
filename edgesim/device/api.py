from threading import Thread

import requests

class EdgeNet(object):
    def __init__(self, location, registry):
        self.location = location
        self.registry = registry
        self.get_candidate_edge_clusters()
        self.pick_edge_cluster()

    def set_location(self, location):
        self.location = location

    def get_candidate_edge_clusters(self):
        resp = requests.post("http://%s/get_edge_clusters" % (self.registry,), json={"location":self.location})
        rjson = resp.json()
        assert rjson.get("status", -1) == 0

        self.candidate_edge_clusters = rjson["result"]

    def pick_edge_cluster(self):
        def worker(ip_addr, responses):
            resp = requests.get("http://%s:8888/stats" % ip_addr)
            rjson = resp.json()["result"]
            rjson["ip_addr"] = ip_addr
            rjson["latency"] = resp.elapsed.total_seconds() * 1000
            responses.append(rjson)


        threads = []
        responses = []
        for ip_addr in self.candidate_edge_clusters:
            thread = Thread(target=worker, args=(ip_addr, responses, ))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        self.selected_edge_cluster = sorted(responses, key=lambda d: (d['latency'], d['cpu_load'], d['memory_used']))[0]["ip_addr"]


if __name__ == "__main__":
    net = EdgeNet(100, "20.0.0.200:8888")
    print net.selected_edge_cluster
