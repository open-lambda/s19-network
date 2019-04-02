import libtmux
import argparse

def create(session):
    device_window = session.new_window(attach=False, window_name="device")
    registry_window = session.new_window(attach=False, window_name="registry")
    cloudlet_windows = []
    for i in xrange(3):
        cloudlet_windows.append(
            session.new_window(attach=False, window_name='ch%d' % i),
        )

def get_windows(session):
    device_window = session.find_where({'window_name': "device"})
    registry_window = session.find_where({'window_name': 'registry'})
    cloudlet_windows = []
    for i in xrange(3):
        cloudlet_windows.append(
                session.find_where({'window_name': 'ch%d' % i}),
        )

    return device_window, registry_window, cloudlet_windows

def get_first_pane_for_windows(device_window, registry_window, cloudlet_windows):
    device_pane = device_window.list_panes()[0]
    registry_pane = registry_window.list_panes()[0]
    cloudlet_panes = []
    for i in xrange(3):
        cloudlet_panes.append(cloudlet_windows[i].list_panes()[0])
    return device_pane, registry_pane, cloudlet_panes

def kill(session):
    device_window, registry_window, cloudlet_windows = get_windows(session)

    device_window.kill_window()
    registry_window.kill_window()
    for i in cloudlet_windows:
        i.kill_window()

def ssh(session):
    device_pane, registry_pane, cloudlet_panes = get_first_pane_for_windows(*get_windows(session))

    device_pane.send_keys('ssh -i ~/id_rsa 23.0.0.2', enter=True)
    registry_pane.send_keys('ssh -i ~/id_rsa 20.0.0.200', enter=True)

    for i in xrange(3):
        cloudlet_panes[i].send_keys('ssh -i ~/id_rsa 20.0.%d.2' % i, enter=True)

def ps1(session):
    device_pane, registry_pane, cloudlet_panes = get_first_pane_for_windows(*get_windows(session))

    device_pane.send_keys("""export PS1='device : \w $ '""", enter=True)
    registry_pane.send_keys("""export PS1='registry : \w $ '""", enter=True)
    for i in xrange(3):
        cloudlet_panes[i].send_keys("""export PS1='ch%d : \w $ '""" % i, enter=True)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-name", required=True)
    parser.add_argument("--action", required=True, choices=[
        'create', 'kill', 'ssh', 'ps1',
    ])
    args = parser.parse_args()
    return args

# cd edgesim && python -m edgesim.registry.server
#
# cd edgesim && python -m edgesim.cloudlet.stats --name ch0 --location 0 --host 20.0.0.2 --port 8888
# cd edgesim && python -m edgesim.cloudlet.stats --name ch1 --location 5 --host 20.0.1.2 --port 8888
# cd edgesim && python -m edgesim.cloudlet.stats --name ch2 --location 10 --host 20.0.2.2 --port 8888
# cd edgesim/edgebit/backend && python server.py --host 20.0.0.2 --port 8090
# cd edgesim/edgebit/backend && python server.py --host 20.0.1.2 --port 8090
# cd edgesim/edgebit/backend && python server.py --host 20.0.2.2 --port 8090

if __name__ == '__main__':
    args = get_args()
    server = libtmux.Server()
    session = server.find_where({"session_name": args.session_name})
    fns = {
        'create': create,
        'kill': kill,
        'ssh': ssh,
        'ps1': ps1,
    }

    fns[args.action](session)
