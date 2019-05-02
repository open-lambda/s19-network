import traceback

import flask

def run_server(host, port, obj, threaded=False):
    assert hasattr(obj, "get_http_endpoints"), "expected obj to have get_http_endpoints"

    obj_functions = obj.get_http_endpoints()

    app = flask.Flask(__name__)
    @app.route('/', defaults={'path': ''}, methods=("GET", "POST"))
    @app.route('/<path:path>', methods=("GET", "POST"))
    def catch_all(path):
        fn = obj_functions.get(path)
        if fn is None:
            return flask.jsonify({'status': -1, 'msg': '%r is not a valid function' % path})

        data = {}
        if flask.request.method == "POST":
            try:
                data = flask.request.get_json(force=True) or {}
            except:
                return flask.jsonify({'status': -1, 'msg': 'require valid json'})

        elif flask.request.method == "GET":
            data = flask.request.args or {}
            data = {k:v for k,v in data.iteritems()}
        else:
            return flask.jsonify({'status': -1, 'msg': 'Only POST or GET allowed'})

        try:
            response = fn(**data)
            return flask.jsonify({'status': 0, 'result': response})
        except Exception as e:
            return flask.jsonify({'status': -1, 'msg': repr(e), 'traceback': traceback.format_exc()})

    app.run(host=host, port=port, threaded=threaded)
