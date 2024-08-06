# gunicorn_config.py
def pre_request(worker, req):
    if 'content-length' not in req.headers:
        req.headers['content-length'] = '0'
    if 'host' not in req.headers:
        req.headers['host'] = 'localhost'