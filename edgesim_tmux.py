import libtmux
import argparse

DEVICE_IP = "23.0.0.2"
REGISTRY_IP = "20.0.0.200"
CLOUDLET_IP_FORMAT = "20.0.%d.2"

def create(session):
    # 2 panes in the device window
    device_window = session.new_window(attach=False, window_name="device")
    device_window.split_window(attach=False, vertical=False)

    # 1 pane / 1 window for registry
    registry_window = session.new_window(attach=False, window_name="registry")

    # 3 panes for cloudlet stats
    cloudlet_stats_window = session.new_window(attach=False, window_name="cloudlet_stats")
    cloudlet_stats_window.split_window(attach=False)
    cloudlet_stats_window.split_window(attach=False)
    cloudlet_stats_window.select_layout("even-vertical")

    # 3 panes for cloudlet edgebit backend
    cloudlet_edgebit_window = session.new_window(attach=False, window_name="cloudlet_edgebit_backend")
    cloudlet_edgebit_window.split_window(attach=False)
    cloudlet_edgebit_window.split_window(attach=False)
    cloudlet_edgebit_window.select_layout("even-vertical")

class Windows(object):
    def __init__(self, session):
        self.session = session
        get_window = lambda x: session.find_where({'window_name': x})

        self.device = get_window("device")
        self.registry = get_window("registry")
        self.stats = get_window("cloudlet_stats")
        self.edgebit_backend = get_window("cloudlet_edgebit_backend")

        self.windows = [self.device, self.registry, self.stats, self.edgebit_backend]

def kill(session):
    wobj = Windows(session)
    for w in wobj.windows:
        w.kill_window()

def unssh(session):
    wobj = Windows(session)
    for w in wobj.windows:
        for pane in w.list_panes():
            pane.send_keys('exit', enter=True)

def ssh(session):
    wobj = Windows(session)

    for pane in wobj.device.list_panes():
        pane.send_keys('ssh -i ~/id_rsa %s' % DEVICE_IP, enter=True)

    for pane in wobj.registry.list_panes():
        pane.send_keys('ssh -i ~/id_rsa %s' % REGISTRY_IP, enter=True)

    for i, pane in enumerate(wobj.stats.list_panes()):
        cloudlet_ip = CLOUDLET_IP_FORMAT % i
        pane.send_keys('ssh -i ~/id_rsa %s' % cloudlet_ip, enter=True)

    for i, pane in enumerate(wobj.edgebit_backend.list_panes()):
        cloudlet_ip = CLOUDLET_IP_FORMAT % i
        pane.send_keys('ssh -i ~/id_rsa %s' % cloudlet_ip, enter=True)

def ps1(session):
    wobj = Windows(session)

    ps1_fmt = """export PS1='{}:\w$ '"""
    for pane in wobj.device.list_panes():
        pane.send_keys(ps1_fmt.format("device"), enter=True)
        pane.clear()

    for pane in wobj.registry.list_panes():
        pane.send_keys(ps1_fmt.format("registry"), enter=True)
        pane.clear()

    for i, pane in enumerate(wobj.stats.list_panes()):
        pane.send_keys(ps1_fmt.format("ch%d" % i), enter=True)
        pane.clear()

    for i, pane in enumerate(wobj.edgebit_backend.list_panes()):
        pane.send_keys(ps1_fmt.format("ch%d" % i), enter=True)
        pane.clear()

def start(session):
    wobj = Windows(session)
    rpane = wobj.registry.list_panes()[0]
    rpane.send_keys("cd ~/edgesim && python -m edgesim.registry.server", enter=True)
    raw_input("Press enter when registry is ready to accept connections > ")

    cmd_fmt = "cd ~/edgesim && python -m edgesim.cloudlet.stats --name {name} --location {loc} --host {host} --port 8888"
    for i, pane in enumerate(wobj.stats.list_panes()):
        host = CLOUDLET_IP_FORMAT % i
        location = i * 5
        name = 'ch%d' % i
        cmd = cmd_fmt.format(name=name, host=host, loc=location)
        pane.send_keys(cmd, enter=True)

    cmd_fmt = "cd ~/edgesim/edgebit/backend && python server.py --host {host} --port 8090"
    for i, pane in enumerate(wobj.edgebit_backend.list_panes()):
        host = CLOUDLET_IP_FORMAT % i
        cmd = cmd_fmt.format(host=host)
        pane.send_keys(cmd, enter=True)


    devpanes = wobj.device.list_panes()
    devpanes[0].send_keys('# cd ~/edgesim/edgebit/device && python app.py', enter=True)
    devpanes[1].send_keys('# cd ~/edgesim/edgesim && python keep_moving.py --rate 2', enter=True)

def stop(session):
    wobj = Windows(session)
    for w in wobj.windows:
        for pane in w.list_panes():
            pane.cmd('send-keys', 'C-c')

def clear(session):
    wobj = Windows(session)
    for w in wobj.windows:
        for pane in w.list_panes():
            pane.clear()

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-name", required=True)
    parser.add_argument("--action", required=True, choices=[
        'create', 'kill', 'ssh', 'ps1', 'unssh', 'start', 'stop', 'clear',
    ])
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()
    server = libtmux.Server()
    session = server.find_where({"session_name": args.session_name})
    fns = {
        'create': create,
        'kill': kill,
        'ssh': ssh,
        'ps1': ps1,
        'unssh': unssh,
        'start': start,
        'stop': stop,
        'clear': clear,
    }

    fns[args.action](session)
