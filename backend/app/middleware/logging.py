def log_request(func):
    def wrapper(*args, **kwargs):
        print("Request received")
        return func(*args, **kwargs)
    return wrapper
