def pre_request(worker, req):
    # Normalize header names to lower case for consistency
    headers = {k.lower(): v for k, v in req.headers.items()}
    
    if 'content-length' not in headers:
        req_body = req.get_data(as_text=False)  # Get the raw request body
        req.headers['content-length'] = str(len(req_body))
    if 'host' not in headers:
        req.headers['host'] = 'localhost'