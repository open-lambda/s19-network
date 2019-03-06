import argparse

from edgesim.utils.server import run_server

class RegistryServer(object):
    def __init__(self):
        self.edge_clusters = dict([
            ('ch%d' % i, '10.0.%d.2' % i) for i in xrange(3)
        ])

    def register(self, ip, name, location):
        self.edge_clusters[name] = ip

    def get_edge_clusters(self, location):
        return self.edge_clusters.values()

    def get_http_endpoints(self):
        return {
                "register": self.register,
                "get_edge_clusters": self.get_edge_clusters,
            }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    run_server(args.host, args.port, RegistryServer())

if __name__ == '__main__':
    main()
