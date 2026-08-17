#this files main purpose is to catch errors when code is being run to prevent any crashes the server or if any commands are unrecognizable 

class CommandError(Exception):
    """User sends a message that is undetecatbale"""
    pass

class Disconnect(Exception):
    """User disconnected"""
    pass