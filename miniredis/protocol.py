from miniredis.exceptions import CommandError, Disconnect

from collections import namedtuple

#incase something goes wrong we dmade a simple class called error
Error = namedtuple('Error', ('message',))

#maps each wire protocol prefix byte to the method that knows how to pares datatype. this allow the handle_request() function
class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            '+': self.handle_simple_string, #simple string
            '-': self.handle_error,         #error message
            ':': self.handle_integer,       #integer
            '$': self.hanlde_string,        #length-prefixed binary data
            '*': self.handle_array,         #array of other type elements
            '%': self.handle_dict,          #dictionary of key or value pairs
        }