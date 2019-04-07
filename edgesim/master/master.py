import atexit

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.term import makeTerm
from mininet.log import setLogLevel, info

from edgesim.utils import get_ip
from edgesim.utils.server import run_server

from .mesh import EdgesimNet, TCLink, connectToRootNS, add_edgesim_rules, enableSSH
from .mobility_switch import MobilitySwitch

import config

class Master(object):
    def __init__(self):
        setLogLevel( 'info' )
        self.tower_to_locations = {'ts0': 0, 'ts1': 5, 'ts2': 10}

        topo = EdgesimNet(num_towers=config.num_towers, num_cloudlets=config.num_cloudlets)
        self.net = Mininet(topo=topo, link=TCLink, switch=MobilitySwitch)
        connectToRootNS(self.net, num_cloudlets=config.num_cloudlets)
        self.net.start()
        add_edgesim_rules(self.net, topo)

        enableSSH(self.net['server'])
        enableSSH(
            self.net['device'],
            extraOpts="-o ListenAddress=%s" % config.device_to_master_ip,
            wait_listen_ip=config.device_to_master_ip,
        )

        for i in xrange(config.num_cloudlets):
            enableSSH(self.net['ch%d' % i])

        # makeTerm(self.net['device'])
        # makeTerm(self.net['server'])

        atexit.register(self.close)

    def close(self):
        for host in ('server', 'device', ):
            self.net[host].cmd('kill %/usr/sbin/sshd')

        for i in xrange(config.num_cloudlets):
            self.net['ch%d' % i].cmd('kill %/usr/sbin/sshd')

        self.net.stop()

    def hello(self):
        return {"blah": "blah"}

    def launch_xterm(self, name):
        makeTerm(self.net[name])

    def launch_cli(self):
        CLI(self.net)

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
        new_ip = get_ip(a=config.tower_network_prefix, c=tower_num, d=2, suffix=24)
        device.setIP(new_ip, intf=dintf)
        default_route = get_ip(a=config.tower_network_prefix, c=tower_num, d=1)
        device.cmd('ip route add to 0.0.0.0/0 via %s' % default_route)

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

        return self.move_device(min(distances)[1])

    def get_http_endpoints(self):
        return {
            "hello": self.hello,
            "add": self.add,
            "move_device": self.move_device,
            "update_location": self.update_location,
            "launch_xterm": self.launch_xterm,
            "launch_cli": self.launch_cli,
        }
