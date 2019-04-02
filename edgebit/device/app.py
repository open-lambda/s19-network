import os
import sys
import time

import requests

this_src_dir = os.path.dirname(os.path.abspath(__file__))
edgesim_package = os.path.abspath(os.path.join(this_src_dir, '../../'))
sys.path = [edgesim_package] + sys.path

from edgesim.device.api import EdgeNet

class Edgebit(object):
    def __init__(self):
        self.steps = 0
        # should be 20.0.0.200 (hopefully)
        self.net = EdgeNet(100, "registry.edgesim.com:8888")
        self.update_current_location()

    def update_current_location(self):
        # read in the location from file
        with open("/tmp/location", "r") as f:
            location = int(f.read().strip())

        self.location = location
        self.net.set_location(self.location)

    def send_steps(self):
        self.steps += 1
        self.update_current_location()

        url = "http://%s:8090/steps" % self.net.pick_edge_cluster()
        resp = requests.post(url, json={'steps': self.steps})
        assert resp.status_code == 200
        print "SENT : STEPS = %s to %s" % (str(self.steps), url)
        time.sleep(2)

    def run(self):
        while True:
            self.send_steps()

if __name__ == "__main__":
    with open("/tmp/location", "w") as fp:
        fp.write("0")

    eb = Edgebit()
    eb.run()

