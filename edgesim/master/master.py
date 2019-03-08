import atexit

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.term import makeTerm

from edgesim.utils.server import run_server

from .mesh import EdgesimNet, TCLink, connectToRootNS, add_edgesim_rules, enableSSH
from .mobility_switch import MobilitySwitch

class Master(object):
    def __init__(self):
        self.tower_to_locations = {'ts0': 0, 'ts1': 5, 'ts2': 10}

        topo = EdgesimNet(num_towers=3, num_cloudlets=3)
        self.net = Mininet(topo=topo, link=TCLink, switch=MobilitySwitch)
        connectToRootNS(self.net, num_cloudlets=3, root_to_dev_ip='13.0.0.3', dev_to_root_ip='13.0.0.2')
        self.net.start()
        add_edgesim_rules(self.net, topo)
        enableSSH(self.net['server'])
        enableSSH(self.net['device'], extraOpts="-o ListenAddress=13.0.0.2",
            wait_listen_ip='13.0.0.2')

        # makeTerm(self.net['device'])
        # makeTerm(self.net['server'])

        atexit.register(self.close)

    def close(self):
        for host in ('server', 'device', ):
            self.net[host].cmd('kill %/usr/sbin/sshd')

        self.net.stop()

    def hello(self):
        return {"blah": "blah"}

    def move_device(self, tower):
        device = self.net["device"]
        intf = device.nameToIntf["dev_ts"]
        n1, n2 = intf.link.intf1.node.name, intf.link.intf2.node.name
        current_switch_name = n1
        if current_switch_name == 'device':
            current_switch_name = n2

        current_switch = self.net[current_switch_name]
        target_switch = self.net[tower]

        dintf, sintf = device.connectionsTo(current_switch)[0]

        # TODO don't move if current_switch same as target_switch
        current_switch.moveIntf(sintf, target_switch, newname='%s_dev' % (tower, ))

        tower_num = int(tower[2:])
        device.setIP('12.0.%d.2/24' % tower_num, intf=dintf)
        device.cmd('ip route add to 0.0.0.0/0 via 12.0.%d.1' % tower_num)

        return device.cmd("""ifconfig | grep 'dev_ts' -A1 | tail -1 | awk '{ print $2 }'""")

        # out2 = self.net.ping([ self.net[x] for x in ['device', 'ch0', 'ch1', 'ch2']], timeout=3)

        # CLI(self.net)
        # return [out1, out2]

    def add(self, x, y):
        return {"sum": x + y }

    def update_location(self, location):
        # find the right tower switch
        # call move_device on that
        distances = []
        for ts, loc in self.tower_to_locations.iteritems():
            distances.append((abs(location - loc), ts))

        self.move_device(min(distances)[1])

    def get_http_endpoints(self):
        return {
            "hello": self.hello,
            "add": self.add,
            "move_device": self.move_device,
            "update_location": self.update_location,
        }
