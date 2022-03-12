"""
List of all errors on PotatoApp.
"""

class Err(BaseException): pass # Base error for all exception.

class PayloadError(Err): pass # Credentials error.

class ConnectionError(Err): pass # Failed to etablish connection.