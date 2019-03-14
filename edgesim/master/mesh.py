from collections import defaultdict

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import Link, TCIntf
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import waitListening

from mobility_switch import MobilitySwitch

from edgesim.utils import get_ip
import config

class TCLink( Link ):
    "Link with symmetric TC interfaces configured via opts"
    def __init__( self, node1, node2, port1=None, port2=None,
                  intfName1=None, intfName2=None,
                  addr1=None, addr2=None, **params ):
        params1 = params
        params2 = params
        if 'params1' in params:
            params1 = params['params1']
            params1.update(params)

        if 'params2' in params:
            params2 = params['params2']
            params2.update(params)

        Link.__init__( self, node1, node2, port1=port1, port2=port2,
                       intfName1=intfName1, intfName2=intfName2,
                       cls1=TCIntf,
                       cls2=TCIntf,
                       addr1=addr1, addr2=addr2,
                       params1=params1,
                       params2=params2 )


class EdgesimNet(Topo):
    def _edgesim_get_dpid(self, name):
        if name in self._edgesim_name_to_dpid:
            return self._edgesim_name_to_dpid[name]

        self._edgesim_last_dpid += 1
        dpid = '%010x' % self._edgesim_last_dpid
        self._edgesim_name_to_dpid[name] = dpid
        return dpid

    def build(self, num_cloudlets=1, num_towers=1):
        """
        """
        self._edgesim_name_to_dpid = {}
        self._edgesim_last_dpid = 0

        D = self._edgesim_get_dpid

        # server_host = self.addHost('sh', ip='13.0.0.2/24', defaultRoute='via 13.0.0.1')
        # TODO maybe add switch later
        # server_router = self.addNode('sr', cls=LinuxRouter, ip='13.0.0.1/24')
        # self.addLink(server_router, server_host, intfName1='sr_sh', intfName2='sh_sr',
        #   params1={'ip': '13.0.0.1/24'})

        cloudlet_routers = []
        cloudlet_switches = []
        cloudlet_hosts = []

        for i in xrange(num_cloudlets):
            ip = get_ip(a=config.cloudlet_network_prefix, c=i, d=1, suffix=24)
            default_route_ip = get_ip(a=config.cloudlet_network_prefix, c=((i * num_towers) + i), d=1)

            cr = self.addNode(
                'cr%d' % i,
                cls=LinuxRouter,
                ip=ip,
                defaultRoute='via %s' % default_route_ip,
            )
            cloudlet_routers.append(cr)

            cs = self.addSwitch('cs%d' % i, dpid=D('cs%d' % i))
            cloudlet_switches.append(cs)

            self.addLink(cs, cr,
                intfName1='cs%d_cr%d' % (i,i),
                intfName2='cr%d_cs%d' % (i,i),
                params2={'ip': ip},
            )

            ip = get_ip(a=config.cloudlet_network_prefix, c=i, d=2, suffix=24)
            default_route_ip = get_ip(a=config.cloudlet_network_prefix, c=i, d=1)
            ch = self.addHost('ch%d' % i, ip=ip,
                defaultRoute='via %s' % default_route_ip,
            )

            self.addLink(ch, cs,
                intfName1='ch%d_cs%d' % (i,i),
                intfName2='cs%d_ch%d' % (i,i),
            )


        tower_routers = []
        tower_switches = []
        for i in xrange(num_towers):
            ip = get_ip(a=config.tower_network_prefix, c=i, d=1, suffix=24)
            tr = self.addNode('tr%d' % i, cls=LinuxRouter, ip=ip)
            tower_routers.append(tr)

            ts = self.addSwitch('ts%d' % i, dpid=D('ts%d' % i))
            tower_switches.append(ts)

            self.addLink(ts, tr,
                intfName1='ts%d_tr%d' % (i,i), intfName2='tr%d_ts%d' % (i,i),
                params2={'ip': ip},
            )

        self._edgesim_rules = defaultdict(list)
        for t in xrange(num_towers):
            tower_network = get_ip(a=config.tower_network_prefix, c=t, suffix=24)
            tower_router = 'tr%d' % t
            for c in xrange(num_cloudlets):
                cloudlet_router = 'cr%d' % c
                cloudlet_network = get_ip(a=config.cloudlet_network_prefix, c=c, suffix=24)
                ip = get_ip(a=config.mesh_network_prefix, c=((t*num_cloudlets) + c), d="%d", suffix=24)
                next_hop = get_ip(a=config.mesh_network_prefix, c=((t*num_cloudlets) + c), d="%d")
                self.addLink(tower_routers[t], cloudlet_routers[c],
                    intfName1='tr%d_cr%d' % (t,c), intfName2='cr%d_tr%d' % (c,t),
                    params1={'ip': ip % 1 }, params2={'ip': ip % 2},
                    #bw=10, delay='5ms', max_queue_size=1000,
                    delay='%dms' % ((abs(c-t) + 1) * 5),
                    bw=10,
                )
                self._edgesim_rules[tower_router].append('ip route add to %s via %s' % (cloudlet_network, next_hop % 2))
                self._edgesim_rules[cloudlet_router].append('ip route add to %s via %s' % (tower_network, next_hop % 1))
                # ip route add to 10.0.3.0/24 via 10.0.1.2 dev r1-eth1

        device_ip = get_ip(a=config.tower_network_prefix, d=2, suffix=24)
        device_default_route = get_ip(a=config.tower_network_prefix, d=1)
        device = self.addHost('device', ip=device_ip, defaultRoute='via %s' % device_default_route)
        self.addLink(device, tower_switches[0],
            intfName1='dev_ts', intfName2='ts0_dev',
        )

        registry_default_route = get_ip(a=config.cloudlet_network_prefix, d=1)
        server = self.addHost('server', ip=config.registry_ip, defaultRoute='via %s' % registry_default_route)
        self.addLink(server, cloudlet_switches[0],
            intfName1='server_cs0', intfName2='cs0_server')


