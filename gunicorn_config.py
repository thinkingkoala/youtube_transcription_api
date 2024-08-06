def pre_request(worker, req):
    # Create a case-insensitive dictionary from the headers list
    headers = {k.lower(): v for k, v in req.headers}
    
    # Check and set Content-Length if not present
    if 'content-length' not in headers:
        body_length = 0
        if hasattr(req, 'body'):
            body_length = len(req.body)
        
        content_length = str(body_length)
        req.headers.append(('Content-Length', content_length))
    
    # Check and set Host if not present
    if 'host' not in headers:
        req.headers.append(('Host', 'localhost'))
    
    return None  # Gunicorn expects None if processing should continue