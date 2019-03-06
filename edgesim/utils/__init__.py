import json
import requests

def move(loc, edgesim_master_loc):
    try:
        resp = requests.post('http://%s/update_location' % edgesim_master_loc, data=json.dumps({'location': loc}), timeout=2)
    except requests.exceptions.Timeout:
        pass
    