class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

def add_edgesim_rules(net, topo):
    for router, rules in topo._edgesim_rules.iteritems():
        info( '*** Routing Table on Router %s:\n' % router )
        for rule in rules:
            print rule
            net[router].cmd(rule)

        info( net[router].cmd( 'route -n' ) )

def connectToRootNS(net, num_cloudlets):
    root = Node('root', inNamespace=False)
    switch = net['cs0']
    ip = config.master_root_ip
    intf = net.addLink( root, switch ).intf1
    root.setIP( ip, intf=intf )

    # TODO better id?
    dpid = '%010x' % 130013
    device_switch = net.addSwitch('ds', dpid=dpid)
    intf = net.addLink( root, device_switch).intf1
    root.setIP( config.master_to_device_ip, intf=intf)

    intf = net.addLink(net['device'], device_switch, intf1Name="dev_root", intf2Name="root_dev").intf1
    net['device'].setIP(config.device_to_master_ip, intf=intf)
    # TODO do we need routing rules for device?

    routes = [get_ip(a=x, suffix=16) for x in (config.mesh_network_prefix, config.tower_network_prefix, )]
    for i in range(1, num_cloudlets):
        routes.append(get_ip(a=config.cloudlet_network_prefix, c=i, suffix=24))

    default_route_ip = get_ip(a=config.cloudlet_network_prefix, d=1)
    for route in routes:
        root.cmd('ip route add to %s via %s dev %s' % (route, default_route_ip, intf))

def enableSSH(node, extraOpts='', wait_listen_ip=None):
    node.cmd('/usr/sbin/sshd -D -o UseDNS=no %s -u0 &' % extraOpts)
    if not wait_listen_ip:
        waitListening(server=node, port=22, timeout=5)
    else:
        waitListening(server=wait_listen_ip, port=22, timeout=5)


def run():
    "Test linux router"
    topo = EdgesimNet(num_towers=3, num_cloudlets=3)
    net = Mininet( topo=topo, link=TCLink, switch=MobilitySwitch )  # controller is used by s1-s3
    connectToRootNS(net, 3)

    net.start()

    add_edgesim_rules(net, topo)
    enableSSH(net['server'])
    enableSSH(net['device'], extraOpts='-o ListenAddress=13.0.0.2')

    CLI( net )

    # move code
    """
    current_switch = net['ts0']
    target_switch = net['ts1']

    device = net['device']
    dintf, sintf = device.connectionsTo(current_switch)[0]
    current_switch.moveIntf(sintf, target_switch, newname='ts1_dev')

    device.setIP('12.0.1.2')
    device.cmd('ip route add to 0.0.0.0/0 via 12.0.1.1')
    """

    net['server'].cmd('kill %/usr/sbin/sshd')
    net['client'].cmd('kill %/usr/sbin/sshd')
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
