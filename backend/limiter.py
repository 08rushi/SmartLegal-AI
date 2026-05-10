from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter — imported by main.py and every router that needs it.
# Keyed by client IP address.
limiter = Limiter(key_func=get_remote_address)