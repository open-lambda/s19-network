import json
import requests

def move(loc, edgesim_master_loc):
    resp = requests.post('http://%s/update_location' % edgesim_master_loc, data=json.dumps({'location': loc}))
    assert resp.json()['status'] == 0

def get_ip(a=0, b=0, c=0, d=0, suffix=None):
    """
    a.b.c.d
    """
    ip = '%s.%s.%s.%s' % (a,b,c,d)
    if suffix is not None:
        return '%s/%s' % (ip, suffix)

    return ip
