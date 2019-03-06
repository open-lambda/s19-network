import json
import requests

def move(loc, edgesim_master_loc):
    resp = requests.post('http://%s/update_location' % edgesim_master_loc, data=json.dumps({'location': loc}))
    assert resp.json()['status'] == 0

