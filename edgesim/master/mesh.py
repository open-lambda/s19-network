from collections import defaultdict

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import Link, TCIntf
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import waitListening

from mobility_switch import MobilitySwitch

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
            ip = '10.0.%d.1/24' % i
            cr = self.addNode('cr%d' % i, cls=LinuxRouter, ip=ip, defaultRoute='via 11.0.%d.1' % ((i * num_towers) + i))
            cloudlet_routers.append(cr)

            cs = self.addSwitch('cs%d' % i, dpid=D('cs%d' % i))
            cloudlet_switches.append(cs)

            self.addLink(cs, cr,
                intfName1='cs%d_cr%d' % (i,i),
                intfName2='cr%d_cs%d' % (i,i),
                params2={'ip': ip},
            )

            ch = self.addHost('ch%d' % i, ip='10.0.%d.2/24' % i,
                defaultRoute='via 10.0.%d.1' % i,
            )

            self.addLink(ch, cs,
                intfName1='ch%d_cs%d' % (i,i),
                intfName2='cs%d_ch%d' % (i,i),
            )


        tower_routers = []
        tower_switches = []
        for i in xrange(num_towers):
            ip = '12.0.%d.1/24' % i
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
            tower_network = '12.0.%d.0/24' % t
            tower_router = 'tr%d' % t
            for c in xrange(num_cloudlets):
                cloudlet_router = 'cr%d' % c
                cloudlet_network = '10.0.%d.0/24' % c
                ip = '11.0.%d.' % (t * num_cloudlets + c) + '%d/24'
                next_hop = '11.0.%d.' % (t * num_cloudlets + c) + '%d'
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

        device = self.addHost('device', ip='12.0.0.2/24', defaultRoute='via 12.0.0.1')
        self.addLink(device, tower_switches[0],
            intfName1='dev_ts', intfName2='ts0_dev',
        )

        server = self.addHost('server', ip='10.0.0.200/24', defaultRoute='via 10.0.0.1')
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
    # root = net.addHost('root', ip='10.0.0.201/24', defaultRoute='via 10.0.0.1', inNamespace=False)
    # net.addLink(root, cloudlet_switches[0], intfName1='root_cs0', intfName2='cs0_root')

    root = Node('root', inNamespace=False)
    switch = net['cs0']
    ip = '10.0.0.201'
    intf = net.addLink( root, switch ).intf1
    root.setIP( ip, intf=intf )

    routes = ['11.0.0.0/16', '12.0.0.0/16']
    for i in range(1, num_cloudlets):
        routes.append('10.0.%d.0/24' % i)

    for route in routes:
        # root.cmd('route add -net ' + route + ' dev ' + str(intf))
        root.cmd('ip route add to %s via 10.0.0.1 dev %s' % (route, intf))

def enableSSH(node):
    node.cmd('/usr/sbin/sshd -D -o UseDNS=no -u0 &')
    waitListening(server=node, port=22, timeout=5)

def run():
    "Test linux router"
    topo = EdgesimNet(num_towers=3, num_cloudlets=3)
    net = Mininet( topo=topo, link=TCLink, switch=MobilitySwitch )  # controller is used by s1-s3
    connectToRootNS(net, 3)

    net.start()

    add_edgesim_rules(net, topo)
    info( '*** Routing Table on Router:\n' )
    CLI( net )

    # move code
    current_switch = net['ts0']
    target_switch = net['ts1']

    device = net['device']
    dintf, sintf = device.connectionsTo(current_switch)[0]
    current_switch.moveIntf(sintf, target_switch, newname='ts1_dev')

    device.setIP('12.0.1.2')
    device.cmd('ip route add to 0.0.0.0/0 via 12.0.1.1')

    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
