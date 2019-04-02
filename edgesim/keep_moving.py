import argparse
import time

import requests

def move_device(location):
    print "moving to location: %s" % location
    resp = requests.post("http://23.0.0.3:9999/update_location", json={"location": location})
    assert resp.status_code == 200
    jresp = resp.json()
    print jresp
    assert jresp['status'] == 0

    with open("/tmp/location", "w") as fp:
        fp.write(str(location))


def keep_moving(start, end, interval, rate):
    while True:
        for i in xrange(start, end, interval):
            move_device(i)
            time.sleep(rate)

        start, end = end, start
        interval = -1 * interval

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=0, type=int)
    parser.add_argument("--end", default=10, type=int)
    parser.add_argument("--interval", default=2, type=int)
    parser.add_argument("--rate", default=1, type=float)

    args = parser.parse_args()
    keep_moving(args.start, args.end, args.interval, args.rate)
