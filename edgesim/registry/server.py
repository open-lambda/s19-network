import argparse

from edgesim.utils.server import run_server

class RegistryServer(object):
    def __init__(self):
        self.edge_clusters = {}

    def register(self, ip, name, location):
        self.edge_clusters[name] = {
            "ip": ip, "location": location,
        }

    def get_edge_clusters(self, location):
        ip_location_pairs = [ (abs(i['location'] - location), i['ip']) for i in self.edge_clusters.itervalues() ]
        ip_location_pairs.sort()
        return [i[1] for i in ip_location_pairs[:3]]

    def get_http_endpoints(self):
        return {
                "register": self.register,
                "get_edge_clusters": self.get_edge_clusters,
            }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="20.0.0.200")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    run_server(args.host, args.port, RegistryServer())

if __name__ == '__main__':
    main()
