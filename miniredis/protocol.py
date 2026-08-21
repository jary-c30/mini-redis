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

def handle_request(self, socket_file):
    #grabbing the first byte of the message, the sees which data type it is from the handlers
    first_byte = socket_file.read(1)

    #checks if empty
    if not first_byte:
        raise Disconnect()


    try:
        #converting the byte into plain string
        byte = first_byte.decode('utf-8')
        #goes to whichever handler method that know how to parse this data type
        return self.handlers[byte](socket_file)
    
    #if the first byte is undetictable
    except KeyError:
        raise CommandError('bad request')


def handle_simple_string(self, socket_file):
    #reading raw bytes up to line ending and decoding into plain text
    line_string = socket_file.readline()
    decoded_string = line_string.decode('utf-8')

    #returning the plain string
    return decoded_string.rstrip('\r\n')


def handle_error(self, socket_file):
    #reading raw bytes up to line ending and decoding into plain text
    line_string = socket_file.readline()
    decoded_string = line_string.decode('utf-8').rstrip('\r\n')

    #wrapping string in a error namedtuple so the software can reconginze that it is an error from a normal string value
    return Error(decoded_string)



