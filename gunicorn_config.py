def pre_request(worker, req):
    # Create a case-insensitive dictionary from the headers list
    headers = {k.lower(): v for k, v in req.headers}
    
    # Check and set Content-Length if not present
    if 'content-length' not in headers:
        req_body = req.get_data(as_text=False)  # Get the raw request body
        content_length = str(len(req_body))
        req.headers.append(('Content-Length', content_length))
    
    # Check and set Host if not present
    if 'host' not in headers:
        req.headers.append(('Host', 'localhost'))
    
    return None  # Gunicorn expects None if processing should continue